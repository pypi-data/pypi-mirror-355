from __future__ import annotations

import abc
import inspect
import json
import pathlib
from functools import partial
from typing import TYPE_CHECKING

import torch as th
from attrs import asdict
from stable_baselines3.common.vec_env import DummyVecEnv, VecMonitor, VecNormalize

from eta_ctrl.util import dict_get_any, log_add_filehandler

from . import processors
from .policies import NoPolicy

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence
    from typing import Any

    from gymnasium import Env
    from stable_baselines3.common.base_class import BaseAlgorithm, BasePolicy
    from stable_baselines3.common.vec_env import VecEnv

    from eta_ctrl.config import Config, ConfigRun
    from eta_ctrl.envs import BaseEnv
    from eta_ctrl.util.type_annotations import AlgoSettings, EnvSettings, Path
from logging import getLogger

log = getLogger(__name__)


def vectorize_environment(
    env: type[BaseEnv],
    config_run: ConfigRun,
    env_settings: EnvSettings,
    callback: Callable[[BaseEnv], None],
    verbose: int = 2,
    vectorizer: type[DummyVecEnv] = DummyVecEnv,
    n: int = 1,
    *,
    training: bool = False,
    monitor_wrapper: bool = False,
    norm_wrapper_obs: bool = False,
    norm_wrapper_reward: bool = False,
) -> VecNormalize | VecEnv:
    """Vectorize the environment and automatically apply normalization wrappers if configured. If the environment
    is initialized as an interaction_env it will not have normalization wrappers and use the appropriate configuration
    automatically.

    :param env: Environment class which will be instantiated and vectorized.
    :param config_run: Configuration for a specific optimization run.
    :param env_settings: Configuration settings dictionary for the environment which is being initialized.
    :param callback: Callback to call with an environment instance.
    :param verbose: Logging verbosity to use in the environment.
    :param vectorizer: Vectorizer class to use for vectorizing the environments.
    :param n: Number of vectorized environments to create.
    :param training: Flag to identify whether the environment should be initialized for training or playing. If true,
                     it will be initialized for training.
    :param norm_wrapper_obs: Flag to determine whether observations from the environments should be normalized.
    :param norm_wrapper_reward: Flag to determine whether rewards from the environments should be normalized.
    :return: Vectorized environments, possibly also wrapped in a normalizer.
    """
    # Create the vectorized environment
    log.debug("Trying to vectorize the environment.")
    # Ensure n is one, if the DummyVecEnv is used (it doesn't support more than one)
    if vectorizer.__class__.__name__ == "DummyVecEnv" and n != 1:
        n = 1
        log.warning("Setting number of environments to 1 because DummyVecEnv (default) is used.")

    if "verbose" in env_settings and env_settings["verbose"] is not None:
        verbose = env_settings.pop("verbose")

    # Create the vectorized environment
    def create_env(env_id: int) -> Env:
        env_id += 1
        return env(env_id=env_id, config_run=config_run, verbose=verbose, callback=callback, **env_settings)

    envs: VecEnv | VecNormalize
    envs = vectorizer([partial(create_env, i) for i in range(n)])

    # The VecMonitor knows the ep_reward and so this can be logged to tensorboard
    if monitor_wrapper:
        envs = VecMonitor(envs)

    # Automatically normalize the input features
    if norm_wrapper_obs or norm_wrapper_reward:
        # check if normalization data is available and load it if possible, otherwise
        # create a new normalization wrapper.
        if config_run.path_vec_normalize.is_file():
            log.info(
                f"Normalization data detected. Loading running averages into normalization wrapper: \n"
                f"\t {config_run.path_vec_normalize}"
            )
            envs = VecNormalize.load(str(config_run.path_vec_normalize), envs)
            envs.training = training
            envs.norm_obs = norm_wrapper_obs
            envs.norm_reward = norm_wrapper_reward
        else:
            log.info("No Normalization data detected.")
            envs = VecNormalize(envs, training=training, norm_obs=norm_wrapper_obs, norm_reward=norm_wrapper_reward)

    return envs


def initialize_model(
    algo: type[BaseAlgorithm],
    policy: type[BasePolicy],
    envs: VecEnv | VecNormalize,
    algo_settings: AlgoSettings,
    seed: int | None = None,
    *,
    tensorboard_log: bool = False,
    log_path: Path | None = None,
) -> BaseAlgorithm:
    """Initialize a new model or algorithm.

    :param algo: Algorithm to initialize.
    :param policy: The policy that should be used by the algorithm.
    :param envs: The environment which the algorithm operates on.
    :param algo_settings: Additional settings for the algorithm.
    :param seed: Random seed to be used by the algorithm.
    :param tensorboard_log: Flag to enable logging to tensorboard.
    :param log_path: Path for tensorboard log. Online required if logging is true
    :return: Initialized model.
    """
    log.debug(f"Trying to initialize model: {algo.__name__}")
    _log_path = log_path if log_path is None or isinstance(log_path, pathlib.Path) else pathlib.Path(log_path)

    # tensorboard logging
    algo_kwargs = {}
    if tensorboard_log:
        if _log_path is None:
            msg = "If tensorboard logging is enabled, a path for results must be specified as well."
            raise ValueError(msg)
        log.info(f"Tensorboard logging is enabled. Log file: {_log_path}")
        log.info(
            f"Please run the following command in the console to start tensorboard: \n"
            f'tensorboard --logdir "{_log_path}" --port 6006'
        )
        algo_kwargs = {"tensorboard_log": str(_log_path)}

    # check if the agent takes all the default parameters.
    algo_settings.setdefault("seed", seed)

    algo_params = inspect.signature(algo).parameters
    if "seed" not in algo_params and inspect.Parameter.VAR_KEYWORD not in {p.kind for p in algo_params.values()}:
        del algo_settings["seed"]
        log.warning(
            f"'seed' is not a valid parameter for agent {algo.__name__}. This default parameter will be ignored."
        )

    # create model instance
    return algo(policy, envs, **algo_settings, **algo_kwargs)  # type: ignore[arg-type]


def load_model(
    algo: type[BaseAlgorithm],
    envs: VecEnv | VecNormalize,
    algo_settings: AlgoSettings,
    path_model: Path,
    *,
    tensorboard_log: bool = False,
    log_path: Path | None = None,
) -> BaseAlgorithm:
    """Load an existing model.

    :param algo: Algorithm type of the model to be loaded.
    :param envs: The environment which the algorithm operates on.
    :param algo_settings: Additional settings for the algorithm.
    :param path_model: Path to load the model from.
    :param tensorboard_log: Flag to enable logging to tensorboard.
    :param log_path: Path for tensorboard log. Online required if logging is true
    :return: Initialized model.
    """
    log.debug(f"Trying to load existing model: {path_model}")
    _path_model = path_model if isinstance(path_model, pathlib.Path) else pathlib.Path(path_model)
    _log_path = log_path if log_path is None or isinstance(log_path, pathlib.Path) else pathlib.Path(log_path)

    if not _path_model.exists():
        msg = f"Model couldn't be loaded. Path not found: {_path_model}"
        raise OSError(msg)

    # tensorboard logging
    algo_kwargs = {}
    if tensorboard_log:
        if _log_path is None:
            msg = "If tensorboard logging is enabled, a path for results must be specified as well."
            raise ValueError(msg)
        log.info(f"Tensorboard logging is enabled. Log file: {_log_path}")
        log.info(
            f"Please run the following command in the console to start tensorboard: \n"
            f"tensorboard --logdir '{_log_path}' --port 6006"
        )
        algo_kwargs = {"tensorboard_log": str(_log_path)}

    try:
        model = algo.load(_path_model, envs, **algo_settings, **algo_kwargs)  # type: ignore[arg-type]
        log.debug("Model loaded successfully.")
    except OSError as e:
        msg = f"Model couldn't be loaded: {e.strerror}. Filename: {e.filename}"
        raise OSError(msg) from e

    return model


def log_to_file(config: Config, config_run: ConfigRun) -> None:
    """Log output in terminal to the run_info file.

    :param config: Configuration to figure out the logging settings.
    :param config_run: Configuration for this optimization run.
    """
    file_path = config_run.path_log_output

    if config.settings.log_to_file:
        try:
            log_add_filehandler(filename=file_path)
        except Exception:
            log.exception("Log file could not be created.")


def log_run_info(config: Config, config_run: ConfigRun) -> None:
    """Save run configuration to the run_info file.

    :param config: Configuration for the framework.
    :param config_run: Configuration for this optimization run.
    """
    with config_run.path_run_info.open("w") as f:

        class Encoder(json.JSONEncoder):
            def default(self, o: object) -> object:
                if isinstance(o, pathlib.Path):
                    return str(o)
                if isinstance(o, abc.ABCMeta):
                    return None
                return repr(o)

        try:
            json.dump({**asdict(config_run), **asdict(config)}, f, indent=4, cls=Encoder)
            log.info("Log file successfully created.")
        except TypeError:
            log.warning("Log file could not be created because of non-serializable input in config.")


def deserialize_net_arch(
    net_arch: Sequence[Mapping[str, Any]], in_features: int, device: th.device | str = "auto"
) -> th.nn.Sequential:
    """Deserialize_net_arch can take a list of dictionaries describing a sequential torch network and deserialize
    it by instantiating the corresponding classes.

    An example for a possible net_arch would be:

    .. code-block::

        [{"layer": "Linear", "out_features": 60},
         {"activation_func": "Tanh"},
         {"layer": "Linear", "out_features": 60},
         {"activation_func": "Tanh"}]

    One key of the dictionary should be either 'layer', 'activation_func' or 'process'. If the 'layer' key is present,
    a layer from the :py:mod:`torch.nn` module is instantiated, if the 'activation_func' key is present, the
    value will be instantiated as an activation function from :py:mod:`torch.nn`. If the key 'process' is present,
    the value will be interpreted as a data processor from :py:mod:`eta_ctrl.common.processors`.

    All other keys of each dictionary will be used as keyword parameters to the instantiation of the layer,
    activation function or processor.

    Only the number of input features for the first layer must be specified (using the 'in_features') parameter.
    The function will then automatically determine the number of input features for all other layers in the
    sequential network.

    :param net_arch: List of dictionaries describing the network architecture.
    :param in_features: Number of input features for the first layer.
    :param device: Torch device to use for training the network.
    :return: Sequential torch network.
    """
    network = th.nn.Sequential()
    _features = in_features

    for net in net_arch:
        _net = dict(net)
        if "process" in net:
            process = getattr(processors, _net.pop("process"))

            # The "Split" process must be treated differently, because it needs to be deserialized recursively.
            if {"net_arch" and "sizes"} < inspect.signature(process).parameters.keys():
                sizes = process.get_full_sizes(_features, _net["sizes"])
                _net["net_arch"] = [deserialize_net_arch(e, sizes[i], device) for i, e in enumerate(_net["net_arch"])]

            try:
                if len({"in_channels", "in_features"} & inspect.signature(process).parameters.keys()) > 0:
                    network.append(process(_features, **_net))
                else:
                    network.append(process(**_net))
            except TypeError as e:
                msg = f"Could not instantiate processing module {process.__name__}: {e}"
                raise TypeError(msg) from e

        elif "layer" in net:
            layer = getattr(th.nn, _net.pop("layer"))

            # Set the number of input features if required by the layer class
            try:
                if len({"in_channels", "in_features"} & inspect.signature(layer).parameters.keys()) > 0:
                    network.append(layer(_features, **_net))
                else:
                    network.append(layer(**_net))
            except TypeError as e:
                msg = f"Could not instantiate layer module {layer.__name__}: {e}"
                raise TypeError(msg) from e

        elif "activation_func" in net:
            activation_func = _net.pop("activation_func")
            try:
                network.append(getattr(th.nn, activation_func)(**_net))
            except TypeError as e:
                msg = f"Could not instantiate activation function module {activation_func}: {e}"
                raise TypeError(msg) from e
        else:
            msg = f"Unknown process or layer type: {net}."
            raise ValueError(msg)

        _features = dict_get_any(_net, "out_channels", "out_features", fail=False, default=_features)

    network.to(device)
    return network


def log_net_arch(model: BaseAlgorithm, config_run: ConfigRun) -> None:
    """Store network architecture or policy information in a file. This requires for the model to be initialized,
    otherwise it will raise a ValueError.

    :param model: The algorithm whose network architecture is stored.
    :param config_run: Optimization run configuration (which contains info about the file to store info in).
    :raises: ValueError.
    """
    if not config_run.path_net_arch.exists() and model.policy is not None and model.policy.__class__ is not NoPolicy:
        with pathlib.Path(config_run.path_net_arch).open("w") as f:
            f.write(str(model.policy))

        log.info(f"Net arch / Policy information store successfully in: {config_run.path_net_arch}.")
    elif config_run.path_net_arch.exists():
        log.info(f"Net arch / Policy information already exists in {config_run.path_net_arch}")


def is_vectorized_env(env: BaseEnv | VecEnv | VecNormalize | None) -> bool:
    """Check if an environment is vectorized.

    :param env: The environment to check.
    """
    if env is None:
        return False

    return hasattr(env, "num_envs")


def is_env_closed(env: BaseEnv | VecEnv | VecNormalize | None) -> bool:
    """Check whether an environment has been closed.

    :param env: The environment to check.
    """
    if env is None:
        return True

    if hasattr(env, "closed"):
        return env.closed

    if hasattr(env, "venv"):
        return is_env_closed(env.venv)

    return False


def episode_results_path(series_results_path: Path, run_name: str, episode: int, env_id: int = 1) -> pathlib.Path:
    """Generate a filepath which can be used for storing episode results of a specific environment as a csv file.

    Name is of the format: ThisRun_001_01.csv (run name _ episode number _ environment id .csv)

    :param series_results_path: Path for results of the series of optimization runs.
    :param run_name: Name of the optimization run.
    :param episode: Number of the episode the environment is working on.
    :param env_id: Identification of the environment.
    """
    path = series_results_path if isinstance(series_results_path, pathlib.Path) else pathlib.Path(series_results_path)

    return path / f"{episode_name_string(run_name, episode, env_id)}.csv"


def episode_name_string(run_name: str, episode: int, env_id: int = 1) -> str:
    """Generate a name which can be used to pre or postfix files from a specific episode and run of an environment.

    Name is of the format: ThisRun_001_01 (run name _ episode number _ environment id)

    :param run_name: Name of the optimization run.
    :param episode: Number of the episode the environment is working on.
    :param env_id: Identification of the environment.
    """
    return f"{run_name}_{episode:0>#3}_{env_id:0>#2}"

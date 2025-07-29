from __future__ import annotations

import abc
from collections.abc import Mapping, MutableMapping, Sequence
from datetime import datetime, timedelta
from logging import getLogger
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from pyomo import environ as pyo
from pyomo.core import base as pyo_base

from eta_ctrl.envs import BaseEnv
from eta_ctrl.envs.state import StateConfig, StateVar

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from pyomo.opt import SolverResults

    from eta_ctrl.config import ConfigRun
    from eta_ctrl.util.type_annotations import PyoParams, StepResult, TimeStep


log = getLogger(__name__)


class PyomoEnv(BaseEnv, abc.ABC):
    """Base class for mathematical MPC models. This class can be used in conjunction with the MathSolver agent.
    You need to implement the *_model* method in a subclass and return a *pyomo.AbstractModel* from it.

    :param env_id: Identification for the environment, useful when creating multiple environments.
    :param config_run: Configuration of the optimization run.
    :param verbose: Verbosity to use for logging.
    :param callback: callback which should be called after each episode.
    :param scenario_time_begin: Beginning time of the scenario.
    :param scenario_time_end: Ending time of the scenario.
    :param episode_duration: Duration of the episode in seconds.
    :param sampling_time: Duration of a single time sample / time step in seconds.
    :param model_parameters: Parameters for the mathematical model.
    :param prediction_scope: Duration of the prediction (usually a subsample of the episode duration).
    :param render_mode: Renders the environments to help visualise what the agent see, examples
        modes are "human", "rgb_array", "ansi" for text.
    :param kwargs: Other keyword arguments (for subclasses).
    """

    def __init__(
        self,
        env_id: int,
        config_run: ConfigRun,
        verbose: int = 2,
        callback: Callable | None = None,
        *,
        scenario_time_begin: datetime | str,
        scenario_time_end: datetime | str,
        episode_duration: TimeStep | str,
        sampling_time: TimeStep | str,
        model_parameters: Mapping[str, Any],
        prediction_scope: TimeStep | str | None = None,
        render_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            env_id=env_id,
            config_run=config_run,
            verbose=verbose,
            callback=callback,
            scenario_time_begin=scenario_time_begin,
            scenario_time_end=scenario_time_end,
            episode_duration=episode_duration,
            sampling_time=sampling_time,
            render_mode=render_mode,
            **kwargs,
        )
        # Check configuration for MILP compatibility
        #: Total duration of one prediction/optimization run when used with the MPC agent.
        #: This is automatically set to the value of episode_duration if it is not supplied
        #: separately.
        self.prediction_scope: float
        if prediction_scope is None:
            log.info("prediction_scope parameter is not present. Setting prediction_scope to episode_duration.")
            self.prediction_scope = self.episode_duration
        else:
            self.prediction_scope = float(
                prediction_scope if not isinstance(prediction_scope, timedelta) else prediction_scope.total_seconds()
            )

        if self.prediction_scope % self.sampling_time != 0:
            msg = (
                "The sampling_time must fit evenly into the prediction_scope "
                "(prediction_scope % sampling_time must equal 0)."
            )
            raise ValueError(msg)

        # Make some more settings easily accessible
        #: Number of steps in the prediction (prediction_scope/sampling_time).
        self.n_prediction_steps: int = int(self.prediction_scope // self.sampling_time)
        #: Duration of the scenario for each episode (for total time imported from csv).
        self.scenario_duration: float = self.episode_duration + self.prediction_scope

        #: Configuration for the MILP model parameters.
        self.model_parameters = model_parameters

        # Set additional attributes with model specific information.
        self._concrete_model: pyo.ConcreteModel | None = None  #: Concrete pyomo model as initialized by _model.

        #: Name of the "time" variable/set in the model (i.e. "T"). This is if the pyomo sets must be re-indexed when
        #:   updating the model between time steps. If this is None, it is assumed that no reindexing of the timeseries
        #:   data is required during updates - this is the default.
        self.time_var: str | None = None

        #: Updating indexed model parameters can be achieved either by updating only the first value of the actual
        #:   parameter itself or by having a separate handover parameter that is used for specifying only the first
        #:   value. The separate handover parameter can be denoted with an appended string. For example, if the actual
        #:   parameter is x.ON then the handover parameter could be x.ON_first. To use x.ON_first for updates, set the
        #:   nonindex_update_append_string to "_first". If the attribute is set to None, the first value of the
        #:   actual parameter (x.ON) would be updated instead.
        self.nonindex_update_append_string: str | None = None

        #: Some models may not use the actual time increment (sampling_time). Instead, they would translate into model
        #:   time increments (each sampling time increment equals a single model time step). This means that indices
        #:   of the model components simply count 1,2,3,... instead of 0, sampling_time, 2*sampling_time, ...
        #:   Set this to true, if model time increments (1, 2, 3, ...) are used. Otherwise, sampling_time will be used
        #:   as the time increment. Note: This is only relevant for the first model time increment, later increments
        #:   may differ.
        self._use_model_time_increments: bool = False

    @property
    def model(self) -> tuple[pyo.ConcreteModel, list]:
        """The model property is a tuple of the concrete model and the order of the action space. This is used
        such that the MPC algorithm can re-sort the action output. This sorting cannot be conveyed differently through
        pyomo.

        :return: Tuple of the concrete model and the order of the action space.
        """
        if self._concrete_model is None:
            self._concrete_model = self._model()

        if self._state_config is None:
            _vars = [
                StateVar(com.name, is_agent_action=True)
                for com in self._concrete_model.component_objects(pyo.Var)
                if not isinstance(com, pyo.ScalarVar)
            ]

            self.state_config = StateConfig(*_vars)

        return self._concrete_model, self.state_config.actions

    @model.setter
    def model(self, value: pyo.ConcreteModel) -> None:
        """The model attribute setter should be used for returning the solved model.

        :param value: The pyomo.ConcreteModel object which should be used as the model.
        """
        if not isinstance(value, pyo.ConcreteModel):
            msg = "The model attribute can only be set with a pyomo concrete model."
            raise TypeError(msg)
        self._concrete_model = value

    @abc.abstractmethod
    def _model(self) -> pyo.AbstractModel:
        """Create the abstract pyomo model. This is where the pyomo model description should be placed.

        :return: Abstract pyomo model.
        """
        msg = "The abstract MPC environment does not implement a model."
        raise NotImplementedError(msg)

    def step(self, action: np.ndarray) -> StepResult:
        """Perform one time step and return its results. This is called for every event or for every time step during
        the simulation/optimization run. It should utilize the actions as supplied by the agent to determine the new
        state of the environment. The method must return a five-tuple of observations, rewards, terminated, truncated,
        info.

        This also updates self.state and self.state_log to store current state information.

        .. note::
            This function always returns 0 reward. Therefore, it must be extended if it is to be used with reinforcement
            learning agents. If you need to manipulate actions (discretization, policy shaping, ...)
            do this before calling this function.
            If you need to manipulate observations and rewards, do this after calling this function.

        :param np.ndarray action: Actions to perform in the environment.
        :return: The return value represents the state of the environment after the step was performed.

            * **observations**: A numpy array with new observation values as defined by the observation space.
              Observations is a np.array() (numpy array) with floating point or integer values.
            * **reward**: The value of the reward function. This is just one floating point value.
            * **terminated**: Boolean value specifying whether an episode has been completed. If this is set to true,
              the reset function will automatically be called by the agent or by eta_i.
            * **truncated**: Boolean, whether the truncation condition outside the scope is satisfied.
            * **truncated**: Boolean, whether the truncation condition outside the scope is satisfied.
              Typically, this is a timelimit, but could also be used to indicate an agent physically going out of
              bounds. Can be used to end the episode prematurely before a terminal state is reached. If true, the
              user needs to call the `reset` function.
            * **info**: Provide some additional info about the state of the environment. The contents of this may
              be used for logging purposes in the future but typically do not currently serve a purpose.
        """
        self._actions_valid(action)

        observations = self.update()

        # Update and log current state
        self._create_new_state(self.additional_state)
        self._actions_to_state(action)

        for idx, obs in enumerate(self.state_config.observations):
            self.state[obs] = observations[idx]
        self.state_log.append(self.state)

        reward = pyo.value(next(self.model[0].component_objects(pyo.Objective)))

        # Render the environment at each step
        if self.render_mode is not None:
            self.render()

        return observations, reward, self._done(), False, {}

    def update(self, observations: Sequence[Sequence[float | int]] | None = None) -> np.ndarray:
        """Update the optimization model with observations from another environment.

        :param observations: Observations from another environment.
        :return: Full array of current observations.
        """
        # Update shift counter for rolling MPC approach
        self.n_steps += 1

        # The timeseries data must be updated for the next time step. The index depends on whether time itself is being
        # shifted. If time is being shifted, the respective variable should be set as "time_var".
        step = int(1 if self._use_model_time_increments else self.sampling_time)
        duration = int(
            self.prediction_scope // self.sampling_time + 1
            if self._use_model_time_increments
            else self.prediction_scope
        )

        if self.time_var is not None:
            index = range(self.n_steps * step, duration + (self.n_steps * step), step)
            ts_current = self.pyo_convert_timeseries(
                self.timeseries.iloc[self.n_steps : self.n_prediction_steps + self.n_steps + 1],
                index=tuple(index),
                _add_wrapping_none=False,
            )
            ts_current[self.time_var] = list(index)
            log.debug(
                f"Updated time_var ({self.time_var}) with the set from {index[0]} to "
                f"{index[1]} and steps (sampling time) {self.sampling_time}."
            )
        else:
            index = range(0, duration, step)
            ts_current = self.pyo_convert_timeseries(
                self.timeseries.iloc[self.n_steps : self.n_prediction_steps + self.n_steps + 1],
                index=tuple(index),
                _add_wrapping_none=False,
            )

        # Log current time shift
        if self.n_steps + self.n_prediction_steps + 1 < len(self.timeseries.index):
            log.info(
                f"Current optimization time shift: {self.n_steps} of {self.n_episode_steps} | "
                f"Current scope: {self.timeseries.index[self.n_steps]} "
                f"to {self.timeseries.index[self.n_steps + self.n_prediction_steps + 1]}"
            )
        else:
            log.info(
                f"Current optimization time shift: {self.n_steps} of {self.n_episode_steps}."
                " Last optimization step reached."
            )

        self._create_new_state(self.additional_state)
        updated_params = ts_current
        return_obs = []  # Array for all current observations
        for var_name in self.state_config.observations:
            settings = self.state_config.vars[var_name]
            if not isinstance(settings.interact_id, int):
                msg = "The interact_id value for observations must be an integer."
                raise TypeError(msg)
            value = None

            # Read values from external environment (for example simulation)
            if observations is not None and settings.from_interact is True:
                value = round(
                    (observations[0][settings.interact_id] + settings.interact_scale_add)
                    * settings.interact_scale_mult,
                    5,
                )
                return_obs.append(value)
            else:
                # Read additional values from the mathematical model
                for component in self.model[0].component_objects():
                    if component.name == var_name:
                        # Get value for the component from specified index
                        value = round(pyo.value(component[list(component.keys())[int(settings.index)]]), 5)
                        return_obs.append(value if value is not None else np.nan)
                        break
                else:
                    log.error(f"Specified observation value {var_name} could not be found")
            updated_params[var_name] = value
            self.state[var_name] = value if value is not None else float("nan")

            log.debug(f"Observed value {var_name}: {value}")

        self.state_log.append(self.state)
        self.pyo_update_params(updated_params, self.nonindex_update_append_string)
        return np.array(return_obs)

    def solve_failed(self, model: pyo.ConcreteModel, result: SolverResults) -> None:
        """This method will try to render the result in case the model could not be solved. It should automatically
        be called by the agent.

        :param model: Current model.
        :param result: Result of the last solution attempt.
        """
        self.model = model
        try:
            self.render()
        except Exception:
            log.exception("Rendering partial results failed")
        self.reset()

    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        """Reset the environment to an initial internal state, returning an initial observation and info.

        This method generates a new starting state often with some randomness to ensure that the agent explores the
        state space and learns a generalised policy about the environment. This randomness can be controlled
        with the ``seed`` parameter otherwise if the environment already has a random number generator and
        :meth:`reset` is called with ``seed=None``, the RNG is not reset. When using the environment in conjunction with
        *stable_baselines3*, the vectorized environment will take care of seeding your custom environment automatically.

        For Custom environments, the first line of :meth:`reset` should be ``super().reset(seed=seed)`` which implements
        the seeding correctly.

        .. note ::
            Don't forget to store and reset the episode_timer.

        :param seed: The seed that is used to initialize the environment's PRNG (`np_random`).
                If the environment does not already have a PRNG and ``seed=None`` (the default option) is passed,
                a seed will be chosen from some source of entropy (e.g. timestamp or /dev/urandom).
                However, if the environment already has a PRNG and ``seed=None`` is passed, the PRNG will *not* be
                reset. If you pass an integer, the PRNG will be reset even if it already exists. (default: None)
        :param options: Additional information to specify how the environment is reset (optional,
                depending on the specific environment) (default: None)

        :return: Tuple of observation and info. The observation of the initial state will be an element of
                :attr:`observation_space` (typically a numpy array) and is analogous to the observation returned by
                :meth:`step`. Info is a dictionary containing auxiliary information complementing ``observation``. It
                should be analogous to the ``info`` returned by :meth:`step`.
        """
        if self.n_steps > 0:
            self.model = self._model()

        super().reset(seed=seed, options=options)

        # Initialize state with the initial observation
        self.state = {} if self.additional_state is None else self.additional_state
        observations = []
        for var_name in self.state_config.observations:
            # Try getting the first value from initialized variables. Use the configured low_value from state_config
            # for all others.
            obs_val = self.pyo_get_component_value(self.model[0].component(var_name), allow_stale=True)
            obs_val = obs_val if obs_val is not None else 0
            observations.append(obs_val)
            self.state[var_name] = obs_val

        # Initialize state with zero actions
        for act in self.state_config.actions:
            self.state[act] = 0
        self.state_log.append(self.state)

        # Render the environment when calling the reset function
        if self.render_mode is not None:
            self.render()

        return np.array(observations), {}

    def close(self) -> None:
        """Close the environment. This should always be called when an entire run is finished. It should be used to
        close any resources (i.e. simulation models) used by the environment.

        Default behavior for the MPC environment is to do nothing.
        """

    def pyo_component_params(
        self,
        component_name: None | str,
        ts: pd.DataFrame | pd.Series | dict[str, dict] | Sequence | None = None,
        index: pd.Index | Sequence | pyo.Set | None = None,
    ) -> PyoParams:
        """Retrieve parameters for the named component and convert the parameters into the pyomo dict-format.
        If required, timeseries can be added to the parameters and timeseries may be reindexed. The
        pyo_convert_timeseries function is used for timeseries handling. See also *pyo_convert_timeseries*

        :param component_name: Name of the component.
        :param ts: Timeseries for the component.
        :param index: New index for timeseries data. If this is supplied, all timeseries will be copied and
                      reindexed.
        :return: Pyomo parameter dictionary.
        """
        if component_name is None:
            params = self.model_parameters
        elif component_name in self.model_parameters:
            params = self.model_parameters[component_name]
        else:
            params = {}
            log.warning(f"No parameters specified for requested component {component_name}")

        out: PyoParams
        out = {
            param: {None: float(value) if isinstance(value, str) and value in {"inf", "-inf"} else value}
            for param, value in params.items()
        }

        # If component name was specified only look for relevant time series
        if ts is not None:
            out.update(self.pyo_convert_timeseries(ts, index, component_name, _add_wrapping_none=False))

        return {None: out}

    @staticmethod
    def pyo_convert_timeseries(
        ts: pd.DataFrame | pd.Series | dict[str | None, dict[str, Any] | Any] | Sequence,
        index: pd.Index | Sequence | pyo.Set | None = None,
        component_name: str | None = None,
        *,
        _add_wrapping_none: bool = True,
    ) -> PyoParams:
        """Convert a time series data into a pyomo format. Data will be reindexed if a new index is provided.

        :param ts: Timeseries to convert.
        :param index: New index for timeseries data. If this is supplied, all timeseries will be copied and
                      reindexed.
        :param component_name: Name of a specific component that the timeseries is used for. This limits which
                               timeseries are returned.
        :param _add_wrapping_none: Add a "None" indexed dictionary as the top level.
        :return: Pyomo parameter dictionary.
        """
        output: PyoParams = {}
        if index is not None and not isinstance(index, list):
            index = list(index)

        _ts: pd.DataFrame | pd.Series | dict[str, Any] | Sequence
        # If part of the timeseries was converted before, make sure that everything is on the same level again.
        if isinstance(ts, dict) and None in ts and isinstance(ts[None], Mapping):
            _ts = {}
            _ts.update(ts[None])

        else:
            _ts = ts

        def convert_index(cts: pd.Series | Sequence | Mapping, _index: Sequence[int] | None) -> dict[int, Any]:
            """Take the timeseries and change the index to correspond to _index.

            :param cts: Original timeseries object (with or without index does not matter).
            :param _index: New index.
            :return: New timeseries dictionary with the converted index.
            """
            values = None
            if isinstance(cts, pd.Series):
                values = cts.to_numpy()
            elif isinstance(cts, Sequence):
                values = cts
            elif isinstance(cts, Mapping):
                values = cts.values()

            if _index is not None and values is not None:
                cts = dict(zip(_index, values, strict=False))
            elif _index is not None and values is None:
                msg = "Unsupported timeseries type for index conversion."
                raise ValueError(msg)

            return cts

        if isinstance(_ts, pd.DataFrame | Mapping):
            for key, t in _ts.items():
                # Determine whether the timeseries should be returned, based on the timeseries name and the requested
                #  component name.
                if component_name is not None and "." in key and component_name not in key.split("."):
                    continue
                split_key = key.split(".")[-1]

                # Simple values do not need their index converted...
                if not hasattr(t, "__len__") and np.isreal(t):
                    output[split_key] = {None: t}
                else:
                    output[split_key] = convert_index(t, index)

        elif isinstance(_ts, pd.Series):
            # Determine whether the timeseries should be returned, based on the timeseries name and the requested
            #  component name.
            if (
                component_name is not None
                and isinstance(_ts.name, str)
                and "." in _ts.name
                and component_name in _ts.name.split(".")
            ):
                output[_ts.name.split(".")[-1]] = convert_index(_ts, index)
            elif component_name is None or "." not in _ts.name:
                output[_ts.name] = convert_index(_ts, index)

        else:
            output[None] = convert_index(_ts, index)

        return {None: output} if _add_wrapping_none else output

    def pyo_update_params(
        self,
        updated_params: MutableMapping[str | None, Any],
        nonindex_param_append_string: str | None = None,
    ) -> None:
        """Update model parameters and indexed parameters of a pyomo instance with values given in a dictionary.
        It assumes that the dictionary supplied in updated_params has the correct pyomo format.

        :param updated_params: Dictionary with the updated values.
        :param nonindex_param_append_string: String to be appended to values which are not indexed. This can
            be used if indexed parameters need to be set with values that do not have an index.
        :return: Updated model instance.
        """
        # append string to non indexed values that are used to set indexed parameters.
        if nonindex_param_append_string is not None:
            original_indices = set(updated_params.keys()).copy()
            for param in original_indices:
                component = self.model[0].component(param)
                if (
                    component is not None
                    and (component.is_indexed() or isinstance(component, pyo.Set | pyo.RangeSet))
                    and not isinstance(updated_params[param], Mapping)
                ):
                    updated_params[str(param) + nonindex_param_append_string] = updated_params[param]
                    del updated_params[param]

        for parameter in self.model[0].component_objects():
            parameter_name = str(parameter)
            if parameter_name not in updated_params:
                # last entry is the parameter name for abstract models which are instanced
                parameter_name = parameter_name.split(".")[-1]

            if parameter_name in updated_params:
                if isinstance(parameter, pyo_base.param.ScalarParam | pyo_base.var.ScalarVar):
                    # update all simple parameters (single values)
                    parameter.value = updated_params[parameter_name]
                elif isinstance(parameter, pyo_base.indexed_component.IndexedComponent):
                    # update all indexed parameters (time series)
                    if not isinstance(updated_params[parameter_name], Mapping):
                        parameter[next(parameter)] = updated_params[parameter_name]
                    else:
                        for param_val in list(parameter):
                            parameter[param_val] = updated_params[parameter_name][param_val]

        log.info("Pyomo model parameters updated.")

    def pyo_get_solution(self, names: set[str] | None = None) -> dict[str, float | int | dict[int, float | int]]:
        """Convert the pyomo solution into a more usable format for plotting.

        :param names: Names of the model parameters that are returned.
        :return: Dictionary of {parameter name: value} pairs. Value may be a dictionary of {time: value} pairs which
                 contains one value for each optimization time step.
        """
        solution = {}

        for com in self.model[0].component_objects():
            if com.ctype not in {pyo.Var, pyo.Param, pyo.Objective}:
                continue
            if names is not None and com.name not in names:
                continue  # Only include names that where asked for

            # For simple variables we need just the values, for everything else we want time indexed dictionaries
            if isinstance(com, pyo.ScalarVar | pyo_base.objective.SimpleObjective | pyo_base.param.ScalarParam):
                solution[com.name] = pyo.value(com)
            else:
                solution[com.name] = {}
                if self._use_model_time_increments:
                    for ind, val in com.items():
                        solution[com.name][
                            self.timeseries.index[self.n_steps].to_pydatetime()
                            + timedelta(seconds=ind * self.sampling_time)
                        ] = pyo.value(val)
                else:
                    for ind, val in com.items():
                        solution[com.name][
                            self.timeseries.index[self.n_steps].to_pydatetime() + timedelta(seconds=ind)
                        ] = pyo.value(val)

        return solution

    def pyo_get_component_value(
        self, component: pyo.Component, *, at: int = 1, allow_stale: bool = False
    ) -> float | int | None:
        if allow_stale and (
            (getattr(component, "stale", None)) or (getattr(component, "value", None) is component.NoValue)
        ):
            return self.state_config.vars[component.name].low_value

        if isinstance(component, pyo.Var | pyo.RangeSet):
            val = round(pyo.value(component.at(at)), 5)
        elif component.is_indexed() and (
            not hasattr(component, "stale") or (hasattr(component, "stale") and not component.stale)
        ):
            val = round(pyo.value(component[component.index_set().at(at)]), 5)
        else:
            val = round(pyo.value(component), 5)

        return val

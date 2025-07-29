from __future__ import annotations

from typing import TYPE_CHECKING

from stable_baselines3.common.callbacks import BaseCallback, CallbackList

if TYPE_CHECKING:
    from stable_baselines3.common.type_aliases import MaybeCallback

    from eta_ctrl.envs import BaseEnv

from logging import getLogger

log = getLogger(__name__)


class CallbackEnvironment:
    """This callback should be called at the end of each episode.
    When multiprocessing is used, no global variables are available (as an own python instance is created).

    :param plot_interval: How many episodes to pass between each render call.
    """

    def __init__(self, plot_interval: int) -> None:
        self.plot_interval = plot_interval

    def __call__(self, env: BaseEnv) -> None:
        """
        This callback should be called at the end of each episode.
        When multiprocessing is used, no global variables are available (as an own python instance is created).

        :param env: Instance of the environment where the callback was triggered.
        """
        log.info(
            "Environment callback triggered "
            f"(env_id = {env.env_id}, n_episodes = {env.n_episodes}, run_name = {env.run_name}."
        )

        # render first episode
        if env.n_episodes == 1:
            env.render()
        # render progress over episodes (for each environment individually)
        elif env.n_episodes % self.plot_interval == 0:
            env.render()
            if hasattr(env, "render_episodes"):
                env.render_episodes()


def merge_callbacks(*args: MaybeCallback) -> CallbackList:
    """Take a number of arguments and merge them into a CallbackList object if they instantiate BaseCallback.

    :param args: List of callbacks.
    :return: CallbackList object which merges all callbacks.
    """
    cb_list = []
    for cb in args:
        if isinstance(cb, BaseCallback):
            cb_list.append(cb)
        elif isinstance(cb, list):
            merge_callbacks(*cb)
        elif cb is None:
            continue
        else:
            msg = f"Invalid callback type: {type(cb)}."
            raise ValueError(msg)

    return CallbackList(cb_list)

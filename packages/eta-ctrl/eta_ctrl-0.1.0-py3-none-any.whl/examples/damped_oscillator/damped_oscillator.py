from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from eta_ctrl.common import episode_results_path
from eta_ctrl.envs import SimEnv, StateConfig, StateVar

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime
    from typing import Any

    from eta_ctrl.config import ConfigRun
    from eta_ctrl.util.type_annotations import ObservationType, StepResult, TimeStep


class DampedOscillatorEnv(SimEnv):
    """
    Damped oscillator environment class from SimEnv.
    Model settings come from fmu file.

    :param env_id: Identification for the environment, useful when creating multiple environments
    :param config_run: Configuration of the optimization run
    :param verbose: Verbosity to use for logging (default: 2)
    :param callback: callback which should be called after each episode
    :param scenario_time_begin: Beginning time of the scenario
    :param scenario_time_end: Ending time of the scenario
    :param episode_duration: Duration of the episode in seconds
    :param sampling_time: Duration of a single time sample / time step in seconds
    :param scale_actions: Normalize the actions when using RL algorithms
    """

    # Set info
    version = "v0.1"
    description = "Damped oscillator"
    fmu_name = "damped_oscillator"

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
        scale_actions: bool = False,
        render_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            env_id,
            config_run,
            verbose,
            callback,
            scenario_time_begin=scenario_time_begin,
            scenario_time_end=scenario_time_end,
            episode_duration=episode_duration,
            sampling_time=sampling_time,
            render_mode=render_mode,
            **kwargs,
        )
        self.scale_actions = scale_actions
        action_values = 1 if self.scale_actions else 15

        # Set action space and observation space
        self.state_config = StateConfig(
            StateVar(
                name="u",
                ext_id="u",
                is_agent_action=True,
                low_value=-action_values,
                high_value=action_values,
                is_ext_input=True,
            ),
            StateVar(name="s", ext_id="s", is_agent_observation=True, low_value=-15, high_value=15, is_ext_output=True),
            StateVar(name="v", ext_id="v", is_agent_observation=True, low_value=-20, high_value=20, is_ext_output=True),
            StateVar(
                name="a", ext_id="a", is_agent_observation=True, low_value=-20.0, high_value=20.0, is_ext_output=True
            ),
            StateVar(name="f", ext_id="f", low_value=0, high_value=100, is_ext_input=True),
        )
        self.action_space, self.observation_space = self.state_config.continuous_spaces()

        # Initialize the simulator
        self._init_simulator()

        #: Total reward over an episode
        self.episode_reward: float = 0.0

    def step(self, action: np.ndarray) -> StepResult:
        """Perform one time step and return its results. Set random force and perform the simulation.

        :param action: Actions to perform in the environment.
        :return: The return value represents the state of the environment after the step was performed.
        """
        assert self.state_config is not None, "Set state_config before calling step function."

        force_var = self.state_config.vars["f"]
        assert force_var.low_value is not None, "Set low value for the applied force"
        assert force_var.high_value is not None, "Set high value for the applied force"
        self.additional_state = {"f": self.np_random.uniform(force_var.low_value, force_var.high_value)}

        # scale the actions
        if self.scale_actions:
            action *= 15

        observations, _, terminated, truncated, info = super().step(action)
        self.episode_reward -= abs(self.state["s"])
        return observations, self.episode_reward, terminated, truncated, info

    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[ObservationType, dict[str, Any]]:
        """Reset the model and return initial observations.

        :param seed: The seed that is used to initialize the environment's PRNG (`np_random`) (default: None).
        :param options: Additional information to specify how the environment is reset (optional,
                depending on the specific environment) (default: None)
        :return: Tuple of observation and info. Analogous to the ``info`` returned by :meth:`step`.
        """
        assert self.state_config is not None, "Set state_config before calling reset function."

        force_var = self.state_config.vars["f"]
        assert force_var.low_value is not None, "Set low value for the applied force"
        assert force_var.high_value is not None, "Set high value for the applied force"
        self.additional_state = {"f": self.np_random.uniform(force_var.low_value, force_var.high_value)}

        observations, infos = super().reset(seed=seed, options=options)
        self.episode_reward = 0

        return observations, infos

    def render(self, mode: str = "human") -> None:
        self.export_state_log(
            path=episode_results_path(self.config_run.path_series_results, self.run_name, 1, self.env_id)
        )

        mpl.rcParams["font.family"] = "Times New Roman"
        mpl.rcParams["font.size"] = "9"
        linestyles = [":", "--", "-"]

        def greys(x: int) -> tuple[float, ...]:
            return (*tuple([(x / 4) for _ in range(3)]), 1)

        fig, ax = plt.subplots(1, 1, figsize=(7, 3.5))
        fig.set_layout_engine("tight")

        data = pd.DataFrame(data=self.state_log, index=list(range(len(self.state_log))), dtype=np.float32)
        x = data.index
        columns = {"distance of mass": "s", "input signal": "u"}

        lines: list[mpl.lines.Line2D] = []
        labels: list[str] = []
        for name, col in columns.items():
            hdl = ax.plot(x, data[col], color=greys(len(lines)), linestyle=linestyles[len(lines)])[0]
            lines.append(hdl)
            labels.append(name)

        ax.legend(lines, labels, loc="upper right")
        ax.yaxis.grid(color="gray", linestyle="dashed")

        ax.set_xlabel("time")
        ax.set_ylabel("distance")

        plt.show()

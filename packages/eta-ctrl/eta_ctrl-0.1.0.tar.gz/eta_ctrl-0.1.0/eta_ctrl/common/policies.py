from __future__ import annotations

from typing import TYPE_CHECKING

from stable_baselines3.common import policies

if TYPE_CHECKING:
    from typing import Any

    import torch as th


class NoPolicy(policies.BasePolicy):
    """No Policy allows for the creation of agents which do not use neural networks. It does not implement any of
    the typical policy functions but is a simple interface that can be used and ignored. There is no need
    to worry about the implementation details of policies.
    """

    def forward(self, *args: Any, **kwargs: Any) -> None:
        """No Policy allows for the creation of agents which do not use neural networks. It does not implement any of
        the typical policy functions but is a simple interface that can be used and ignored. There is no need
        to worry about the implementation details of policies.
        """
        msg = "'NoPolicy' should be used only, when predictions are calculated otherwise."
        raise NotImplementedError(msg)

    # type ignored because mypy doesn't seem to think the following is equivalent to the super class...
    def _predict(self, observation: th.Tensor, deterministic: bool = False) -> th.Tensor:  # type: ignore[override]
        """Get the action according to the policy for a given observation.

        Not implemented in NoPolicy.

        :param observation: Observations of the agent.
        :param deterministic: Whether to use stochastic or deterministic actions.
        :return: Taken action according to the policy.
        """
        msg = "'NoPolicy' should be used only, when predictions are calculated otherwise."
        raise NotImplementedError(msg)

    # type ignored because mypy doesn't seem to think the following is equivalent to the super class...
    def state_dict(  # type: ignore[override]
        self, *, destination: dict[str, Any] | None = None, prefix: str = "", keep_vars: bool = False
    ) -> dict[str, Any]:
        """Return a dictionary containing a whole state of the module. The dictionary is empty in NoPolicy.

        :param destination: If provided, the state will be updated into the dictionary and the same object returned.
        :param prefix: Prefix added to parameter and buffer names when composing keys in state_dict.
        :param keep_vars: Determine, which variables will be detached from torch.autograd.
        :return: Dictionary with the module/policy state.
        """
        return {}

    # type ignored because mypy doesn't seem to think the following is equivalent to the super class...
    def load_state_dict(self, state_dict: dict[str, Any] | None = None, strict: bool = True) -> None:  # type: ignore[override]
        """Load the state dictionary. Since the dictionary is always empty, this method doesn't do anything in
        NoPolicy.

        state_dict (dict): a dict containing parameters and
                persistent buffers.
        strict (bool, optional): whether to strictly enforce that the keys
                in :attr:`state_dict` match the keys returned by this module's
                :meth:`~torch.nn.Module.state_dict` function. Default: ``True``
        """

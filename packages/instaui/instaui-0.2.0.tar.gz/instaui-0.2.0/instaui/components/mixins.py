from typing import Dict, Protocol
from typing_extensions import Self
from instaui.vars.types import TMaybeRef


class PropsProtocol(Protocol):
    def props(self, props: Dict) -> Self: ...


class CanDisabledMixin:
    def disabled(self: PropsProtocol, disabled: TMaybeRef[bool] = True):
        return self.props({"disabled": disabled})

from typing import Sequence, Callable

from requests import PreparedRequest
from requests.auth import AuthBase

from . import Request

request_type = PreparedRequest | Request

class RequestHook(AuthBase):
    def __init__(self, auth: AuthBase | None = None,
                 hooks: Sequence[Callable[[request_type], request_type]] | None = None):
        self.auth = auth
        if hooks is None:
            hooks = []
        self.hooks = hooks

    def __call__(self, r: request_type) -> request_type:
        if self.auth:
            r = self.auth(r)
        for hook in self.hooks:
            r = hook(r)
        return r

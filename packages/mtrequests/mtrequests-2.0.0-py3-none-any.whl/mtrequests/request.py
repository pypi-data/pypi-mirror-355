from __future__ import annotations
from typing import TYPE_CHECKING
from contextlib import nullcontext

import requests

import mtrequests
if TYPE_CHECKING:
    from . import PendingResponse, PendingPool, RequestHook, PendingRequest


class SessionArgs:
    def __init__(
            self,
            send_kwargs=None,
            proxies=None,
            stream=None,
            verify=None,
            cert=None,
    ):
        self.send_kwargs = send_kwargs
        self.proxies = proxies
        self.stream = stream
        self.verify = verify
        self.cert = cert


class Request:
    def __init__(
            self,
            method=None,
            url=None,
            headers=None,
            files=None,
            data=None,
            params=None,
            auth=None,
            cookies=None,
            hooks=None,
            json=None,
            send_kwargs=None,
            proxies=None,
            stream=None,
            verify=None,
            cert=None,
            save_headers_position=None,
    ):
        data = [] if data is None else data
        files = [] if files is None else files
        headers = {} if headers is None else headers
        params = {} if params is None else params
        hooks = {} if hooks is None else hooks

        self.method = method
        self.url = url
        self.headers = headers
        self.files = files
        self.data = data
        self.json = json
        self.params = params
        self.auth = auth
        self.cookies = cookies
        self.hooks = hooks

        self.session_args = SessionArgs(
            send_kwargs=send_kwargs,
            proxies=proxies,
            stream=stream,
            verify=verify,
            cert=cert,
        )
        self.save_headers_position = save_headers_position

    def send(self, repeats=0, delay=0.1, session: "mtrequests.Session" = None, session_class: type = requests.Session, keep_cookies: bool = True) -> PendingResponse | None:
        if session is None:
            session = mtrequests.Session(session_class)
            keep_cookies = False
        return mtrequests.PendingRequest(session, self, nullcontext(), keep_cookies, None).send(repeats, delay)  # noqa

    def wrap(self, pending_pool: PendingPool, request_hook: RequestHook = None) -> PendingRequest | None:
        return pending_pool.wrap(self, request_hook)


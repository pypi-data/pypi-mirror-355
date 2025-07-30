import json
from collections import OrderedDict

import requests
import tls_client
from requests.utils import CaseInsensitiveDict

from .request import Request
from .pending_response import PendingResponse


class Session:
    def __init__(self, session_class=requests.Session):
        self.session_class: type = requests.Session
        self.session = self.session_class()
        self._req = None
        self._prep = None
        self._resp = None

        self.requests_count = 0

    def set_requests_session(self):
        self.session_class = requests.Session
        self.session = self.session_class()

    def set_tls_client_session(self):
        self.session_class = tls_client.Session
        self.session = self.session_class()

    @staticmethod
    def make_request(
            method,
            url,
            params=None,
            data=None,
            headers=None,
            cookies=None,
            files=None,
            auth=None,
            timeout=None,
            allow_redirects=True,
            proxies=None,
            hooks=None,
            stream=None,
            verify=None,
            cert=None,
            json=None,
            save_headers_position=None
    ) -> Request:
        send_kwargs = {
            "timeout": timeout,
            "allow_redirects": allow_redirects,
        }
        return Request(
            method=method.upper(),
            url=url,
            headers=headers,
            files=files,
            data=data or {},
            json=json,
            params=params or {},
            auth=auth,
            cookies=cookies,
            hooks=hooks,
            send_kwargs=send_kwargs,
            proxies=proxies,
            stream=stream,
            verify=verify,
            cert=cert,
            save_headers_position=save_headers_position
        )

    def send(self, request: Request, keep_cookie=False) -> PendingResponse:
        self.requests_count += 1
        if request.json is not None:
            request.data = json.dumps(request.json, separators=(",", ":"))
            request.json = None
        self._req = request
        if isinstance(self.session, requests.Session):
            if keep_cookie is False:
                self.session.cookies = requests.sessions.cookiejar_from_dict({})
            _request = requests.Request(
                method=request.method,
                url=request.url,
                headers=request.headers,
                files=request.files,
                data=request.data,
                json=request.json,
                params=request.params,
                auth=request.auth,
                cookies=request.cookies,
                hooks=request.hooks,
            )
            prep = self.session.prepare_request(_request)
            if request.save_headers_position:
                prepared_headers = prep.headers
                prep.headers = CaseInsensitiveDict(
                    OrderedDict(request.headers.items())
                )
                prep.headers.update(prepared_headers)

            session_args = request.session_args

            proxies = session_args.proxies or {}
            settings = self.session.merge_environment_settings(
                prep.url, proxies, session_args.stream,
                session_args.verify, session_args.cert
            )

            send_kwargs = session_args.send_kwargs
            send_kwargs.update(settings)

            self._resp = self.session.send(prep, **send_kwargs)
            return PendingResponse(self._resp, None, None, 1)

        elif isinstance(self.session, tls_client.Session):
            if keep_cookie is False:
                self.session.cookies = requests.sessions.cookiejar_from_dict({})
            if request.auth is not None:
                request = request.auth(request)
            self._resp = self.session.execute_request(
                method=request.method,
                url=request.url,
                params=request.params,
                data=request.data,
                headers=request.headers,
                cookies=request.cookies,
                json=request.json,
                allow_redirects=request.session_args.send_kwargs.get("allow_redirects", False),
                insecure_skip_verify=request.session_args.verify,
                timeout_seconds=request.session_args.send_kwargs.get("timeout", None),
                proxy=request.session_args.proxies
            )
            return PendingResponse(self._resp, None, None, 1)

    def send_all(self, *requests, keep_cookie=False):
        return [self.send(request, keep_cookie) for request in requests]

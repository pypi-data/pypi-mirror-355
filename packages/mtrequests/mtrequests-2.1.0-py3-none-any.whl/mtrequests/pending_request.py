from contextlib import nullcontext
from time import sleep
from threading import Lock

from .request import Request
from .session import Session
from .pending_response import PendingResponse


class PendingRequest:
    def __init__(self, session: Session, request: Request, lock: Lock = nullcontext(), keep_cookies: bool = True, parent = None):
        self.session = session
        self.request = request
        self.lock = lock
        self.keep_cookies = keep_cookies
        self.parent = parent

    def send(self, repeats=0, delay=0.1) -> PendingResponse | None:
        initial_repeats = repeats
        with self.lock:
            while repeats >= 0:
                if self.parent is not None and self.parent.alive is False:
                    return None
                try:
                    response = self.session.send(self.request, self.keep_cookies)
                    rsp = PendingResponse(response.response, None, self, 1 + (initial_repeats - repeats))
                except Exception as exc:
                    rsp = PendingResponse(None, exc, self, 1 + (initial_repeats - repeats))
                    rsp.request = self.session._req
                if rsp.is_valid():
                    return rsp
                repeats -= 1
                sleep(delay)
            return rsp

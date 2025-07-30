from requests import Response

import mtrequestsold


class PendingResponse:
    def __init__(
            self,
            response: Response | None,
            exception: Exception | None,
            pending_request: "mtrequestsold.PendingRequest",
            elapsed_requests: int = 1
    ):
        self.response = response
        self.exception = exception
        self.pending_request = pending_request
        self.elapsed_requests = elapsed_requests

    def is_exception(self):
        return self.exception is not None

    def is_not_exception(self):
        return self.exception is None

    def is_valid(self):
        return self.is_not_exception() and (200 <= self.status_code <= 299)

    def __bool__(self):
        return self.is_valid()

    def __repr__(self):
        if self.is_not_exception():
            if self.status_code == 200:
                return f"<PendingResponse [{self.status_code}]>"
            return f"<PendingResponse [{self.status_code}]: {self.content}>"
        exception_type = (
            f"{type(self.exception).__module__}.{type(self.exception).__name__}"
            if type(self.exception).__module__ else type(
                self.exception).__name__)
        return f"<PendingResponse: [{exception_type}({self.exception})]>"

    @property
    def status_code(self):
        return self.response.status_code

    @property
    def content(self):
        return self.response.content
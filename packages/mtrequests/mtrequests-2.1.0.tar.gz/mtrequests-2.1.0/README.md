# mtrequests
threading for requests

```python
import mtrequests

pp = mtrequests.PendingPool()

print(mtrequests.get("https://example.com").send())
print(mtrequests.get("https://example.com").wrap(pp).send())
print(pp.wrap(mtrequests.get("https://example.com")).send())
```

## New in 2.0.0+

```python
import mtrequests

session = mtrequests.Session()
session.set_tls_client_session()  # add tls-client session for requests
```
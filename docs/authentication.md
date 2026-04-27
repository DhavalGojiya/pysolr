# Authentication and HTTPS

PySolr passes authentication and TLS options through to `requests`, so the same
objects and settings you would use with `requests` usually work with PySolr.

## Basic Authentication

```python
solr = pysolr.Solr(
    "https://solr.example.com/solr/my_core",
    auth=("username", "password"),
)
```

Avoid committing credentials to source control. Read them from environment
variables or your application's secret manager.

## Custom Auth Objects

Any `requests` authentication object can be passed as `auth`.

```python
from requests_kerberos import HTTPKerberosAuth, OPTIONAL

kerberos_auth = HTTPKerberosAuth(
    mutual_authentication=OPTIONAL,
    sanitize_mutual_error_response=False,
)

solr = pysolr.Solr(
    "https://solr.example.com/solr/my_core",
    auth=kerberos_auth,
)
```

## TLS Verification

By default, TLS verification is enabled. To use a custom certificate bundle,
pass the path with `verify`:

```python
solr = pysolr.Solr(
    "https://solr.example.com/solr/my_core",
    verify="/path/to/ca-bundle.pem",
)
```

Only disable verification for local testing:

```python
solr = pysolr.Solr(
    "https://localhost:8983/solr/my_core",
    verify=False,
)
```

## Timeouts

Set `timeout` so application requests do not wait forever on a slow or
unreachable Solr server:

```python
solr = pysolr.Solr(
    "https://solr.example.com/solr/my_core",
    timeout=10,
)
```

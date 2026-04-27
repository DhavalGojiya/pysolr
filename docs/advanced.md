# Advanced Usage

PySolr keeps most Solr features available by passing keyword arguments through
to Solr. If Solr accepts a request parameter, you can usually pass it from
PySolr.

## Custom Request Handlers

The default search handler is `select`. Set a different handler on the client:

```python
solr = pysolr.Solr(
    "http://localhost:8983/solr/my_core",
    search_handler="/autocomplete",
)

results = solr.search("py")
```

Or override the handler for a single request:

```python
results = solr.search("py", search_handler="/autocomplete")
```

If your Solr deployment expects the handler in the `qt` parameter, enable
`use_qt_param`:

```python
solr = pysolr.Solr(
    "http://localhost:8983/solr/my_core",
    search_handler="/autocomplete",
    use_qt_param=True,
)
```

## More Like This

Use `more_like_this()` when your Solr configuration has the MoreLikeThis
component enabled:

```python
similar = solr.more_like_this(
    q="id:doc-1",
    mltfl="title,body",
    rows=5,
)

for doc in similar:
    print(doc["id"])
```

## Terms Suggestions

Use `suggest_terms()` with the Solr Terms component:

```python
terms = solr.suggest_terms(
    fields=["title"],
    prefix="py",
    terms_limit=10,
)

print(terms["title"])
```

The return value is a dictionary keyed by field name. Each value is a list of
`(term, count)` pairs.

## Passing Dotted Solr Parameters

Python keyword arguments cannot contain dots, so use a dictionary and unpack it:

```python
results = solr.search(
    "python",
    **{
        "defType": "edismax",
        "qf": "title^2 body",
        "hl": "true",
        "hl.fl": "title",
    },
)
```

## Custom JSON Encoders

Pass custom JSON encoder or decoder instances when your application needs
special serialization behavior:

```python
import json

solr = pysolr.Solr(
    "http://localhost:8983/solr/my_core",
    encoder=json.JSONEncoder(),
    decoder=json.JSONDecoder(),
)
```

## Custom Sessions

You can provide a `requests.Session` for connection pooling, headers, proxies,
or adapters:

```python
import requests

session = requests.Session()
session.headers.update({"User-Agent": "my-search-app/1.0"})

solr = pysolr.Solr(
    "http://localhost:8983/solr/my_core",
    session=session,
)
```

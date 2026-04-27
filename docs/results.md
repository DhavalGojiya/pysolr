# Results

`solr.search()` and `solr.more_like_this()` return a `pysolr.Results` object by
default. It wraps the decoded Solr JSON response while keeping common fields
easy to access.

## Iterate Over Documents

```python
results = solr.search("category:docs", rows=10)

for doc in results:
    print(doc["id"])
```

Iteration yields documents from `results.docs`.

```python
print(results.docs)
```

`Results` does not support indexing or slicing directly. Use `results.docs`
when you need list-style access:

```python
first_doc = results.docs[0]
```

## Count Results

```python
results = solr.search("python")

print(results.hits)
print(len(results))
```

`results.hits` is Solr's `numFound` value. `len(results)` is normally the number
of documents in the current response. When cursor pagination is active,
`len(results)` returns `results.hits`.

## Response Metadata

PySolr copies common Solr response sections to attributes:

```python
results = solr.search(
    "python",
    **{
        "facet": "true",
        "facet.field": "category",
        "hl": "true",
        "hl.fl": "title",
    },
)

print(results.facets)
print(results.highlighting)
print(results.qtime)
```

Available attributes include:

| Attribute | Solr response key |
| --- | --- |
| `debug` | `debug` |
| `facets` | `facet_counts` |
| `grouped` | `grouped` |
| `highlighting` | `highlighting` |
| `qtime` | `responseHeader.QTime` |
| `spellcheck` | `spellcheck` |
| `stats` | `stats` |
| `raw_response` | The full decoded response |

## Custom Results Class

Pass `results_cls` when constructing the client if your application wants a
different wrapper:

```python
solr = pysolr.Solr(
    "http://localhost:8983/solr/my_core",
    results_cls=dict,
)

response = solr.search("*:*")
print(response["response"]["docs"])
```

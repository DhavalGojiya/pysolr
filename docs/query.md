# Querying Data

## Basic Search

```python
results = solr.search("title:python", rows=10)
```

The first argument is the Solr `q` parameter. You can use normal Solr query
syntax, such as field queries, boolean operators, ranges, and `*:*`.

## With Parameters

Extra keyword arguments are sent to Solr as request parameters:

```python
results = solr.search(
    "python",
    rows=10,
    sort="id asc",
    fl="id,title,score",
)
```

For Solr parameters that contain dots, pass a dictionary with `**`:

```python
results = solr.search(
    "python",
    **{
        "hl": "true",
        "hl.fl": "title",
        "facet": "true",
        "facet.field": "category",
    },
)
```

## Access Results

```python
print("Matches:", results.hits)

for doc in results:
    print(doc["id"])
```

The default `Results` object exposes useful response data:

| Attribute | Description |
| --- | --- |
| `docs` | Documents returned in the current response |
| `hits` | Total number of matching documents reported by Solr |
| `facets` | Facet counts from `facet_counts` |
| `highlighting` | Highlight snippets from `highlighting` |
| `spellcheck` | Spellcheck response data |
| `stats` | Stats component response data |
| `raw_response` | Full decoded JSON response |

## Cursor Pagination

Solr cursor pagination works by passing `cursorMark="*"` and a deterministic
sort. PySolr follows the cursor as you iterate:

```python
for doc in solr.search("*:*", fl="id", sort="id asc", cursorMark="*"):
    print(doc["id"])
```

When using cursor pagination, `len(results)` reports Solr's `numFound` value
instead of only the number of documents in the first page.

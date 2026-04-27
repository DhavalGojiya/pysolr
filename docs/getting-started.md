# Getting Started

## Installation

Install PySolr from PyPI:

```bash
pip install pysolr
```

PySolr supports Python 3.10 and newer. The only required runtime dependency is
`requests`.

For SolrCloud support, install the optional extra:

```bash
pip install "pysolr[solrcloud]"
```

## Connect to Solr

Create a `Solr` client with the URL of a Solr core or collection:

```python
import pysolr

solr = pysolr.Solr(
    "http://localhost:8983/solr/my_core",
    timeout=10,
)
```

The URL normally follows this pattern:

```text
http://host:port/solr/<core-or-collection-name>
```

## Health Check

Use `ping()` to verify that Solr is reachable:

```python
solr.ping()
```

## First Query

```python
results = solr.search("*:*", rows=5)

print("Found:", len(results))

for doc in results:
    print(doc)
```

## First Index Operation

Add one or more dictionaries. Each key should match a field in your Solr schema.

```python
solr.add(
    [
        {"id": "doc-1", "title": "A first document"},
        {"id": "doc-2", "title": "Another document"},
    ],
    commit=True,
)
```

Passing `commit=True` makes the change visible immediately. For larger
applications, prefer Solr `autoCommit`, `commitWithin`, or explicit batch
commits so every request does not open a new searcher.

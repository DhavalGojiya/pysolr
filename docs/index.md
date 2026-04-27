# PySolr Documentation

PySolr is a lightweight Python client for [Apache Solr](https://solr.apache.org/).
It gives Python applications a small, direct API for sending queries, indexing
documents, deleting records, and using common Solr features.

Use these docs when you want examples that are close to real application code.
For a complete project overview, see the repository `README.md`.

## Features

- Query Solr with normal Lucene-style query strings.
- Add, update, and delete documents.
- Read result metadata such as facets, highlighting, spellcheck, and stats.
- Use commits, soft commits, `commitWithin`, and optimize operations.
- Work with SolrCloud through ZooKeeper.
- Pass custom authentication, TLS verification, and `requests.Session` objects.

## Quick Example

```python
import pysolr

solr = pysolr.Solr("http://localhost:8983/solr/my_core", timeout=10)

solr.add(
    [
        {"id": "1", "title": "Python Guide", "category": "docs"},
        {"id": "2", "title": "Solr Basics", "category": "docs"},
    ],
    commit=True,
)

results = solr.search("title:python", rows=10)

for doc in results:
    print(doc["id"], doc["title"])
```

## Common Tasks

| Task | Page |
| --- | --- |
| Install PySolr and connect to a core | [Getting Started](getting-started.md) |
| Send queries and read search metadata | [Querying](query.md) |
| Add and update documents | [Indexing](indexing.md) |
| Delete documents safely | [Deleting](delete.md) |
| Work with advanced Solr features | [Advanced Usage](advanced.md) |
| Connect to SolrCloud | [SolrCloud](solrcloud.md) |
| Manage Solr cores | [Core Admin](core-admin.md) |

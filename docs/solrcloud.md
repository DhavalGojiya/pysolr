# SolrCloud

PySolr can discover SolrCloud nodes through ZooKeeper. Install the SolrCloud
extra before using this mode:

```bash
pip install "pysolr[solrcloud]"
```

## Connect Through ZooKeeper

```python
import pysolr

zookeeper = pysolr.ZooKeeper(
    "zkhost1:2181,zkhost2:2181,zkhost3:2181",
)

solr = pysolr.SolrCloud(
    zookeeper,
    "collection1",
    timeout=10,
)
```

`SolrCloud` has the same high-level methods as `Solr`, including `search()`,
`add()`, `delete()`, `commit()`, and `optimize()`.

## Reads and Writes

For normal requests, `SolrCloud` picks an active replica URL from ZooKeeper.
For update requests, it asks ZooKeeper for a leader URL before sending the
update.

```python
solr.add([{"id": "1", "title": "Cloud document"}], commit=True)

results = solr.search("title:cloud")
```

## Retries

Configure retry behavior when constructing the client:

```python
solr = pysolr.SolrCloud(
    zookeeper,
    "collection1",
    retry_count=5,
    retry_timeout=0.2,
)
```

`retry_timeout` is the delay between attempts in seconds.

## Aliases

ZooKeeper collection aliases are supported. If the name you pass is an alias,
PySolr resolves the alias to its backing collection hosts.

```python
solr = pysolr.SolrCloud(zookeeper, "search_alias")
```

## Authentication and HTTPS

`SolrCloud` accepts the same `auth` and `verify` options as `Solr`:

```python
solr = pysolr.SolrCloud(
    zookeeper,
    "collection1",
    auth=("username", "password"),
    verify="/path/to/ca-bundle.pem",
)
```

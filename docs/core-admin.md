# Core Admin

`pysolr.SolrCoreAdmin` wraps common Solr CoreAdmin API operations for
standalone Solr cores.

## Create a Client

Use the full CoreAdmin URL:

```python
import pysolr

admin = pysolr.SolrCoreAdmin(
    "http://localhost:8983/solr/admin/cores",
    timeout=10,
)
```

The admin client accepts `auth`, `verify`, and `session` options, like the main
`Solr` client.

## Core Status

```python
status = admin.status()
print(status)

single_core = admin.status("my_core")
print(single_core)
```

## Create a Core

```python
admin.create(
    name="new_core",
    instance_dir="new_core",
    config="solrconfig.xml",
    schema="schema.xml",
)
```

When `instance_dir` is omitted, PySolr uses the core name as the instance
directory.

## Reload, Rename, Swap, and Unload

```python
admin.reload("my_core")

admin.rename("old_core", "new_core")

admin.swap("blue_core", "green_core")

admin.unload("old_core")
```

These operations return the decoded JSON response from Solr. Solr may require
specific server-side permissions or core configuration for these actions.

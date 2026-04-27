# Indexing Data

## Add Documents

```python
docs = [
    {"id": "1", "title": "Python Guide"},
    {"id": "2", "title": "Solr Basics"}
]

solr.add(docs)
```

By default, `solr.add()` sends JSON to Solr when no field boost is used. This is
usually the best path for normal indexing.

## Make Changes Visible

You can commit a single update:

```python
solr.add(docs, commit=True)
```

Or commit after a batch:

```python
solr.add(docs)
solr.commit()
```

Use `commitWithin` when you want Solr to make the change visible within a time
window without forcing an immediate commit:

```python
solr.add(docs, commitWithin=10000)
```

The value is in milliseconds.

## Atomic Updates

Use `fieldUpdates` to send Solr atomic update modifiers:

```python
solr.add(
    [{"id": "1", "views": 1}],
    fieldUpdates={"views": "inc"},
    commit=True,
)
```

Common modifiers include `set`, `add`, `remove`, `removeregex`, and `inc`.
Your Solr schema must support atomic updates for the fields you update.

## Nested Documents

PySolr supports Solr nested documents with the special `_doc` key:

```python
solr.add(
    [
        {
            "id": "book-1",
            "title": "Python Search",
            "_doc": [
                {"id": "chapter-1", "title": "Indexing"},
                {"id": "chapter-2", "title": "Querying"},
            ],
        }
    ],
    commit=True,
)
```

## Optimize

`optimize()` asks Solr to merge index segments. It can be expensive, so use it
only when you understand the operational cost for your Solr deployment.

```python
solr.optimize(maxSegments=1)
```

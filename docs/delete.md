# Deleting Data

## Delete by ID

```python
solr.delete(id="1", commit=True)
```

You can delete several IDs in one request:

```python
solr.delete(id=["1", "2", "3"], commit=True)
```

## Delete by Query

```python
solr.delete(q="title:python", commit=True)
```

Delete by query uses Solr query syntax. Be careful with broad queries because
Solr will delete every matching document.

## Delete Everything

```python
solr.delete(q="*:*", commit=True)
```

Use this only for test data, rebuild jobs, or administrative tasks where a full
clear is intended.

## Commit Policy

Like indexing, delete operations can use explicit commits, soft commits, or
Solr-side commit policies:

```python
solr.delete(id="old-doc", commit=False)
solr.commit()
```

If the client was created with `always_commit=True`, delete calls commit by
default unless you override the operation with `commit=False`.

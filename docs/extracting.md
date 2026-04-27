# Extracting Content

`solr.extract()` sends a file to Solr's `ExtractingRequestHandler`, which uses
Apache Tika to extract text and metadata from rich documents.

Your Solr server must have the extraction handler configured before this method
can work.

## Extract Without Indexing

By default, PySolr asks Solr to extract content without indexing it:

```python
with open("example.pdf", "rb") as file_obj:
    data = solr.extract(file_obj)

print(data["contents"])
print(data["metadata"])
```

The file object must have a `name` attribute. Normal files opened with `open()`
already have one.

## Index Directly

Pass `extractOnly=False` if you want Solr to index the uploaded file directly:

```python
with open("example.pdf", "rb") as file_obj:
    solr.extract(
        file_obj,
        extractOnly=False,
        **{
            "literal.id": "example-pdf",
            "literal.source": "upload",
            "commit": "true",
        },
    )
```

Direct indexing gives Solr the extracted data immediately, but it leaves less
room for application-side cleanup. Many applications prefer the default
extract-only mode, transform the returned content, and then call `solr.add()`.

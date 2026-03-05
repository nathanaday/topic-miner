# PDF Excerpt

Given a large PDF textbook, the user will provide a configuration file showing how to break this PDF into multiple excerpt PDFs.

The configuration is provided in `config.json` in the following format:

```json
{
    "input_pdf": "/Full/Path/To/Textbook/Foo-Text-8-1.pdf",
    "output_dir": "/Full/Path/To/Output/Excerpts",
    "make": {
        "1": {
            "title": "Foo-1.1",
            "page_start": 100,
            "page_end": 120
        },
        "2": {
            "title": "Foo-1.2",
            "page_start": 121,
            "page_end": 140
        }
    }
}
```

In this example configuration, the output should be:
- "/Full/Path/To/Output/Excerpts/Foo-1.1.pdf" , contains pages 100-120 of the input text
- "/Full/Path/To/Output/Excerpts/Foo-1.2.pdf" , contains pages 121-140 of the input text

The input PDF text should not be modified in any way.


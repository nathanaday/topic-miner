import json
import os
import sys

from PyPDF2 import PdfReader, PdfWriter


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.json")

    with open(config_path, "r") as f:
        config = json.load(f)

    input_pdf = config["input_pdf"]
    output_dir = config["output_dir"]

    if not os.path.isfile(input_pdf):
        print(f"Error: input PDF not found: {input_pdf}")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    reader = PdfReader(input_pdf)
    total_pages = len(reader.pages)
    print(f"Loaded: {input_pdf} ({total_pages} pages)")

    for key, entry in config["make"].items():
        title = entry["title"]
        page_start = entry["page_start"]
        page_end = entry["page_end"]

        if page_start > page_end:
            print(f"Skipping '{title}': page_start ({page_start}) > page_end ({page_end})")
            continue

        if page_start < 1 or page_end > total_pages:
            print(f"Skipping '{title}': page range {page_start}-{page_end} out of bounds (1-{total_pages})")
            continue

        writer = PdfWriter()
        for page_num in range(page_start - 1, page_end):
            writer.add_page(reader.pages[page_num])

        output_path = os.path.join(output_dir, f"{title}.pdf")
        with open(output_path, "wb") as out_file:
            writer.write(out_file)

        print(f"Created: {output_path} (pages {page_start}-{page_end}, {page_end - page_start + 1} pages)")

    print("Done.")


if __name__ == "__main__":
    main()

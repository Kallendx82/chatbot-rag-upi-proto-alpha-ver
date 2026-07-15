# Dataset PDF Conversion Tool

This script converts all non-PDF files in the dataset (Excel, Word, images, etc.) to PDF format so they can be served via the `/api/source/{doc_id}.pdf` endpoint.

## Why?

The RAG indexing pipeline extracts text from PDFs. When the frontend tries to open a source document via `/api/source/{doc_id}.pdf`, the backend checks that the file is actually a PDF (line 177 in `rag_routes.py`). Non-PDF files (Excel, Word, images) cause an HTTP 415 "Unsupported Media Type" error.

This script solves this by converting all source files to PDF **before** indexing, so the entire index points to PDF files.

## Installation

```bash
pip install openpyxl python-docx pillow reportlab PyPDF2
```

- `openpyxl`: Read Excel files
- `python-docx`: Read Word files  
- `pillow`: Convert images
- `reportlab`: Generate PDFs
- `PyPDF2`: PDF utilities (optional, for future enhancements)

## Usage

```bash
python convert_dataset_to_pdf.py <dataset_root_dir>
```

**Example:**
```bash
python convert_dataset_to_pdf.py "D:\Project\RAG_UPI\Dataset"
```

## What It Does

1. **Scans** the entire dataset directory recursively
2. **Skips** PDF files (already in the correct format)
3. **Converts**:
   - Excel (`.xlsx`, `.xls`) → PDF (tabular layout preserved)
   - Word (`.docx`, `.doc`) → PDF (paragraphs + tables extracted)
   - Images (`.png`, `.jpg`, `.gif`, `.bmp`) → PDF (white background if transparent)
4. **Saves** each converted PDF next to the original file with the same base name
5. **Reports** summary: total files, files converted, failures

## Output

Original files are **NOT deleted**. For each file:
- `DataSource.xlsx` → `DataSource.pdf` (new file created)
- `Document.docx` → `Document.pdf` (new file created)

The original files remain as backup. You can delete them after verifying the conversion.

## Error Handling

- **Corrupt files**: Logged and skipped; conversion continues for other files
- **Missing dependencies**: Script fails gracefully if a package isn't installed
- **Existing PDFs**: Script skips files where the PDF already exists (idempotent)

## Next Steps After Conversion

After running the conversion:

1. **Rebuild the index** — re-run the indexing pipeline so all sources point to PDF files:
   ```bash
   cd backend
   python -m app.indexing.build  # or your indexing script
   ```

2. **Test the endpoint** — verify that `/api/source/{doc_id}.pdf` now works:
   ```bash
   curl http://localhost:8000/api/source/ref_prodi_09.pdf -o test.pdf
   # Should return HTTP 200, not 415
   ```

## Troubleshooting

**Q: Script fails on Excel files**
- A: Some Excel files use unsupported formats (e.g., VBA macros, encrypted). These are logged and skipped.

**Q: Converted PDFs look ugly**
- A: `openpyxl` + `reportlab` are lightweight and don't preserve all formatting. For production quality, consider using LibreOffice CLI or Pandoc as an alternative.

**Q: The HTTP 415 error still occurs**
- A: After conversion, you MUST rebuild the index so the source paths point to the new PDF files. The old index still references `.xlsx`, `.docx`, etc.

## Alternative: Use External Tools

For better quality conversion, consider:

### LibreOffice CLI (recommended for production)
```bash
# Requires LibreOffice to be installed
libreoffice --headless --convert-to pdf --outdir "output_dir" "input_file"
```

### Pandoc
```bash
# Converts Word/Markdown to PDF
pandoc input.docx -o output.pdf
```

Modify the script's handlers to shell out to these tools if needed.

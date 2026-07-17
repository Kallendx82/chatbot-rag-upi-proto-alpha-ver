# Manual PDF Ingestion Pipeline

Add new PDFs to the chatbot's knowledge base: **extract → clean → chunk → embed**.
Each step is its own script (so you can inspect/debug intermediate output),
plus one orchestrator that runs all four in sequence.

```
scripts/ingestion/
├── extract.py       Step 1: PDF -> raw per-page text (OCR fallback for scans)
├── clean.py         Step 2: normalise whitespace, strip headers/footers/page numbers
├── chunk.py         Step 3: split each page into schema-aligned chunks + keywords
├── embed.py         Step 4: embed chunks, merge into the live FAISS index
└── run_pipeline.py  Runs all four steps for a folder of PDFs in one command
```

## Quick start

```bash
cd backend
.venv\Scripts\python.exe scripts\ingestion\run_pipeline.py ^
    --pdf-dir "C:\path\to\new_pdfs" ^
    --category "BiroSDM"
```

That's it — the new PDFs' chunks are embedded and merged straight into
`app/data/faiss.index` + `app/data/chunks_meta.json` + `app/data/index_info.json`
(the same files the running backend reads). **Restart the backend** afterwards
so it picks up the updated index.

`--category` is a free-text label stored on every chunk from that run (shows
up in citations/debug info) - use whatever grouping makes sense (a faculty
name, a document type, "BiroSDM", etc).

## Organizing batches - one subfolder per topic, always

`--pdf-dir` is scanned **recursively**. Point it at a folder that already
holds an earlier batch in its own subfolders (e.g. a shared "New PDF"
staging folder) and it will re-scan - and re-OCR - every old PDF too,
overwriting their category with today's `--category` label in the process.

The tool refuses to run when this looks like it's about to happen (any
direct subfolder of `--pdf-dir` that already contains PDFs), so this fails
safely rather than silently corrupting old categories. Fix it by creating a
**new** subfolder named after what this batch is actually about, and
pointing `--pdf-dir` directly at that subfolder:

```
New PDF/
├── Kalender-Akademik/       already ingested - leave alone
├── Struktur-Organisasi/     already ingested - leave alone
└── Kalender-Akademik-2027/  new batch -> point --pdf-dir here, not at "New PDF"
```

If you genuinely want to re-scan everything under a folder in one go (rare -
e.g. rebuilding categories from scratch), pass `--allow-nested-batches` to
skip the check.

## What each step does

### 1. Extract (`extract.py`)
Opens every `.pdf` under `--pdf-dir` (recursively) with PyMuPDF and pulls the
text layer per page. If a page comes back with almost no text (a scanned
page with no text layer), it's rendered to an image and run through
Tesseract OCR (Indonesian + English) instead.

**OCR requires the Tesseract binary installed separately** (it's not a pip
package): [Tesseract at UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
for Windows, then make sure `tesseract.exe` is on PATH and the `ind` +
`eng` language packs are installed. If Tesseract isn't installed, scanned
pages are skipped with a warning instead of crashing the run - you'll see
`[WARN] pytesseract/Pillow not installed` or `[WARN] OCR failed` in the
output for anything that needed it.

### 2. Clean (`clean.py`)
Strips running headers/footers ("Halaman 3 dari 10", bare page numbers),
de-hyphenates line-broken words, collapses repeated whitespace/blank lines.
Pure text transform - safe to re-run on already-cleaned text.

### 3. Chunk (`chunk.py`)
Splits each page's cleaned text into chunks of roughly 900 characters,
splitting on paragraph boundaries first and falling back to sentence
boundaries for oversized paragraphs (a "recursive" splitter). Adjacent
chunks get a one-sentence overlap for retrieval continuity across chunk
boundaries. The first heading-looking line on a page (ALL CAPS, "BAB I",
numbered headings like "1.2 ...") becomes that page's `section` label.
Also extracts a handful of frequency-based keywords per chunk (best-effort,
no NLP dependency - shown as hint chips in the UI, not used for ranking).

Chunking is **per page**, so the `page` field on every chunk always matches
the PDF page number the document viewer will jump to.

### 4. Embed (`embed.py`)
Embeds every new chunk with the exact same model + query/passage prefixing
the backend uses at query time (`app/rag/embedder.py` - this consistency
matters, a different model here would silently break retrieval). New
vectors are then merged into the existing FAISS index:

- **Brand-new document** (new `doc_id`): its vectors are appended.
- **Re-ingesting a document you already added** (same `doc_id` - i.e. same
  absolute file path): its old chunks are dropped and replaced, rather than
  duplicated. This is done by reconstructing the *existing* vectors
  straight out of the FAISS index (no re-embedding of untouched documents,
  so this stays fast even with tens of thousands of chunks already indexed)
  and only embedding what's new/changed.

Before writing anything, the current `faiss.index` / `chunks_meta.json` /
`index_info.json` are copied to `app/data/backups/<timestamp>/` so a bad
ingestion run can always be undone by restoring that folder.

## Running steps individually

Useful when debugging a specific document (e.g. checking OCR quality before
committing to the full run):

```bash
cd backend
.venv\Scripts\python.exe scripts\ingestion\extract.py --pdf-dir "C:\new_pdfs" --out _work\raw
.venv\Scripts\python.exe scripts\ingestion\clean.py    --in _work\raw       --out _work\clean
.venv\Scripts\python.exe scripts\ingestion\chunk.py    --in _work\clean     --out _work\chunks --category "BiroSDM"
.venv\Scripts\python.exe scripts\ingestion\embed.py    --in _work\chunks    --data-dir app\data
```

`run_pipeline.py` does exactly this, writing intermediate files to an
auto-named folder under `scripts/ingestion/_work/` and deleting it on
success (pass `--keep-work` to keep it, e.g. while tuning the chunker).

## Undoing a bad ingestion

```bash
cd backend/app/data
# find the timestamp folder from just before your run
cp backups/<timestamp>/faiss.index .
cp backups/<timestamp>/chunks_meta.json .
cp backups/<timestamp>/index_info.json .
```
Restart the backend afterwards.

## Where the original PDF ends up

By default, each PDF you ingest is **copied** into `backend/app/data/sources/`
as `<doc_id>.pdf`, and `chunks_meta.json`'s `source` field points at that
copy - not wherever you ingested it from. This means the chatbot's "view
source" link keeps working even if you later move, rename, or delete the
folder you dragged into `Add-New-PDF.exe`.

Pass `--sources-dir ""` to `run_pipeline.py` to disable this and keep the
old reference-only behaviour (chunks_meta.json points straight at the
original file; nothing gets copied - useful if you're ingesting from a
huge shared drive and don't want a second copy of everything).

## Notes / limitations

- `doc_id` is a hash of the PDF's **absolute file path at ingestion time**
  (not its content), computed before any copying happens. Moving/renaming
  the PDF and re-ingesting it will be treated as a brand-new document (its
  old chunks under the previous path are *not* auto-removed) - copying the
  original into `sources/` only protects against the *source folder*
  disappearing after ingestion, not against re-ingesting a relocated file.
- The keyword extractor and section/heading detector are simple heuristics,
  not real NLP - good enough for UI hints, not for anything that needs to be
  precise.
- Large `.pdf` scans (many pages needing OCR) are slow - Tesseract runs
  page-by-page on the CPU. Ingest a few documents at a time rather than an
  entire archive in one run if most of it is scanned images.

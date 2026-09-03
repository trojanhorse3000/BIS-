# BIS AI Pipeline

A hybrid AI and retrieval pipeline for the **Bureau of Indian Standards (BIS)** data:
- **Standards Master Table**: Indian Standards (`IS 1293:2019`, `IS 15820:2009`, etc.) and Quality Control Orders (QCO).
- **HUID Reference Records**: 6-character Hallmark Unique Identification for gold and silver jewellery.
- **Crosswalk Mapping**: Customs HS codes mapped to applicable Indian Standards, scheme types (Scheme-I ISI Mark, Scheme-II CRS, Scheme-IV), and ministries.
- **Vector Knowledge Base**: Regulatory scopes, technical notes, and guidelines vectorized in ChromaDB for semantic search.

---

## Directory Structure

```text
bis_ai_pipeline/
├── bis_data.db                        # SQLite database file (pre-populated)
├── chroma_store/                      # ChromaDB persistent vector database (populated via load_vectors.py)
├── schema.sql                         # SQL DDL defining standards, huid_records, and crosswalk
├── init_db.py                         # Recreates & seeds bis_data.db from data CSVs
├── load_vectors.py                    # Vectorizes vector_corpus_upload_ready.jsonl into chroma_store
├── main.py                            # End-to-end pipeline CLI runner
├── requirements.txt                   # Python dependencies
├── data/
│   ├── crosswalk_upload_ready.csv     # HS Code to IS Standards crosswalk
│   ├── huid_reference_upload_ready.csv # 6-digit HUID hallmarking reference data
│   ├── vector_corpus_upload_ready.jsonl# Text chunks with metadata for RAG embeddings
│   └── standards_upload_ready.csv     # Standards master data with QCO orders
└── pipeline/
    ├── __init__.py                    # Package exports
    ├── normalize.py                   # Query normalization & entity extraction (IS numbers, HUID, HS codes)
    ├── intent.py                      # Intent classification (HUID verification, QCO checks, Standard lookup)
    ├── retrieve.py                    # HybridRetriever combining SQLite queries with ChromaDB vector search
    └── generate.py                    # Structured answer synthesis and prompt builder
```

---

## Getting Started

### 1. Prerequisites
Ensure you have Python 3.9+ installed and required packages:
```bash
pip install pandas chromadb sentence-transformers
```

### 2. (Optional) Rebuild the SQLite Database
If you edit CSV files in `data/`, regenerate `bis_data.db`:
```bash
python init_db.py
```

### 3. Load / Re-index Vectors
To index the vector corpus into `chroma_store`:
```bash
python load_vectors.py
```

### 4. Run the Pipeline
Run an end-to-end test query:
```bash
python main.py "Please verify gold hallmark HUID code AB1234"
```
Or test an Indian Standard query:
```bash
python main.py "What are the mandatory requirements under IS 1293:2019?"
```
Or test an HS code import crosswalk query:
```bash
python main.py "Which Indian Standard applies to HS code 8504.40.90?"
```

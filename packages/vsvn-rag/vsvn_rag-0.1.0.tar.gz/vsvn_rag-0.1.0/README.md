# VSVN Modular RAG System

>  A RAG (Retrieval-Augmented Generation) system designed with a modular architecture, enabling easy reuse, independent testing, scalability, and step-by-step quality evaluation.

---

## 📦 Project Overview

The system comprises the following main modules:
- **Reader**: Reads and extracts content from various document formats such as PDF, DOCX, PPTX, XLSX,...
- **Chunker**: Divides content into smaller segments for embedding.
- **Embedder**: Represents text segments as vectors (OpenAI, local embedding,...).
- **Retriever**: Searches for information relevant to the query from a vector database (BM25, hybrid,...).
- **Generator**: Generates answers from the retrieved context (OpenAI, Prompt template,...).
- **Evaluation**: Assesses accuracy and factuality using the [RAGAS](https://github.com/explodinggradients/ragas) library.
- **Logging**: Records system logs in a standardized format, using `loguru`.
- **Pipeline**: Integrates all the above modules into a complete RAG system.

---

##  Directory Structure

```
vsvn_rag/
├── reader/             # Document reading module
├── chunker/            # Chunking module
├── embedder/           # Embedding module
├── retriever/          # Retrieval module
├── generator/          # Answer generation module
├── evaluation/         # Pipeline quality evaluation
├── logging/            # System-wide log configuration and recording
├── config/             # YAML configuration
├── docs/               # Architecture, schema documentation,...
├── shared/             # Common schemas (pydantic)
├── pipeline/           # Main pipeline runner
└── main.py             # System entry point
```

---

##  Installation

### 1. Install via pip from internal library:

```bash
pip install vsvn_rag-0.1.0-py3-none-any.whl
```

or:

```bash
pip install http://<your-private-pypi>/vsvn_rag-0.1.0-py3-none-any.whl
```

### 2. Install from source code

```bash
git clone https://your-git-url/vsvn-rag.git
cd vsvn-rag
pip install -e .
```

---

##  Usage

###   Run pipeline

```bash
python main.py
```

Or modify main.py to pass specific queries, read from a file, or from a web API.

###  Call individual modules independently

Example: using the Reader module independently

```bash
python reader/run_loader.py docs/sample.pdf
```

###  Evaluate pipeline with RAGAS

```bash
python evaluation/evaluator.py
```

Then view the chart at: `ragas_report/ragas_comparison_chart.png`

---

##  Output Example

**Multi-run evaluation chart:**

![chart](ragas_report/ragas_comparison_chart.png)

---

##  Configuration

Edit the config/config.yaml file to change:
- Model used for generator
- Retriever type
- Log file saving, log format
- Data and output paths

---

##  Documentation

- [docs/architecture.md](docs/architecture.md) – System architecture
- [docs/design.md](docs/design.md) – Design details and flow
- [docs/schema.md](docs/schema.md) – Definition of common schemas

---

##  Notes

- This project is not dependent on OpenAI (can be configured to use offline models)
- Can be extended to LangChain or LlamaIndex if needed
- Designed to integrate into any NLP pipeline with low integration cost

---

##  Contact

> Project developed by the VSVN AI team. Contact: ai-team@vsvn.vn

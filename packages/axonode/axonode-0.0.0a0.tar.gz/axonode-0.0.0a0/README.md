# Axonode

> **Graph-structured long-term memory layer for Retrieval-Augmented LLMs**  
> _Work-in-progress — API not yet stable_

[![PyPI version](https://img.shields.io/pypi/v/axonode?color=informational)](https://pypi.org/project/axonode/)
[![License](https://img.shields.io/github/license/AXONODE-DEV/axonode)](LICENSE)

---

## Why Axonode?

* **Neural–style graph storage** – typed nodes & edges mimic axons/dendrites, not flat key–value blobs.  
* **Token-budget optimisation** – automatic chunking, clustering and summarisation keep context windows small.  
* **Pluggable RAG pipeline** – slot in OpenAI, Anthropic, Llama 2/3, etc., behind a single retrieval interface.  
* **Embeddings-agnostic** – use any vector backend (Faiss, PGVector, Pinecone, etc.).  
* **Python-first** – minimal deps, zero-config `pip install axonode` to get started.

---

## Quick start

```bash
pip install axonode==0.0.0a0   # placeholder version

python -m axonode.cli ingest ./docs/*.pdf
python -m axonode.cli chat
```

> ⚠️ **Alpha quality** – the commands and import paths will change.

---

## Roadmap

| Milestone | Status |
|-----------|--------|
| MVP graph schema & local storage | ✅ DONE |
| PDF + ChatGPT ingest | ⏳ IN PROGRESS |
| REST / WebSocket API | 🔜 |
| Cloud-hosted demo | 🔜 |
| 1.0 stable release | 🛣️ |

---

## How it works (30 seconds)

```
┌── Ingest ──┐   ┌──────── Graph store ───────┐   ┌─ Retrieval + Context ┐
│  Files     │ → │  Nodes: Chunk | Concept   │ → │  Prompt w/ citations │
│  Chat logs │   │  Edges: TAGS | RELATES_TO │   └──────────────────────┘
└────────────┘   └───────────────────────────┘
```

---

## Contributing

1. Clone the repo and `poetry install` / `pip -e .`  
2. Run `make test` (pytest + coverage).  
3. Open a PR against **main**.

See **CONTRIBUTING.md** for coding-style & commit-message guidelines.

---

## License

This project is licensed under the **MIT License** – see [`LICENSE`](LICENSE).

---

## Citation

If Axonode helped your research, please cite:

```bibtex
@software{axonode_2025,
  author       = {Erez Azaria},
  title        = {Axonode},
  year         = 2025,
  url          = {https://github.com/AXONODE-DEV/axonode},
  version      = {0.0.0a0}
}
```

---

> _Questions? Open an [issue](../../issues) or join our Discord: **discord.gg/XXXXXX**_

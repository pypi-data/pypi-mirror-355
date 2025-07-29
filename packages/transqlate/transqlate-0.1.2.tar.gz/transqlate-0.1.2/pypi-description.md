# Transqlate

**Transqlate** is a production‑ready natural language → SQL assistant powered by a fine‑tuned Phi‑4 Mini model.
It lets anyone—technical or not—create and run complex queries over **SQLite, PostgreSQL, MySQL, MSSQL, or Oracle databases** using plain English.

---

## Key Features

* **Schema‑Aware NL→SQL** – Automatically extracts your database schema and prunes it with an RAG pipeline so prompts fit within model limits.
* **Interactive CLI** – Generate queries, explore schemas, edit or write SQL, and dynamically switch connections with `:changedb` (alias `:change_db`).
* **Safe Execution** – DDL/DML statements require explicit confirmation. Lost connections trigger an optional reconnect with troubleshooting tips.
* **Chain‑of‑Thought Reasoning** – View the model’s reasoning and final SQL, converted from SQLite syntax to your database dialect with automatic schema qualification.
* **Customizable Inference** – Control maximum generation length (`--max-new-tokens`), enable Python tracebacks for debugging, and point to local or HF-hosted model weights.
* **Offline‑Friendly** – Runs on CPU and can pre‑download the sentence‑transformer embedding model so future runs work without internet access.
* **Supports One‑Shot Queries** – Use `-q "question"` for quick, non‑interactive SQL generation.

---

## Installation

```bash
pip install transqlate
```

---

## Usage

**Launch the interactive CLI:**

```bash
transqlate --interactive
```

**Run a single question:**

```bash
transqlate -q "List all customers who made purchases in March." --db-path path/to/database.db
```

REPL commands include `:show schema`, `:history`, `:edit`, `:write`, `:examples`, `:clear`, `:changedb`, `:about`, and `:exit`.

---

## License

MIT License

---

## Author

Shaurya Sethi
Contact: [shauryaswapansethi@gmail.com](mailto:shauryaswapansethi@gmail.com)

---

For the full user manual and source code, visit the [GitHub repository](https://github.com/Shaurya-Sethi/transqlate-phi4) or the [Hugging Face model page](https://huggingface.co/Shaurya-Sethi/transqlate-phi4).

---

## What's New in v0.1.2

- **Cross-dialect SQL post-processing:** Automatically transforms model-generated (SQLite-style) SQL into the target dialect (PostgreSQL, MySQL, MSSQL, Oracle) with clear conversion notices.
- **Enhanced CLI workflow:** Added `:edit` for modifying generated SQL, `:write` for manual queries, and seamless database switching with `:changedb`/`:change_db`.
- **Improved schema extraction:** Robust support for PostgreSQL, Oracle, and MSSQL with qualified and escaped identifiers; Oracle system tables can now be filtered.
- **Safer execution and state management:** CLI now detects and recovers from lost connections, rolls back on errors, and requires confirmation for DDL/DML.
- **History and troubleshooting:** Query history now shows manual/edited status and execution results. Added `:troubleshoot` for step-by-step connection help.
- **Token limit control:** Set output length using the `--max-new-tokens` argument (default: 2048).
- **Numerous bugfixes and UX refinements:** Identifier quoting, error messages, startup feedback, and more.

For the full release notes, see [CHANGELOG.md](https://github.com/Shaurya-Sethi/transqlate-phi4/blob/main/CHANGELOG.md).

# AGENTS.md / CLAUDE.md

## 1. Purpose

This repository implements a reproducible ETL for territorial inequality analysis in Santiago and is being evolved toward a second Lakehouse implementation.

Agents working in this repository must prioritize:

1. correctness and reproducibility;
2. preservation of the existing local pipeline;
3. verifiable evidence over claims;
4. incremental implementation;
5. technical learning and explainability;
6. minimal, reviewable changes;
7. avoiding unnecessary architecture or technologies.

Do not treat planned capabilities as implemented.

---

## 2. Agent file identity

`AGENTS.md` and `CLAUDE.md` must remain **identical byte for byte**.

They define the same repository rules, workflow, constraints, validation expectations, and project context for both Codex and Claude Code.

The choice between Codex and Claude Code is external to the repository instructions and depends only on the token/context budget appropriate for the task.

Do not introduce tool-specific methodology, permissions, scope, architecture rules, or validation requirements into only one of these files.

Whenever one file is updated, update the other with exactly the same content.

Recommended validation:

```bash
cmp AGENTS.md CLAUDE.md
```

A non-zero result means the files have diverged and must be reconciled before continuing.

---

## 3. Current architecture

### Local implementation — existing baseline

The repository currently contains a local pipeline based on:

- Python;
- pandas;
- CSV/XLS/XLSX sources;
- SQLite;
- reproducible validation and analytical outputs.

The current documented technical baseline covers Phases 1–9:

1. structural/path validation;
2. source reading and profiling;
3. master commune dimension validation and homologation;
4. extraction to staging;
5. per-source transformation and staging validation;
6. final dataset integration;
7. final dataset validation;
8. SQLite loading and query validation;
9. reproducible exploratory analysis.

Do not remove, replace, or silently change this implementation while building the Lakehouse version.

### Lakehouse implementation — target architecture

The intended second implementation is:

`Sources → Bronze → Silver → Gold → Databricks SQL / Power BI`

Target technologies include:

- Databricks;
- PySpark;
- Delta Lake;
- SQL;
- Bronze / Silver / Gold architecture;
- Data Quality;
- Databricks Jobs / Workflows;
- incremental loads;
- Delta `MERGE`;
- schema enforcement / evolution;
- eventual Power BI serving.

These capabilities are **planned until verified in the repository or external execution evidence**.

Never describe a planned feature as implemented.

---

## 4. Source-of-truth rules

For repository work, use this order:

1. explicit instructions from the user for the current task;
2. actual current repository state;
3. existing verified data contracts, outputs, and validation reports;
4. repository documentation;
5. project roadmap / architectural documentation;
6. official current documentation for Databricks, Spark, Delta Lake, or other external technologies;
7. clearly identified inference.

If documentation conflicts with current code or generated evidence, investigate the discrepancy instead of silently choosing one.

Do not rewrite repository history or documentation to make an inconsistency disappear.

---

## 5. Domain invariants

These rules are fundamental unless the user explicitly changes the methodology.

### Analytical unit

Final analytical grain:

`one row = one commune`

### Territorial universe

The analytical universe is the **Provincia de Santiago**, currently represented by 32 communes.

### Canonical key

`codigo_comuna` is the canonical integration key.

`nombre_comuna` may be used for:

- display;
- diagnostics;
- auditing;
- validation;
- traceability.

Do **not** use raw commune names as the primary join key.

### Temporal references

The current baseline intentionally contains different reference years:

- population: 2024;
- poverty: 2022;
- green areas: 2024;
- municipal income/capacity: 2024.

Do not hide or artificially homogenize these years.

### Analytical interpretation

The analysis is:

- descriptive;
- comparative;
- non-causal.

Do not turn observed associations into causal conclusions.

---

## 6. Current baseline invariants

The current validated local final dataset is:

`data/processed/desigualdad_comunal_final.csv`

Expected baseline:

- 32 rows;
- 12 columns;
- one row per `codigo_comuna`;
- zero duplicate commune keys;
- exact coverage of the master commune dimension;
- zero nulls in the current final columns.

Current final columns:

- `codigo_comuna`
- `nombre_comuna`
- `poblacion`
- `anio_poblacion`
- `pobreza_ingresos_pct`
- `anio_pobreza`
- `areas_verdes_m2`
- `anio_areas_verdes`
- `ipp_miles_pesos`
- `anio_ingresos`
- `areas_verdes_m2_hab`
- `ipp_pesos_hab`

The current SQLite product is:

`db/lab1_desigualdad.sqlite`

Expected tables and row counts:

- `dim_comuna`: 32;
- `fact_desigualdad_comunal`: 32;
- `metadata_fuentes`: 4.

`nombre_comuna` belongs to `dim_comuna`; the fact table currently does not duplicate it.

Any intentional change to these invariants must be explicitly justified and validated.

---

## 7. Raw data rules

Files under `data/raw/` are versioned source inputs.

Do not manually edit source data to make transformations pass.

Important source behavior:

### Sources A and B — SINIM

The files use the `.xls` extension but are SpreadsheetML/XML 2003.

Do not assume ordinary binary XLS format.

The existing local implementation intentionally does not use `pandas.read_excel()` directly for these files.

### Source C — poverty

The source is XLSX.

Its poverty value is originally represented as a proportion and is converted to percentage in the local transformation.

### Source D — Census population

The source is XLSX.

Non-commune rows and aggregate rows must not enter the final commune dataset.

### Master universe

`data/raw/dim_comuna_base.csv` defines the current master commune universe.

### Source metadata

`data/raw/metadata_fuentes.csv` acts as an operational source-reading contract.

Preserve source traceability.

---

## 8. Important analytical anomaly

The current data contains a very large `areas_verdes_m2_hab` value for Quilicura.

The existing analysis treats this as a **plausible outlier**, not as a proven source error.

Do not delete, cap, replace, or “correct” this value without source evidence and an explicit methodological decision.

---

## 9. Local pipeline execution

Install dependencies with:

```bash
python -m pip install -r requirements.txt
```

The complete local pipeline supports:

```bash
python src/main.py
```

and:

```bash
python -m src.main
```

The pipeline regenerates the local ETL products and validation artifacts.

When changing pipeline behavior, validate the relevant stages and inspect generated outputs rather than relying only on process exit status.

---

## 10. Testing and validation

At the time this file was introduced, the repository did not contain a dedicated `tests/` suite or configured CI workflow.

Do not claim that automated tests or CI exist unless they have subsequently been added and verified.

The existing pipeline contains executable validation logic and generated validation reports.

Relevant evidence includes:

- `outputs/perfilado_fuentes.xlsx`
- `outputs/conflictos_fuentes.md`
- `outputs/homologacion_comunas.csv`
- `outputs/resumen_homologacion.md`
- `outputs/resumen_transformaciones.md`
- `outputs/validacion_staging.csv`
- `outputs/log_integracion.md`
- `outputs/resumen_dataset_final.md`
- `outputs/reporte_validacion_final.csv`
- `outputs/reporte_validacion_final.md`
- `outputs/reporte_carga_sqlite.md`
- `outputs/reporte_consultas_sqlite.csv`
- analytical outputs under `outputs/`

When formal tests are later introduced, add them incrementally around behavior that benefits from automated regression protection.

Do not add a testing framework merely to create the appearance of maturity.

---

## 11. Baseline versus Lakehouse

The local implementation is the functional baseline for the Lakehouse implementation.

When migrating a source or product, compare relevant properties such as:

- row counts;
- column names;
- schemas/types where semantically comparable;
- commune keys;
- missing keys;
- extra keys;
- null counts;
- duplicate counts;
- reference years;
- important metric values;
- derived calculations.

A difference is not automatically a defect, but every material difference must be investigated and documented.

Do not silently alter methodology to simplify the Databricks implementation.

---

## 12. Databricks / PySpark / Delta principles

Do not translate pandas mechanically line by line into PySpark.

The Lakehouse implementation should be used to learn and demonstrate:

- Spark DataFrames;
- explicit schemas;
- transformations;
- lazy evaluation;
- joins;
- shuffles;
- partitioning concepts;
- Delta reads/writes;
- SQL integration;
- data quality;
- orchestration.

The dataset is small.

Do not claim that Spark is required because of data volume.

Its use in this project is justified primarily by:

- practical learning;
- architectural implementation;
- transferable Data Engineering patterns.

---

## 13. Medallion responsibilities

### Bronze

Bronze should preserve source fidelity and ingestion traceability.

Prefer:

- raw or near-raw values;
- source identity;
- source file metadata;
- ingestion timestamps/batch metadata when useful;
- observed schema.

Do not perform complex business cleaning or silent row deletion in Bronze.

### Silver

Silver is responsible for:

- stable names;
- typing;
- cleaning;
- normalization;
- commune-key resolution;
- homologation;
- deduplication where justified;
- Data Quality;
- domain-consistent datasets.

`codigo_comuna` must remain the canonical commune key.

### Gold

Gold contains consumption-ready analytical products.

Preserve the dimension/fact model when appropriate:

- `dim_comuna`
- `fact_desigualdad_comunal`
- `metadata_fuentes`

Additional Gold tables require an actual analytical or serving purpose.

Do not create tables solely to make the architecture look more complex.

---

## 14. PySpark versus SQL

Prefer PySpark for:

- ingestion;
- programmatic transformation;
- parsing;
- reusable transformation logic;
- complex cleaning;
- reusable quality logic.

Prefer SQL when it is clearer for:

- analytical joins;
- Gold models;
- validation queries;
- metrics;
- serving;
- Databricks SQL consumption.

Do not force all logic into one language.

---

## 15. Delta Lake requirements

Delta Lake must eventually solve real problems in the project.

The intended progression is:

1. persist Bronze/Silver/Gold as Delta;
2. establish a working batch pipeline;
3. add incremental scenarios;
4. demonstrate inserts and updates;
5. use `MERGE` where appropriate;
6. validate reruns and idempotency;
7. exercise controlled schema enforcement/evolution.

Do not advertise `MERGE`, incremental processing, idempotency, schema evolution, or time travel until there is executable evidence.

---

## 16. Incremental implementation order

Prefer vertical implementation before horizontal expansion.

For the first Lakehouse pattern, implement one source end-to-end:

`Source → Bronze → Silver → Quality → Delta`

Validate the pattern before repeating it across all four sources.

Do not start with incremental loads, schema evolution, workflows, or Power BI before the basic batch path is working and understood.

---

## 17. Avoid overengineering

Do not add tools merely because they appear in job descriptions or Data Engineering stacks.

Initially avoid unless a concrete project problem requires them:

- Kafka;
- streaming;
- Airflow;
- dbt;
- Terraform;
- Kubernetes;
- MLflow;
- Azure Data Factory;
- microservices;
- multi-cloud architecture;
- machine learning.

Before adding technology, answer:

> What concrete problem does this solve in this repository now?

If the only answer is “it looks good on a CV”, do not add it.

---

## 18. Notebook and code organization

Do not build a single monolithic Databricks notebook.

Separate responsibilities by layer and purpose.

When reusable logic genuinely benefits from modules, extract it from notebooks.

Avoid premature abstraction.

Prefer simple, explicit, explainable transformations over artificial enterprise patterns.

---

## 19. Documentation rules

Documentation must reflect verified implementation.

Test or verify first; update implementation claims afterward.

Keep the distinction between:

- Local;
- Lakehouse;
- implemented;
- planned;
- blocked;
- experimentally validated.

The future Lakehouse architecture document should live at:

`docs/architecture/lakehouse.md`

Do not create empty architecture or source directories merely to match a planned tree.

---

## 20. Known Fase 10 status ambiguity

The current README states that Phases 10–12 are not part of the technically closed repository work.

Git history also contains Fase 10 report-generation/material-preparation work.

Therefore:

- do not automatically claim Fase 10 is technically closed;
- inspect current files and intended meaning before modifying or documenting its status;
- keep academic/report-generation artifacts separate from the Lakehouse roadmap;
- do not let historical phase numbering dictate the new Databricks architecture.

Resolve this discrepancy explicitly if a future task depends on Fase 10 status.

---

## 21. Git rules

Do not develop important changes directly on `main`.

Before modifying files, inspect at minimum:

```bash
git status
git branch --show-current
git rev-parse HEAD
```

Also inspect relevant existing files before creating replacements.

Preserve unrelated user changes.

Do not reset, clean, checkout over, or otherwise discard pre-existing work.

Prefer focused branches such as:

- `feat/databricks-foundation`
- `feat/bronze-ingestion`
- `feat/silver-transformations`
- `feat/gold-model`
- `feat/data-quality`
- `feat/databricks-workflow`
- `feat/incremental-merge`

Use the smallest branch scope that remains coherent.

Do not commit, push, merge, create releases, or deploy unless explicitly authorized by the task.

---

## 22. ChatGPT ↔ coding-agent workflow

Substantial coding tasks should follow a prompt/report/evidence workflow.

### Canonical prompt

Before implementation, define a scoped prompt `Pxx`.

Suggested location:

`docs/ai/prompts/`

Example:

`docs/ai/prompts/P00_baseline_audit.md`

The prompt should state:

- objective;
- current context;
- required inspection;
- allowed write scope;
- files/directories that must not be modified;
- acceptance criteria;
- validation commands;
- expected report;
- explicit stop conditions.

Once execution begins, do not rewrite the canonical prompt to match the implementation after the fact.

### Execution report

After implementation, produce the corresponding `Rxx`.

Suggested location:

`docs/ai/reports/`

Example:

`docs/ai/reports/R00_baseline_audit.md`

A report should contain:

- branch;
- HEAD before/after when relevant;
- files inspected;
- files changed;
- decisions taken;
- commands executed;
- validation results;
- unresolved issues;
- deviations from the prompt;
- evidence locations.

Use explicit result states:

- `PASS`
- `FAIL`
- `NO EJECUTADA`
- `BLOCKED` when an external dependency prevents execution.

A report is a summary, **not primary evidence**.

Primary evidence includes:

- code diff;
- actual test output;
- pipeline output;
- generated validation artifacts;
- table contents/counts;
- Databricks execution evidence;
- SQL query results;
- logs.

---

## 23. External/platform validation

Some future validations require an actual Databricks environment.

If the agent cannot access or execute against that environment:

- do not fabricate successful execution;
- do not convert static code inspection into a runtime `PASS`;
- mark the validation `NO EJECUTADA` or `BLOCKED`;
- state exactly what external evidence is still required.

The same rule applies to:

- Databricks Jobs;
- SQL Warehouses;
- Delta table state;
- Power BI connectivity;
- cloud resources;
- permissions.

---

## 24. External side effects

Creating or modifying cloud resources may introduce state or cost.

Do not create, modify, delete, start, stop, or deploy external resources unless explicitly authorized.

Examples include:

- clusters/compute;
- Databricks Jobs;
- SQL Warehouses;
- catalogs/schemas;
- external locations;
- Power BI connections.

Prefer inspection and planning when authorization is not explicit.

---

## 25. Change discipline

Before changing code:

1. inspect relevant implementation;
2. determine whether the capability already exists;
3. understand dependencies;
4. identify invariants affected;
5. keep the diff minimal;
6. implement only the requested scope;
7. validate behavior;
8. report evidence and remaining uncertainty.

Do not refactor unrelated code opportunistically.

Do not invent abstractions for hypothetical future needs.

Do not generate code the project owner could not reasonably explain in a technical interview.

---

## 26. Completion criteria

A task is not complete because code was written.

It is complete only when:

- requested behavior exists;
- relevant checks have actually run or are explicitly marked unexecuted;
- regressions against local baseline have been considered;
- documentation does not overstate implementation;
- evidence is available;
- unresolved limitations are explicit.

For Data Engineering work, evidence should normally cover applicable items such as:

- rows;
- schema;
- keys;
- nulls;
- duplicates;
- reference years;
- quality checks;
- derived metrics;
- baseline equivalence;
- rerun behavior.

---

## 27. Professional representation

This repository is evidence of project work.

Do not modify README, portfolio-oriented text, or other project documentation to imply:

- professional Databricks experience;
- production-scale Spark usage;
- production readiness;
- implemented incremental processing;
- implemented schema evolution;
- implemented orchestration;
- implemented Power BI integration;

unless the repository and execution evidence support the statement.

Prefer precise phrases such as:

- implemented;
- validated;
- demonstrated in project;
- planned;
- experimental;
- not yet implemented.

Evidence first. Claims second.

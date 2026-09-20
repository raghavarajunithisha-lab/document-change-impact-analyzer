# Seamflow-Inspired Document Review Prototype

> **Disclaimer:** This is an independent prototype inspired by the problem
> domain of document change detection and impact tracing. It is **not
> affiliated with, endorsed by, or connected to Seamflow** in any way.

A deterministic Python pipeline that answers: *when a manufacturer submits a
new document version, what changed, which earlier findings may be resolved,
and which other assessments must be reviewed because of those changes?*

No external dependencies — standard library only.

---

## Quick start

```bash
# 1. Download the official reference PDFs (see below)
# 2. Place them in 00_sources/official/

# 3. Run the pipeline
cd 05_prototype
python run.py

# 4. Run the ground-truth tests
python -m unittest discover tests -v
```

---

## Official reference PDFs (required)

The pipeline validates paraphrased technical facts against real Espressif
documentation. The PDFs are **not included** in this repository because
redistribution has not been confirmed. Download them yourself from Espressif:

| Document | Filename to save as | Download |
|---|---|---|
| ESP32-S3-WROOM-1 & WROOM-1U Datasheet | `esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf` | [Espressif product page](https://www.espressif.com/en/products/modules/esp32-s3-wroom-1-wroom-1u) → Documentation |
| ESP32-S3 Hardware Design Guidelines | `esp-hardware-design-guidelines-en-master-esp32s3.pdf` | [Espressif technical documents](https://www.espressif.com/en/support/documents/technical-documents?keys=ESP32-S3) |

Place both files in:

```
00_sources/official/
```

The file-presence validator will report them as missing until they are
downloaded. The rest of the pipeline (change detection, reassessment, impact
tracing) runs entirely from the paraphrased `facts.csv` and synthetic
submissions, so it works without the PDFs — only the validator's source-file
check will warn.

---

## Repository structure

```
data/
├── 00_sources/
│   ├── official/                   ← download PDFs here
│   └── source_manifest.json        ← SHA-256 hashes and download info
├── 01_reference_facts/
│   └── facts.csv                   ← 39 paraphrased technical facts
├── 02_submissions/
│   ├── v1/                         ← fictional AirSense Rev A submission
│   └── v2/                         ← fictional AirSense Rev B submission
├── 03_relationships/
│   ├── assessment_dependencies.csv ← field → assessment mapping
│   └── assessment_registry.csv     ← assessment catalogue
├── 04_ground_truth/
│   ├── change_manifest.csv         ← expected changes (test-only)
│   └── expected_results.csv        ← expected outcomes (test-only)
├── 05_prototype/
│   ├── run.py                      ← pipeline entry point
│   ├── seamflow/                   ← pipeline modules
│   └── tests/                      ← ground-truth validation
├── .gitignore
├── LICENSE                         ← MIT
└── README.md                       ← this file
```

---

## What the pipeline does

1. **Validates** dataset structure (17 files, ID alignment, staleness
   detection, new-file detection)
2. **Parses** V1 and V2 product specifications into structured fields
3. **Detects** atomic field changes and groups them (C-001 – C-006)
4. **Traces** each change through the assessment dependency graph
5. **Reassesses** every existing finding against the V2 state and detects
   regressions (e.g. the 250 mA capacity drop)
6. **Generates** a human-readable report and a JSON report

---

## What this is NOT

- This is **not** a hardware-testing project and does not prove certification
  or physical compliance.
- The AirSense product, its specifications, findings, and assessments are
  entirely **fictional test data**.
- `facts.csv` contains **paraphrased summaries** of publicly available
  Espressif documentation, not verbatim copies.
- The official PDFs are copyrighted by Espressif Systems and are not
  redistributed here.

---

## License

The prototype code and synthetic test data in this repository are released
under the [MIT License](LICENSE).

The official Espressif PDFs are subject to Espressif's own terms and are not
included.

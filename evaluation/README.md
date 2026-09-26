# Quorum — Evaluation Harness

Deterministic, evidence-based evaluation of Quorum's Pull Request analysis
(roadmap Phase 18). Metrics are computed from real stored/measured evidence —
nothing is invented.

## Layout

```text
evaluation/
├── metrics.py      # precision/recall/F1, test pass rate, coverage delta
├── dataset.py      # loads labeled PR entries from dataset/
├── dataset/        # one JSON file per manually labeled Pull Request
├── run.py          # offline runner: Semgrep evidence vs labels -> results/
└── results/        # generated result reports (gitignored)
```

## Run

From the repository root:

```bash
python -m evaluation.run
```

Prints the summary (security precision/recall/F1, test pass rate) and writes a
timestamped report to `evaluation/results/`.

## Dataset entry format

Each `dataset/*.json` entry describes one labeled Pull Request:

```json
{
  "id": "pr-0001",
  "repository": "quorum-dev/eval-demo",
  "pr_number": 1,
  "title": "Add subprocess call with shell=True",
  "files": { "run_cmd.py": "import subprocess\n..." },
  "labeled_findings": [
    { "file": "run_cmd.py", "line": 5, "severity": "high", "title": "..." }
  ],
  "labeled_tests": { "passed": 1, "total": 1 },
  "expected_coverage_delta": 5.0
}
```

`files` are written to a temp directory and scanned with the real Semgrep
pipeline. Predicted findings are matched to labels by `(file, line[, severity])`
and scored with precision/recall/F1. `labeled_tests` give the generated-test
pass rate.

## Metrics

- **Security Precision / Recall / F1** — finding-level.
- **Generated Test Pass Rate** — from labeled test outcomes.
- **Coverage Delta** — expected vs measured when measured data is supplied.

All metric functions are pure and unit-tested in `tests/test_evaluation_*.py`.
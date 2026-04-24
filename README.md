# AEA Hackathon

Utilities for anonymizing sample billing PDFs, extracting call records, and building simple network-analysis outputs from the extracted interactions.

## Context

This repository was produced in response to the [AEA MERLTech Hackathon event](https://www.eval.org/Education-Programs/AEA-MERLTech-Hackathon). Our submission via the event page has more detail about the back-and-forth with the GenAI agent by way of which we developed this repository.

To start off the exercise, we executed the following prompt in OpenCode 1.3.10 running in Ubuntu 24.04.4 LTS on WSL2, using Claude Sonnet 4.5 through a GitHub Copilot Pro subscription:

```md
I have a PDF file at `data/inputs/<filename>.pdf`. I want to extract the contents of the columns whose headers are "Dialled Number" and `Duration {HH:MM:SS} / Volume in Kb`. The desired output is a 3-column TSV where the first column is `source` (with a constant of `<caller-number>`) and the second columns are pulled from the PDF. Create a plan to do this as simply and reliably as possible.
```

Subsequent clean-up (outside the scope of what is reported in the submission) was required in order to properly anonymize source files, output data, etc. for sharing.

## Setup

This is a `uv`-managed Python project.

From a fresh clone, the default install command is:

```bash
uv sync --all-groups
```

That creates the local virtualenv, installs the package in editable mode, and installs the dev tooling used in this repo.

After that, run commands with `uv run ...`.

The repo also includes a committed `uv.lock` for reproducible installs.

## Project Layout

- `data/inputs/`: committed reference inputs and examples
- `data/outputs/`: generated outputs; safe to delete and regenerate
- `scripts/`: operator-facing shell and debugging utilities
- `src/aea_hackathon/`: Python application code
- `tests/`: automated tests

## Input Files

- `data/inputs/sample-bill-mock-nums.pdf`
  A committed example input PDF for testing extraction against clearly fake phone-number-like values.
- `data/inputs/example-mapping-file.csv`
  An example of the mapping file format expected from PDF anonymization output.
  This file is documentation by example, not a live working file.

## Example Output

- `data/outputs/sample-bill-anon.pdf`
  A committed example of anonymized output PDF content.

## Mapping Files

The anonymizer writes its mapping output to `data/outputs/mapping-file.csv` by default.

- Commit `example-mapping-file.csv` when you want to show the format.
- Do not commit generated mapping files, because they are run-specific outputs.

## UUID Generation

Generate a local UUID list with:

```bash
./scripts/make_uuids.sh 300 > /tmp/uuids.txt
```

That UUID file is an input to the anonymizer and is not expected to live in the repo.

## Common Workflows

Anonymize a PDF and emit a mapping file:

```bash
uv run anonymize-bill-pdf \
  --input-pdf /path/to/source-bill.pdf \
  --uuid-file /tmp/uuids.txt \
  --output-pdf data/outputs/sample-bill-anonymized.pdf \
  --mapping-csv data/outputs/mapping-file.csv
```

Extract call records from a bill PDF into TSV:

```bash
uv run extract-bill-data
```

Build the adjacency matrix outputs from the extracted TSV:

```bash
uv run build-call-graph
```

Render the interactive heatmap:

```bash
uv run visualize-heatmap
```

Run the test suite with:

```bash
uv run pytest
```

## Notes

- The Python modules now live under `src/aea_hackathon/`.
- Generated files belong in `data/outputs/`.
- `src/bill-extractor/` is still present as a separate embedded subproject and has not been reorganized yet.

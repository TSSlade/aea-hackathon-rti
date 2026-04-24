#!/usr/bin/env python3
"""Replace dialled numbers in a bill PDF in situ and emit a mapping CSV."""

from __future__ import annotations

import argparse
import csv
import re
from collections import OrderedDict
from pathlib import Path

import pdfplumber
from pypdf import PdfReader, PdfWriter


NUMBER_RE = re.compile(r"\d{9,10}")
ANON_TOKEN_RE = re.compile(r"[0-9a-f]{9,10}")
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_PDF = PROJECT_ROOT / "data/inputs/sample-bill.pdf"
DEFAULT_OUTPUT_PDF = PROJECT_ROOT / "data/outputs/sample-bill-anonymized.pdf"
DEFAULT_MAPPING_CSV = PROJECT_ROOT / "data/outputs/mapping-file.csv"


def normalize_number(raw: str) -> str:
    """Normalize a matched number token before mapping."""
    return "".join(ch for ch in raw if ch.isdigit())


def load_uuid_bases(path: Path, skip: int) -> list[str]:
    tokens = []
    for line in path.read_text(encoding="utf-8").splitlines()[skip:]:
        value = line.strip()
        if not value:
            continue
        tokens.append(value.replace("-", ""))
    return tokens


def collect_source_numbers(pdf_path: Path, normalize: bool) -> list[str]:
    ordered_numbers: OrderedDict[str, None] = OrderedDict()

    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            for word in page.extract_words():
                text = word["text"]
                if not NUMBER_RE.fullmatch(text):
                    continue

                source_num = normalize_number(text) if normalize else text
                ordered_numbers.setdefault(source_num, None)

    return list(ordered_numbers.keys())


def count_existing_anonymized_tokens(pdf_path: Path) -> int:
    """Count hex-like anonymized dialled-number tokens already present in the PDF."""
    count = 0

    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            for word in page.extract_words():
                if ANON_TOKEN_RE.fullmatch(word["text"]):
                    count += 1

    return count


def build_mapping(source_numbers: list[str], uuid_bases: list[str]) -> dict[str, str]:
    if len(uuid_bases) < len(source_numbers):
        raise ValueError(
            f"Not enough UUIDs: need {len(source_numbers)}, found {len(uuid_bases)} after skipping used entries."
        )

    mapping: dict[str, str] = {}
    for index, source_num in enumerate(source_numbers):
        base = uuid_bases[index]
        width = len(source_num)
        mapping[source_num] = base[:width]
    return mapping


def write_mapping_csv(path: Path, mapping: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["source_num", "uuid"])
        for source_num, uuid_token in mapping.items():
            writer.writerow([source_num, uuid_token])


def patch_pdf_text_in_place(
    input_pdf: Path,
    output_pdf: Path,
    mapping: dict[str, str],
    normalize: bool,
) -> tuple[int, int]:
    reader = PdfReader(str(input_pdf))
    writer = PdfWriter()
    replacements = 0

    for page in reader.pages:
        contents = page["/Contents"].get_object()
        data = contents.get_data()

        def replace_match(match: re.Match[bytes]) -> bytes:
            nonlocal replacements

            raw = match.group(1).decode("ascii")
            key = normalize_number(raw) if normalize else raw
            token = mapping.get(key)
            if token is None:
                return match.group(0)

            replacements += 1
            return b"(" + token.encode("ascii") + b")"

        patched = re.sub(rb"\((\d{9,10})\)", replace_match, data)
        contents.set_data(patched)
        writer.add_page(page)

    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    with output_pdf.open("wb") as handle:
        writer.write(handle)

    return replacements, len(mapping)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-pdf",
        type=Path,
        default=DEFAULT_INPUT_PDF,
        help="Source PDF to anonymize.",
    )
    parser.add_argument(
        "--output-pdf",
        type=Path,
        default=DEFAULT_OUTPUT_PDF,
        help="Destination PDF for the anonymized bill.",
    )
    parser.add_argument(
        "--uuid-file",
        type=Path,
        required=True,
        help="UUID source file.",
    )
    parser.add_argument(
        "--mapping-csv",
        type=Path,
        default=DEFAULT_MAPPING_CSV,
        help="CSV file recording source-to-UUID substitutions.",
    )
    parser.add_argument(
        "--skip-uuid-lines",
        type=int,
        default=2,
        help="Number of UUID lines already consumed for other fields.",
    )
    parser.add_argument(
        "--normalize-short-numbers",
        action="store_true",
        help="Normalize matched values by stripping non-digit characters before mapping.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    source_numbers = collect_source_numbers(
        args.input_pdf, normalize=args.normalize_short_numbers
    )
    if not source_numbers:
        existing_tokens = count_existing_anonymized_tokens(args.input_pdf)
        if existing_tokens:
            raise SystemExit(
                "No dialled numbers matching the expected phone-number pattern were found. "
                f"The input appears to already be anonymized ({existing_tokens} anonymized tokens detected)."
            )
        raise SystemExit(
            "No dialled numbers matching the expected phone-number pattern were found in the input PDF."
        )

    uuid_bases = load_uuid_bases(args.uuid_file, args.skip_uuid_lines)
    mapping = build_mapping(source_numbers, uuid_bases)
    write_mapping_csv(args.mapping_csv, mapping)
    replacements, unique_count = patch_pdf_text_in_place(
        args.input_pdf,
        args.output_pdf,
        mapping,
        normalize=args.normalize_short_numbers,
    )

    print(f"Found {replacements} dialled-number entries across {unique_count} unique numbers.")
    print(f"Wrote mapping CSV: {args.mapping_csv}")
    print(f"Wrote anonymized PDF: {args.output_pdf}")


if __name__ == "__main__":
    main()

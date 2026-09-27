#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Excel을 JSON 및 JSONL로 변환하는 공통 모듈 겸 CLI 도구."""

import argparse
import json
import math
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd

SUPPORTED_EXTENSIONS = {".xlsx", ".xlsm"}


def parse_sheet(value: str) -> Union[int, str]:
    try:
        return int(value)
    except ValueError:
        return value


def get_sheet_names(input_file: Path) -> List[str]:
    input_file = Path(input_file).expanduser().resolve()
    with pd.ExcelFile(input_file, engine="openpyxl") as workbook:
        return list(workbook.sheet_names)


def resolve_sheet_name(input_file: Path, sheet: Union[int, str]) -> str:
    sheet_names = get_sheet_names(input_file)
    if not sheet_names:
        raise ValueError("Excel 파일에 시트가 없습니다.")

    if isinstance(sheet, int):
        if sheet < 0 or sheet >= len(sheet_names):
            raise ValueError(
                "시트 인덱스 {0}이 범위를 벗어났습니다. 사용 가능 범위: 0~{1}".format(
                    sheet, len(sheet_names) - 1
                )
            )
        return sheet_names[sheet]

    if sheet not in sheet_names:
        raise ValueError(
            "시트 '{0}'을 찾을 수 없습니다. 사용 가능한 시트: {1}".format(
                sheet, ", ".join(sheet_names)
            )
        )
    return sheet


def make_unique_columns(columns: List[Any]) -> List[str]:
    result: List[str] = []
    used = set()
    for index, column in enumerate(columns, start=1):
        base = str(column).strip()
        if not base or base.lower().startswith("unnamed:"):
            base = "column_{0}".format(index)
        candidate = base
        suffix = 2
        while candidate in used:
            candidate = "{0}_{1}".format(base, suffix)
            suffix += 1
        used.add(candidate)
        result.append(candidate)
    return result


def normalize_value(value: Any) -> Any:
    if value is None:
        return None
    try:
        missing = pd.isna(value)
        if isinstance(missing, bool) and missing:
            return None
    except (TypeError, ValueError):
        pass

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if hasattr(value, "item") and callable(value.item):
        try:
            value = value.item()
        except (TypeError, ValueError):
            pass

    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "isoformat") and callable(value.isoformat):
        try:
            return value.isoformat()
        except (TypeError, ValueError):
            pass
    return str(value)


def dataframe_to_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for source_record in df.to_dict(orient="records"):
        records.append(
            {str(key): normalize_value(value) for key, value in source_record.items()}
        )
    return records


def add_metadata_to_records(
    records: List[Dict[str, Any]],
    source_file: Path,
    sheet_name: str,
) -> List[Dict[str, Any]]:
    enriched: List[Dict[str, Any]] = []
    for excel_row, record in enumerate(records, start=2):
        enriched.append(
            {
                "id": "{0}:{1}:{2}".format(source_file.stem, sheet_name, excel_row),
                "data": record,
                "metadata": {
                    "source_file": source_file.name,
                    "sheet": sheet_name,
                    "row_number": excel_row,
                },
            }
        )
    return enriched


def write_json(records: List[Dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as file:
        json.dump(records, file, ensure_ascii=False, indent=2, allow_nan=False)
        file.write("\n")


def write_jsonl(records: List[Dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")


def convert_excel(
    input_file: Union[str, Path],
    sheet: Union[int, str] = 0,
    json_output: Optional[Union[str, Path]] = None,
    jsonl_output: Optional[Union[str, Path]] = None,
    add_metadata: bool = False,
    overwrite: bool = False,
) -> Tuple[Path, Path, int, str]:
    """CLI와 GUI가 함께 사용하는 실제 변환 함수입니다."""
    input_path = Path(input_file).expanduser().resolve()
    if not input_path.exists() or not input_path.is_file():
        raise FileNotFoundError("입력 파일을 찾을 수 없습니다: {0}".format(input_path))
    if input_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError("지원하는 파일 형식은 .xlsx와 .xlsm입니다.")

    actual_sheet = resolve_sheet_name(input_path, sheet)
    json_path = (
        Path(json_output).expanduser().resolve()
        if json_output is not None
        else input_path.with_suffix(".json")
    )
    jsonl_path = (
        Path(jsonl_output).expanduser().resolve()
        if jsonl_output is not None
        else input_path.with_suffix(".jsonl")
    )

    if json_path == jsonl_path:
        raise ValueError("JSON과 JSONL 출력 경로는 서로 달라야 합니다.")
    if input_path in (json_path, jsonl_path):
        raise ValueError("출력 경로는 입력 Excel 파일과 달라야 합니다.")

    existing = [str(path) for path in (json_path, jsonl_path) if path.exists()]
    if existing and not overwrite:
        raise FileExistsError(
            "출력 파일이 이미 존재합니다:\n  {0}\n덮어쓰려면 overwrite=True 또는 --overwrite를 사용하세요.".format(
                "\n  ".join(existing)
            )
        )

    df = pd.read_excel(input_path, sheet_name=actual_sheet, engine="openpyxl")
    df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")
    df.columns = make_unique_columns(list(df.columns))

    records = dataframe_to_records(df)
    if add_metadata:
        records = add_metadata_to_records(records, input_path, actual_sheet)

    write_json(records, json_path)
    write_jsonl(records, jsonl_path)
    return json_path, jsonl_path, len(records), actual_sheet


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Excel의 지정 시트를 JSON 및 JSONL로 변환합니다."
    )
    parser.add_argument("input_file", type=Path, help="입력 .xlsx 또는 .xlsm 파일")
    parser.add_argument("--sheet", default="0", help="시트명 또는 0부터 시작하는 시트 인덱스")
    parser.add_argument("--json-output", type=Path, help="JSON 출력 경로")
    parser.add_argument("--jsonl-output", type=Path, help="JSONL 출력 경로")
    parser.add_argument("--add-metadata", action="store_true", help="출처 메타데이터 추가")
    parser.add_argument("--overwrite", action="store_true", help="기존 출력 파일 덮어쓰기")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        json_path, jsonl_path, count, sheet_name = convert_excel(
            input_file=args.input_file,
            sheet=parse_sheet(args.sheet),
            json_output=args.json_output,
            jsonl_output=args.jsonl_output,
            add_metadata=args.add_metadata,
            overwrite=args.overwrite,
        )
        print("[완료] Excel 변환이 완료되었습니다.")
        print("시트: {0}".format(sheet_name))
        print("데이터 건수: {0:,}".format(count))
        print("JSON: {0}".format(json_path))
        print("JSONL: {0}".format(jsonl_path))
        return 0
    except Exception as error:
        print("[오류] {0}".format(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

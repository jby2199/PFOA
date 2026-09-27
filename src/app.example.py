"""
[예제] CSV 파일 집계 도구

⚠️  이것은 템플릿 저장소의 예제 구현입니다.
실제 프로젝트에서는 이 코드를 프로젝트의 실제 구현으로 교체해야 합니다.

설계 추적: [SDD-M001] CSV 리더 / [SDD-M002] 합계 집계기 / [SDD-I001] CLI 인터페이스
"""
import csv
import sys
from pathlib import Path


def read_rows(csv_path: str) -> list[list[str]]:
    """[SDD-M001] CSV 리더. 헤더를 건너뛰고 데이터 행을 반환한다."""
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f'CSV file not found: {csv_path}')

    with path.open('r', encoding='utf-8', newline='') as handle:
        reader = csv.reader(handle)
        next(reader, None)
        return [row for row in reader if row]


def read_total(csv_path: str, column_index: int = 0) -> int:
    """[SDD-M002] 합계 집계기. 지정 컬럼의 숫자 값을 합산한다."""
    total = 0
    for row in read_rows(csv_path):
        if column_index >= len(row):
            continue
        try:
            total += int(float(row[column_index]))
        except ValueError:
            continue
    return total


def main(argv: list[str] | None = None) -> int:
    """[SDD-I001] CLI 인터페이스. 합계를 출력하고 종료 코드를 반환한다."""
    args = sys.argv[1:] if argv is None else argv
    if len(args) < 2:
        print('usage: app.py <csv_path> <column_index>')
        return 1

    try:
        total = read_total(args[0], int(args[1]))
    except Exception as exc:  # pragma: no cover
        print(f'error: {exc}')
        return 1

    print(total)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

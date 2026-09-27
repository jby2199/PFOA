"""[예제] 검증대상: [SDD-M001], [SDD-M002], [SDD-I001]"""
from pathlib import Path

import pytest

# 예제 파일이라 pytest 수집에서 제외된다(pytest.ini --ignore-glob=*.example.py).
# 아래 import 가 가리키는 src/app.py 는 이 저장소에 없다 - 짝이 되는 구현도
# src/app.example.py 로 두었기 때문이다. 실작업으로 쓸 땐 두 파일을 각각
# src/app.py 와 tests/test_app.py 로 복사하면 이 import 가 그대로 맞는다.
from src.app import main, read_rows, read_total


def test_read_rows_skips_header(tmp_path: Path):
    """[SDD-M001]"""
    csv_file = tmp_path / 'sample.csv'
    csv_file.write_text('id,value\n1,10\n2,20\n', encoding='utf-8')

    assert read_rows(str(csv_file)) == [['1', '10'], ['2', '20']]


def test_read_rows_missing_file_raises(tmp_path: Path):
    """[SDD-M001] 파일이 없으면 FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        read_rows(str(tmp_path / 'nope.csv'))


def test_read_total_reads_numeric_column(tmp_path: Path):
    """[SDD-M002]"""
    csv_file = tmp_path / 'sample.csv'
    csv_file.write_text('id,value\n1,10\n2,20\n3,30\n', encoding='utf-8')

    assert read_total(str(csv_file), 1) == 60


def test_read_total_ignores_invalid_rows(tmp_path: Path):
    """[SDD-M002]"""
    csv_file = tmp_path / 'sample.csv'
    csv_file.write_text('id,value\n1,10\n2,invalid\n3,30\n', encoding='utf-8')

    assert read_total(str(csv_file), 1) == 40


def test_main_missing_file_returns_1(tmp_path: Path, capsys):
    """[SDD-I001] 없는 경로는 종료 코드 1."""
    assert main([str(tmp_path / 'nope.csv'), '1']) == 1
    assert 'error:' in capsys.readouterr().out

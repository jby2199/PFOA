#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Windows 파일 선택 창에서 CLI 모듈의 변환 함수를 호출하는 GUI."""

import sys
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

try:
    from excel_to_json_cli import convert_excel, get_sheet_names
except ImportError as error:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "모듈 오류",
        "excel_to_json_gui.py와 excel_to_json_cli.py를 같은 폴더에 두세요.\n\n{0}".format(error),
        parent=root,
    )
    root.destroy()
    raise SystemExit(1)


def choose_sheet(root: tk.Tk, sheet_names):
    if len(sheet_names) == 1:
        return sheet_names[0]
    prompt = "변환할 시트 번호를 입력하세요.\n\n" + "\n".join(
        "{0}: {1}".format(index, name) for index, name in enumerate(sheet_names)
    )
    index = simpledialog.askinteger(
        "시트 선택", prompt, parent=root, minvalue=0, maxvalue=len(sheet_names) - 1
    )
    return None if index is None else sheet_names[index]


def main() -> int:
    root = tk.Tk()
    root.withdraw()
    try:
        selected = filedialog.askopenfilename(
            parent=root,
            title="변환할 Excel 파일 선택",
            filetypes=[("Excel 파일", "*.xlsx *.xlsm"), ("모든 파일", "*.*")],
        )
        if not selected:
            return 0

        input_file = Path(selected)
        sheet_names = get_sheet_names(input_file)
        sheet = choose_sheet(root, sheet_names)
        if sheet is None:
            return 0

        json_path = input_file.with_suffix(".json")
        jsonl_path = input_file.with_suffix(".jsonl")
        overwrite = False
        if json_path.exists() or jsonl_path.exists():
            overwrite = messagebox.askyesno(
                "덮어쓰기 확인",
                "출력 파일이 이미 존재합니다. 덮어쓸까요?",
                parent=root,
            )
            if not overwrite:
                return 0

        json_path, jsonl_path, count, actual_sheet = convert_excel(
            input_file=input_file,
            sheet=sheet,
            add_metadata=False,
            overwrite=overwrite,
        )
        messagebox.showinfo(
            "변환 완료",
            "시트: {0}\n데이터 건수: {1:,}\n\nJSON: {2}\nJSONL: {3}".format(
                actual_sheet, count, json_path, jsonl_path
            ),
            parent=root,
        )
        return 0
    except Exception as error:
        messagebox.showerror("변환 오류", str(error), parent=root)
        return 1
    finally:
        root.destroy()


if __name__ == "__main__":
    sys.exit(main())

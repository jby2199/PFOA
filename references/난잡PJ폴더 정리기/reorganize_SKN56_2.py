"""
SKN56 프로젝트 폴더 재정리 스크립트
원본(SRC) 읽기 전용 → 표준 구조로 DST에 복사
매핑 설정은 스크립트와 동일 폴더의 mapping.json 에서 로드
"""

import os
import re
import shutil
import json

# ─────────────────────────────────────────────
# 경로 설정
# ─────────────────────────────────────────────
SRC = r"D:\WORK\SKN56_SP"
DST = r"D:\WORK\SKN56_SP_재정리"

# ─────────────────────────────────────────────
# 매핑 파일 로드 (스크립트와 동일 폴더)
# ─────────────────────────────────────────────
_SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
_MAPPING_FILE = os.path.join(_SCRIPT_DIR, "mapping.json")

def load_mapping():
    if not os.path.exists(_MAPPING_FILE):
        raise FileNotFoundError(f"매핑 파일을 찾을 수 없습니다: {_MAPPING_FILE}")
    with open(_MAPPING_FILE, encoding="utf-8") as f:
        data = json.load(f)

    standard_folders    = data["STANDARD_FOLDERS"]
    special_path_map    = data["SPECIAL_PATH_MAP"]
    # key를 소문자로 정규화해서 로드
    template_folder_map = {k.strip().lower(): v for k, v in data["TEMPLATE_FOLDER_MAP"].items()}
    # [{"keywords": [...], "dest": "..."}] → [(keywords_list, dest), ...]
    keyword_map         = [(item["keywords"], item["dest"]) for item in data["KEYWORD_MAP"]]

    return standard_folders, special_path_map, template_folder_map, keyword_map

STANDARD_FOLDERS, SPECIAL_PATH_MAP, TEMPLATE_FOLDER_MAP, KEYWORD_MAP = load_mapping()

# ─────────────────────────────────────────────
# Draft / 연도 폴더 판별 상수
# ─────────────────────────────────────────────
_DRAFT_FILE_KW    = ["_draft", "draft", "old", "이전", "수정", "비교"]
_DRAFT_FOLDER_KW  = ["_old", "old", "historyrev", "draft", "이전", "비교"]
_RE_YEAR_FOLDER_A = re.compile(r"^\d{2}\.\s*\d{4}$")
_RE_YEAR_FOLDER_B = re.compile(r"^\d{8}$")
_RE_REV           = re.compile(r"[Rr]ev\.?(\d+)")


# ─────────────────────────────────────────────
# 헬퍼 함수
# ─────────────────────────────────────────────
def is_year_folder(name: str) -> bool:
    return bool(_RE_YEAR_FOLDER_A.match(name) or _RE_YEAR_FOLDER_B.match(name))


def extract_rev(name: str) -> str:
    m = _RE_REV.search(name)
    return f"Rev.{int(m.group(1)):02d}" if m else ""


def get_ancestors(filepath: str) -> list:
    """파일의 상위 폴더명 리스트 (직계 → 최대 6단계)"""
    parts = []
    current = os.path.dirname(filepath)
    for _ in range(6):
        head, tail = os.path.split(current)
        if not tail:
            break
        parts.append(tail)
        current = head
    return parts


# ─────────────────────────────────────────────
# 핵심 분류 함수
# ─────────────────────────────────────────────
def classify(filepath: str):
    """
    반환: (dest_relative_path, is_draft)
    dest_relative_path: DST 기준 상대 폴더 경로 (/ 구분자)
    미분류 시 dest_relative_path = None
    """
    filename  = os.path.basename(filepath)
    ancestors = get_ancestors(filepath)

    # ── Step 1. 시스템 구분 ────────────────────
    combined = filename + "".join(ancestors)
    if "NSSS" in combined:
        system = "NSSS"
    elif any(k in combined for k in ["QPSP", "QIAS"]):
        system = "QP"
    elif re.search(r'\bQP\b', combined):
        system = "QP"
    else:
        system = ""

    # ── Step 2. Rev 추출 ──────────────────────
    rev_folder = extract_rev(filename)
    if not rev_folder:
        for anc in ancestors:
            rev_folder = extract_rev(anc)
            if rev_folder:
                break

    # ── Step 3. Draft 여부 ────────────────────
    fname_lower = filename.lower()
    is_draft = any(kw in fname_lower for kw in _DRAFT_FILE_KW)
    if not is_draft:
        for anc in ancestors:
            anc_lower = anc.lower()
            if any(kw in anc_lower for kw in _DRAFT_FOLDER_KW):
                is_draft = True
                break
            if is_year_folder(anc):
                is_draft = True
                break

    # ── Step 4. 상위폴더명 완전일치 매핑 ──────
    base = None
    for anc in ancestors:
        key = anc.strip().lower()
        if key in TEMPLATE_FOLDER_MAP:
            base = TEMPLATE_FOLDER_MAP[key]
            break

    # ── Step 5. 키워드 매핑 (Step 4 실패 시) ──
    if base is None:
        search_targets = [filename] + ancestors
        for keywords, dest in KEYWORD_MAP:
            for target in search_targets:
                if any(kw.lower() in target.lower() for kw in keywords):
                    base = dest
                    break
            if base:
                break

    # ── Step 6. 최종 경로 조합 ────────────────
    if base is None:
        return None, is_draft

    parts = [base]
    if system:
        parts.append(system)
    if rev_folder:
        parts.append(rev_folder)
    if is_draft:
        parts.append("draft")

    return "/".join(parts), is_draft


# ─────────────────────────────────────────────
# 특수 폴더 치환 적용
# ─────────────────────────────────────────────
def apply_special_path(rel_dir: str):
    rel_lower = rel_dir.lower()
    for src_prefix, dst_target in SPECIAL_PATH_MAP.items():
        prefix_lower = src_prefix.lower()
        if rel_lower == prefix_lower or rel_lower.startswith(prefix_lower + "\\"):
            remainder = rel_dir[len(src_prefix):].lstrip("\\")
            return (dst_target + "\\" + remainder) if remainder else dst_target
    return None


# ─────────────────────────────────────────────
# 표준 폴더 생성
# ─────────────────────────────────────────────
def create_standard_folders():
    for folder in STANDARD_FOLDERS:
        os.makedirs(os.path.join(DST, folder.replace("/", os.sep)), exist_ok=True)


# ─────────────────────────────────────────────
# 안전 복사 (동명 파일 처리 + 긴 경로 대응 + 오류 로깅)
# ─────────────────────────────────────────────
def safe_copy(src_file: str, dst_dir: str):
    os.makedirs(dst_dir, exist_ok=True)
    filename = os.path.basename(src_file)
    dst_file = os.path.join(dst_dir, filename)
    if os.path.exists(dst_file):
        stem, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(dst_file):
            dst_file = os.path.join(dst_dir, f"{stem}_{counter}{ext}")
            counter += 1
    # Windows 긴 경로(MAX_PATH 260자 초과) 대응
    src_long = "\\\\?\\" + os.path.abspath(src_file)
    dst_long = "\\\\?\\" + os.path.abspath(dst_file)
    try:
        shutil.copy2(src_long, dst_long)
    except Exception as e:
        print(f"[오류] {src_file} -> {e}")
        error_log.append((src_file, str(e)))
    return dst_file


# ─────────────────────────────────────────────
# 메인 처리
# ─────────────────────────────────────────────
def main():
    global error_log
    error_log          = []
    copied_count       = 0
    unclassified       = []
    unclassified_count = 0

    print(f"매핑 파일: {_MAPPING_FILE}")
    print(f"출처: {SRC}")
    print(f"대상: {DST}")
    print("─" * 60)

    create_standard_folders()

    for dirpath, dirnames, filenames in os.walk(SRC):
        if not filenames:
            continue

        rel_dir         = os.path.relpath(dirpath, SRC)
        special_dst_rel = apply_special_path(rel_dir)

        for filename in filenames:
            src_file = os.path.join(dirpath, filename)

            # ── 특수 폴더 치환 우선 적용 ──
            if special_dst_rel is not None:
                dst_dir = os.path.join(DST, special_dst_rel)
                safe_copy(src_file, dst_dir)
                print(f"[복사] {os.path.join(special_dst_rel, filename)}")
                copied_count += 1
                continue

            # ── 일반 classify ──
            dest_rel, is_draft = classify(src_file)

            if dest_rel is None:
                dst_dir = os.path.join(DST, "_미분류", rel_dir)
                safe_copy(src_file, dst_dir)
                print(f"[미분류] {os.path.join('_미분류', rel_dir, filename)}")
                unclassified.append(src_file)
                unclassified_count += 1
            else:
                dst_dir = os.path.join(DST, dest_rel.replace("/", os.sep))
                safe_copy(src_file, dst_dir)
                label = "[DRAFT]" if is_draft else "[복사]"
                print(f"{label} {os.path.join(dest_rel, filename)}")
                copied_count += 1

    # ── 미분류 목록 저장 ──
    log_path = os.path.join(DST, "_미분류", "_목록.txt")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"미분류 파일 목록 (총 {unclassified_count}개)\n")
        f.write("=" * 60 + "\n")
        for p in unclassified:
            f.write(p + "\n")

    print("─" * 60)
    print(f"완료: 복사 {copied_count}개 / 미분류 {unclassified_count}개 / 오류 {len(error_log)}개")
    print(f"미분류 목록: {log_path}")

    # ── 오류 목록 저장 ──
    if error_log:
        err_path = os.path.join(DST, "_미분류", "_오류목록.txt")
        with open(err_path, "w", encoding="utf-8") as f:
            f.write(f"오류 파일 목록 (총 {len(error_log)}개)\n")
            f.write("=" * 60 + "\n")
            for path, err in error_log:
                f.write(f"{path}\t{err}\n")
        print(f"오류 목록: {err_path}")


if __name__ == "__main__":
    main()

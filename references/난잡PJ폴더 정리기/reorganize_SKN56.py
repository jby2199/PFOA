"""
SKN56 프로젝트 폴더 재정리 스크립트
원본(SRC) 읽기 전용 → 표준 구조로 DST에 복사
"""

import os
import re
import shutil

# ─────────────────────────────────────────────
# 경로 설정
# ─────────────────────────────────────────────
SRC = r"D:\WORK\SKN56_SP"
DST = r"D:\WORK\SKN56_SP_재정리"

# ─────────────────────────────────────────────
# 표준 출력 폴더 목록
# ─────────────────────────────────────────────
STANDARD_FOLDERS = [
    "0.프로젝트관리/1.계약관리",
    "0.프로젝트관리/2.공정계획/Document Delivery Schedule (DDS)",
    "0.프로젝트관리/2.공정계획/Quality Plan (QP)",
    "0.프로젝트관리/2.공정계획/보안서약서 (업체대표용)",
    "0.프로젝트관리/2.공정계획/세부 공정 일정표",
    "0.프로젝트관리/3.자원관리",
    "0.프로젝트관리/4.이슈관리",
    "0.프로젝트관리/5.회의_협의",
    "0.프로젝트관리/6.발표관련",
    "0.프로젝트관리/7.진도보고/월간용역진도보고서",
    "0.프로젝트관리/9.기성_매출",
    "1.문서교신/1.MEMO",
    "1.문서교신/2.TRANSMITTAL",
    "1.문서교신/3.제출물(접수)",
    "1.문서교신/4.산출물(송부)",
    "2.취득_공급/1.SPM",
    "2.취득_공급/2.TS(DS)",
    "3A.개념단계/21.개념단계입력물",
    "3B.요건단계/31.요건단계입력물",
    "3C.설계단계/41.설계단계입력물",
    "3D.구현단계/51.구현단계입력물",
    "3E.시험단계/61.시험단계입력물",
    "3F.설치단계",
    "3H.ComponentTest",
    "3I.IntegrationTest",
    "3J.SystemTest",
    "3K.AcceptanceTest",
    "3M.단계공통/ANR",
    "3M.단계공통/RTM",
    "3M.단계공통/TER",
    "4.유지보수/71.RT Plan",
    "4.유지보수/72.RT Proc",
    "4.유지보수/73.RT Report",
    "8.참고자료/내부작성",
    "8.참고자료/외부작성_참고자료",
    "9.기타",
    "_미분류",
]

# ─────────────────────────────────────────────
# 특수 폴더 경로 치환 맵 (SRC 상대경로 prefix 기준)
# os.walk 결과의 dirpath 에서 prefix 매칭 후 치환
# ─────────────────────────────────────────────
# key: SRC 기준 상대경로 (소문자 비교용)
# value: 치환할 DST 기준 상대경로
SPECIAL_PATH_MAP = {
    r"1.취득_공급_문서교신\7.memo":         r"1.문서교신\1.MEMO",
    r"1.취득_공급_문서교신\8.transmittal":  r"1.문서교신\2.TRANSMITTAL",
    r"1.취득_공급_문서교신\6.기타입력자료":  r"2.취득_공급",
    r"5.참고자료\내부작성":                 r"8.참고자료\내부작성",
    r"5.참고자료\외부작성_참고자료":         r"8.참고자료\외부작성_참고자료",
}

# ─────────────────────────────────────────────
# 상위폴더명 완전일치 매핑 (Step 3)
# ─────────────────────────────────────────────
TEMPLATE_FOLDER_MAP = {
    # 0.프로젝트관리 하위
    "계약관리":                           "0.프로젝트관리/1.계약관리",
    "1.계약관리":                         "0.프로젝트관리/1.계약관리",
    "공정계획":                           "0.프로젝트관리/2.공정계획",
    "2.공정계획":                         "0.프로젝트관리/2.공정계획",
    "document delivery schedule (dds)":   "0.프로젝트관리/2.공정계획/Document Delivery Schedule (DDS)",
    "quality plan (qp)":                  "0.프로젝트관리/2.공정계획/Quality Plan (QP)",
    "보안서약서 (업체대표용)":              "0.프로젝트관리/2.공정계획/보안서약서 (업체대표용)",
    "세부 공정 일정표":                    "0.프로젝트관리/2.공정계획/세부 공정 일정표",
    "자원관리":                           "0.프로젝트관리/3.자원관리",
    "3.자원관리":                         "0.프로젝트관리/3.자원관리",
    "이슈관리":                           "0.프로젝트관리/4.이슈관리",
    "4.이슈관리":                         "0.프로젝트관리/4.이슈관리",
    "회의_협의":                          "0.프로젝트관리/5.회의_협의",
    "5.회의_협의":                        "0.프로젝트관리/5.회의_협의",
    "발표관련":                           "0.프로젝트관리/6.발표관련",
    "6.발표관련":                         "0.프로젝트관리/6.발표관련",
    "진도보고":                           "0.프로젝트관리/7.진도보고",
    "7.진도보고":                         "0.프로젝트관리/7.진도보고",
    "월간용역진도보고서":                  "0.프로젝트관리/7.진도보고/월간용역진도보고서",
    "기성_매출":                          "0.프로젝트관리/9.기성_매출",
    "9.기성_매출":                        "0.프로젝트관리/9.기성_매출",
    # 1.문서교신 하위
    "memo":                               "1.문서교신/1.MEMO",
    "1.memo":                             "1.문서교신/1.MEMO",
    "7.memo":                             "1.문서교신/1.MEMO",
    "transmittal":                        "1.문서교신/2.TRANSMITTAL",
    "2.transmittal":                      "1.문서교신/2.TRANSMITTAL",
    "8.transmittal":                      "1.문서교신/2.TRANSMITTAL",
    "제출물(접수)":                        "1.문서교신/3.제출물(접수)",
    "3.제출물(접수)":                      "1.문서교신/3.제출물(접수)",
    "산출물(송부)":                        "1.문서교신/4.산출물(송부)",
    "4.산출물(송부)":                      "1.문서교신/4.산출물(송부)",
    # 2.취득_공급 하위
    "spm":                                "2.취득_공급/1.SPM",
    "1.spm":                              "2.취득_공급/1.SPM",
    "ts(ds)":                             "2.취득_공급/2.TS(DS)",
    "2.ts(ds)":                           "2.취득_공급/2.TS(DS)",
    "6.기타입력자료":                      "2.취득_공급",
    # 개발 단계
    "3a.개념단계":                        "3A.개념단계",
    "개념단계입력물":                      "3A.개념단계/21.개념단계입력물",
    "21.개념단계입력물":                   "3A.개념단계/21.개념단계입력물",
    "3b.요건단계":                        "3B.요건단계",
    "요건단계입력물":                      "3B.요건단계/31.요건단계입력물",
    "31.요건단계입력물":                   "3B.요건단계/31.요건단계입력물",
    "3c.설계단계":                        "3C.설계단계",
    "설계단계입력물":                      "3C.설계단계/41.설계단계입력물",
    "41.설계단계입력물":                   "3C.설계단계/41.설계단계입력물",
    "3d.구현단계":                        "3D.구현단계",
    "구현단계입력물":                      "3D.구현단계/51.구현단계입력물",
    "51.구현단계입력물":                   "3D.구현단계/51.구현단계입력물",
    "3e.시험단계":                        "3E.시험단계",
    "시험단계입력물":                      "3E.시험단계/61.시험단계입력물",
    "61.시험단계입력물":                   "3E.시험단계/61.시험단계입력물",
    "3f.설치단계":                        "3F.설치단계",
    # 테스트
    "3h.componenttest":                   "3H.ComponentTest",
    "1.ct plan":                          "3H.ComponentTest/1.CT Plan",
    "2.ct proc":                          "3H.ComponentTest/2.CT Proc",
    "3.ct report":                        "3H.ComponentTest/3.CT Report",
    "4.ct exec":                          "3H.ComponentTest/4.CT Exec",
    "3i.integrationtest":                 "3I.IntegrationTest",
    "1.it plan":                          "3I.IntegrationTest/1.IT Plan",
    "2.it proc":                          "3I.IntegrationTest/2.IT Proc",
    "3.it report":                        "3I.IntegrationTest/3.IT Report",
    "4.it exec":                          "3I.IntegrationTest/4.IT Exec",
    "3j.systemtest":                      "3J.SystemTest",
    "1.st plan":                          "3J.SystemTest/1.ST Plan",
    "2.st proc":                          "3J.SystemTest/2.ST Proc",
    "3.st report":                        "3J.SystemTest/3.ST Report",
    "4.st exec":                          "3J.SystemTest/4.ST Exec",
    "3k.acceptancetest":                  "3K.AcceptanceTest",
    # 단계공통
    "anr":                                "3M.단계공통/ANR",
    "rtm":                                "3M.단계공통/RTM",
    "ter":                                "3M.단계공통/TER",
    # 유지보수
    "4.유지보수":                         "4.유지보수",
    "71.rt plan":                         "4.유지보수/71.RT Plan",
    "72.rt proc":                         "4.유지보수/72.RT Proc",
    "73.rt report":                       "4.유지보수/73.RT Report",
    # 참고자료
    "8.참고자료":                         "8.참고자료",
    "5.참고자료":                         "8.참고자료",
    "내부작성":                           "8.참고자료/내부작성",
    "외부작성_참고자료":                   "8.참고자료/외부작성_참고자료",
    "9.기타":                             "9.기타",
}

# ─────────────────────────────────────────────
# 문서 유형 키워드 → 배치 폴더 매핑 (Step 4)
# ─────────────────────────────────────────────
KEYWORD_MAP = [
    (["SRS"],                                           "3B.요건단계"),
    (["RVVR"],                                          "3B.요건단계"),
    (["RSAR"],                                          "3B.요건단계"),
    (["SDD"],                                           "3C.설계단계/20.SDD"),
    (["DVVR"],                                          "3C.설계단계"),
    (["DSAR"],                                          "3C.설계단계"),
    (["IVVR"],                                          "3D.구현단계"),
    (["SCL", "SCIR", "Source", "소스코드", "SourceCode"], "3D.구현단계/51.구현단계입력물"),
    (["CT Plan", "CT_Plan"],                            "3H.ComponentTest/1.CT Plan"),
    (["CT Proc", "CT_Proc"],                            "3H.ComponentTest/2.CT Proc"),
    (["CT Report", "CT_Report"],                        "3H.ComponentTest/3.CT Report"),
    (["IT Plan"],                                       "3I.IntegrationTest/1.IT Plan"),
    (["IT Proc"],                                       "3I.IntegrationTest/2.IT Proc"),
    (["IT Report"],                                     "3I.IntegrationTest/3.IT Report"),
    (["ST Plan"],                                       "3J.SystemTest/1.ST Plan"),
    (["ST Proc"],                                       "3J.SystemTest/2.ST Proc"),
    (["ST Report"],                                     "3J.SystemTest/3.ST Report"),
    (["RTN"],                                           "4.유지보수/71.RT Plan"),
    (["RTP", "RT Procedure"],                           "4.유지보수/72.RT Proc"),
    (["RTR", "RT Report"],                              "4.유지보수/73.RT Report"),
    (["RFVVR"],                                         "4.유지보수"),
    (["SCMR"],                                          "4.유지보수"),
    (["MEMO"],                                          "1.문서교신/1.MEMO"),
    (["TRANSMITTAL"],                                   "1.문서교신/2.TRANSMITTAL"),
    (["DDS"],                                           "0.프로젝트관리/2.공정계획/Document Delivery Schedule (DDS)"),
    (["보안서약"],                                       "0.프로젝트관리/2.공정계획/보안서약서 (업체대표용)"),
    (["공정일정", "세부일정"],                           "0.프로젝트관리/2.공정계획/세부 공정 일정표"),
    (["진도보고", "월간용역"],                           "0.프로젝트관리/7.진도보고/월간용역진도보고서"),
    (["기성", "매출"],                                  "0.프로젝트관리/9.기성_매출"),
    (["PHAR", "CVVR"],                                  "3A.개념단계/21.개념단계입력물"),
    (["ANR"],                                           "3M.단계공통/ANR"),
    (["RTM"],                                           "3M.단계공통/RTM"),
    (["TER"],                                           "3M.단계공통/TER"),
    (["매뉴얼", "코드분석", "참고"],                     "8.참고자료/내부작성"),
]

# ─────────────────────────────────────────────
# 헬퍼 함수
# ─────────────────────────────────────────────
_RE_YEAR_FOLDER_A = re.compile(r"^\d{2}\.\s*\d{4}$")
_RE_YEAR_FOLDER_B = re.compile(r"^\d{8}$")
_RE_REV           = re.compile(r"[Rr]ev\.?(\d+)")
_DRAFT_FILE_KW    = ["_draft", "draft", "old", "이전", "수정", "비교"]
_DRAFT_FOLDER_KW  = ["_old", "old", "historyrev", "draft", "이전", "비교"]


def is_year_folder(name: str) -> bool:
    return bool(_RE_YEAR_FOLDER_A.match(name) or _RE_YEAR_FOLDER_B.match(name))


def extract_rev(name: str) -> str:
    """파일명·폴더명에서 Rev 번호 추출 → 'Rev.NN' 형식 반환, 없으면 ''"""
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
    dest_relative_path: DST 기준 상대 폴더 경로 (/ 구분자 사용)
    """
    filename  = os.path.basename(filepath)
    name_stem = os.path.splitext(filename)[0]
    ancestors = get_ancestors(filepath)  # [직계, 차상위, 차차상위]

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
        return None, is_draft  # 미분류

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
def apply_special_path(rel_dir: str) -> str | None:
    """
    rel_dir: SRC 기준 상대 경로 (소문자 비교)
    일치하면 DST 기준 대체 경로 반환, 아니면 None
    """
    rel_lower = rel_dir.lower()
    for src_prefix, dst_target in SPECIAL_PATH_MAP.items():
        if rel_lower == src_prefix or rel_lower.startswith(src_prefix + "\\"):
            # 접두어 이후 남은 경로 붙이기
            remainder = rel_dir[len(src_prefix):].lstrip("\\")
            result = dst_target
            if remainder:
                result = dst_target + "\\" + remainder
            return result
    return None


# ─────────────────────────────────────────────
# 폴더 생성
# ─────────────────────────────────────────────
def create_standard_folders():
    for folder in STANDARD_FOLDERS:
        path = os.path.join(DST, folder.replace("/", os.sep))
        os.makedirs(path, exist_ok=True)


# ─────────────────────────────────────────────
# 안전 복사 (동명 파일 처리)
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
    shutil.copy2(src_file, dst_file)
    return dst_file


# ─────────────────────────────────────────────
# 메인 처리
# ─────────────────────────────────────────────
def main():
    copied_count      = 0
    unclassified      = []
    unclassified_count = 0

    print(f"출처: {SRC}")
    print(f"대상: {DST}")
    print("─" * 60)

    create_standard_folders()

    for dirpath, dirnames, filenames in os.walk(SRC):
        # 연도 폴더면 해당 폴더 자체는 건너뜀 (내부 파일은 처리)
        rel_dir = os.path.relpath(dirpath, SRC)

        # 파일 없으면 스킵
        if not filenames:
            continue

        # 특수 폴더 치환 확인
        special_dst_rel = apply_special_path(rel_dir)

        for filename in filenames:
            src_file = os.path.join(dirpath, filename)

            # ── 특수 폴더 치환 적용된 경우 직접 복사 ──
            if special_dst_rel is not None:
                dst_dir = os.path.join(DST, special_dst_rel)
                safe_copy(src_file, dst_dir)
                print(f"[복사] {os.path.join(special_dst_rel, filename)}")
                copied_count += 1
                continue

            # ── 일반 classify ──
            dest_rel, is_draft = classify(src_file)

            if dest_rel is None:
                # 미분류: 원본 상대경로 유지
                unclassified_rel = os.path.join("_미분류", rel_dir, filename)
                dst_dir = os.path.join(DST, "_미분류", rel_dir)
                safe_copy(src_file, dst_dir)
                print(f"[미분류] {unclassified_rel}")
                unclassified.append(src_file)
                unclassified_count += 1
            else:
                dst_dir = os.path.join(DST, dest_rel.replace("/", os.sep))
                safe_copy(src_file, dst_dir)
                label = "[DRAFT]" if is_draft else "[복사]"
                print(f"{label} {os.path.join(dest_rel, filename)}")
                copied_count += 1

    # ── 미분류 목록 파일 저장 ──
    log_path = os.path.join(DST, "_미분류", "_목록.txt")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"미분류 파일 목록 (총 {unclassified_count}개)\n")
        f.write("=" * 60 + "\n")
        for p in unclassified:
            f.write(p + "\n")

    print("─" * 60)
    print(f"완료: 복사 {copied_count}개 / 미분류 {unclassified_count}개")
    print(f"미분류 목록: {log_path}")


if __name__ == "__main__":
    main()

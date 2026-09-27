import os
import shutil
import re

# ==========================================
# 1. 경로 설정 (환경에 맞게 수정 가능)
# ==========================================
SRC = r"D:\WORK\SKN56SP"
DST = r"D:\WORK\SKN56_SP재정리"
UNCLASSIFIED_LOG = DST + "_미분류_목록.txt"

# ==========================================
# 2. 표준 출력 폴더 구조 (실행 시 자동 생성)
# ==========================================
STANDARD_FOLDERS = [
    "0.프로젝트관리/1.계약관리", "0.프로젝트관리/2.공정계획/Document Delivery Schedule (DDS)", 
    "0.프로젝트관리/2.공정계획/Quality Plan (QP)", "0.프로젝트관리/2.공정계획/보안서약서 (업체대표용)", 
    "0.프로젝트관리/2.공정계획/세부 공정 일정표", "0.프로젝트관리/3.자원관리", "0.프로젝트관리/4.이슈관리", 
    "0.프로젝트관리/5.회의협의", "0.프로젝트관리/6.발표관련", "0.프로젝트관리/7.진도보고/월간용역진도보고서", 
    "0.프로젝트관리/9.기성매출", "1.문서교신/1.MEMO", "1.문서교신/2.TRANSMITTAL", 
    "1.문서교신/3.제출물(접수)", "1.문서교신/4.산출물(송부)", "2.취득공급/1.SPM", 
    "2.취득공급/2.TS(DS)", "3A.개념단계/21.개념단계입력물", "3B.요건단계/31.요건단계입력물", 
    "3C.설계단계/41.설계단계입력물", "3D.구현단계/51.구현단계입력물", "3E.시험단계/61.시험단계입력물", 
    "3F.설치단계", "3H.ComponentTest", "3I.IntegrationTest", "3J.SystemTest", "3K.AcceptanceTest", 
    "3M.단계공통/ANR", "3M.단계공통/RTM", "3M.단계공통/TER", "4.유지보수/71.RT Plan", 
    "4.유지보수/72.RT Proc", "4.유지보수/73.RT Report", "8.참고자료/내부작성", 
    "8.참고자료/외부작성참고자료", "9.기타", "_미분류"
]

# ==========================================
# 3. 매핑 데이터 정의
# ==========================================
SPECIAL_FOLDER_MAP = {
    r"1.취득공급문서교신\7.MEMO": r"1.문서교신\1.MEMO",
    r"1.취득공급문서교신\8.TRANSMITTAL": r"1.문서교신\2.TRANSMITTAL",
    r"1.취득공급문서교신\6.기타입력자료": r"2.취득_공급",
    r"5.참고자료\내부작성": r"8.참고자료\내부작성",
    r"5.참고자료\외부작성참고자료": r"8.참고자료\외부작성_참고자료"
}

TEMPLATE_FOLDER_MAP = {
    # 0.프로젝트관리
    "계약관리": "0.프로젝트관리/1.계약관리", "1.계약관리": "0.프로젝트관리/1.계약관리",
    "공정계획": "0.프로젝트관리/2.공정계획", "2.공정계획": "0.프로젝트관리/2.공정계획",
    "document delivery schedule (dds)": "0.프로젝트관리/2.공정계획/Document Delivery Schedule (DDS)",
    "quality plan (qp)": "0.프로젝트관리/2.공정계획/Quality Plan (QP)",
    "보안서약서 (업체대표용)": "0.프로젝트관리/2.공정계획/보안서약서 (업체대표용)",
    "세부 공정 일정표": "0.프로젝트관리/2.공정계획/세부 공정 일정표",
    "자원관리": "0.프로젝트관리/3.자원관리", "3.자원관리": "0.프로젝트관리/3.자원관리",
    "이슈관리": "0.프로젝트관리/4.이슈관리", "4.이슈관리": "0.프로젝트관리/4.이슈관리",
    "회의협의": "0.프로젝트관리/5.회의협의", "5.회의협의": "0.프로젝트관리/5.회의협의",
    "발표관련": "0.프로젝트관리/6.발표관련", "6.발표관련": "0.프로젝트관리/6.발표관련",
    "진도보고": "0.프로젝트관리/7.진도보고", "7.진도보고": "0.프로젝트관리/7.진도보고",
    "월간용역진도보고서": "0.프로젝트관리/7.진도보고/월간용역진도보고서",
    "기성매출": "0.프로젝트관리/9.기성매출", "9.기성매출": "0.프로젝트관리/9.기성매출",
    # 1.문서교신
    "memo": "1.문서교신/1.MEMO", "1.memo": "1.문서교신/1.MEMO", "7.memo": "1.문서교신/1.MEMO",
    "transmittal": "1.문서교신/2.TRANSMITTAL", "2.transmittal": "1.문서교신/2.TRANSMITTAL", "8.transmittal": "1.문서교신/2.TRANSMITTAL",
    "제출물(접수)": "1.문서교신/3.제출물(접수)", "3.제출물(접수)": "1.문서교신/3.제출물(접수)",
    "산출물(송부)": "1.문서교신/4.산출물(송부)", "4.산출물(송부)": "1.문서교신/4.산출물(송부)",
    # 2.취득_공급
    "spm": "2.취득공급/1.SPM", "1.spm": "2.취득공급/1.SPM",
    "ts(ds)": "2.취득공급/2.TS(DS)", "2.ts(ds)": "2.취득공급/2.TS(DS)", "6.기타입력자료": "2.취득공급",
    # 3.개발단계
    "3a.개념단계": "3A.개념단계", "개념단계입력물": "3A.개념단계/21.개념단계입력물", "21.개념단계입력물": "3A.개념단계/21.개념단계입력물",
    "3b.요건단계": "3B.요건단계", "요건단계입력물": "3B.요건단계/31.요건단계입력물", "31.요건단계입력물": "3B.요건단계/31.요건단계입력물",
    "3c.설계단계": "3C.설계단계", "설계단계입력물": "3C.설계단계/41.설계단계입력물", "41.설계단계입력물": "3C.설계단계/41.설계단계입력물",
    "3d.구현단계": "3D.구현단계", "구현단계입력물": "3D.구현단계/51.구현단계입력물", "51.구현단계입력물": "3D.구현단계/51.구현단계입력물",
    "3e.시험단계": "3E.시험단계", "시험단계입력물": "3E.시험단계/61.시험단계입력물", "61.시험단계입력물": "3E.시험단계/61.시험단계입력물",
    "3f.설치단계": "3F.설치단계",
    # 테스트 & 단계공통
    "3h.componenttest": "3H.ComponentTest", "1.ct plan": "3H.ComponentTest/1.CT Plan", "2.ct proc": "3H.ComponentTest/2.CT Proc", "3.ct report": "3H.ComponentTest/3.CT Report", "4.ct exec": "3H.ComponentTest/4.CT Exec",
    "3i.integrationtest": "3I.IntegrationTest", "1.it plan": "3I.IntegrationTest/1.IT Plan", "2.it proc": "3I.IntegrationTest/2.IT Proc", "3.it report": "3I.IntegrationTest/3.IT Report", "4.it exec": "3I.IntegrationTest/4.IT Exec",
    "3j.systemtest": "3J.SystemTest", "1.st plan": "3J.SystemTest/1.ST Plan", "2.st proc": "3J.SystemTest/2.ST Proc", "3.st report": "3J.SystemTest/3.ST Report", "4.st exec": "3J.SystemTest/4.ST Exec",
    "3k.acceptancetest": "3K.AcceptanceTest",
    "anr": "3M.단계공통/ANR", "rtm": "3M.단계공통/RTM", "ter": "3M.단계공통/TER",
    # 4.유지보수 & 참고자료 등
    "4.유지보수": "4.유지보수", "71.rt plan": "4.유지보수/71.RT Plan", "72.rt proc": "4.유지보수/72.RT Proc", "73.rt report": "4.유지보수/73.RT Report",
    "8.참고자료": "8.참고자료", "5.참고자료": "8.참고자료", "내부작성": "8.참고자료/내부작성", "외부작성_참고자료": "8.참고자료/외부작성참고자료", "9.기타": "9.기타"
}

KEYWORD_MAP = [
    (["SRS", "RVVR", "RSAR"], "3B.요건단계"),
    (["SDD"], "3C.설계단계/20.SDD"),
    (["DVVR", "DSAR"], "3C.설계단계"),
    (["IVVR"], "3D.구현단계"),
    (["SCL", "SCIR", "Source", "소스코드", "SourceCode"], "3D.구현단계/51.구현단계입력물"),
    (["CT Plan", "CT_Plan"], "3H.ComponentTest/1.CT Plan"),
    (["CT Proc", "CT_Proc"], "3H.ComponentTest/2.CT Proc"),
    (["CT Report", "CT_Report"], "3H.ComponentTest/3.CT Report"),
    (["IT Plan"], "3I.IntegrationTest/1.IT Plan"),
    (["IT Proc"], "3I.IntegrationTest/2.IT Proc"),
    (["IT Report"], "3I.IntegrationTest/3.IT Report"),
    (["ST Plan"], "3J.SystemTest/1.ST Plan"),
    (["ST Proc"], "3J.SystemTest/2.ST Proc"),
    (["ST Report"], "3J.SystemTest/3.ST Report"),
    (["RTN"], "4.유지보수/71.RT Plan"),
    (["RTP", "RT Procedure"], "4.유지보수/72.RT Proc"),
    (["RTR", "RT Report"], "4.유지보수/73.RT Report"),
    (["RFVVR", "SCMR"], "4.유지보수"),
    (["MEMO"], "1.문서교신/1.MEMO"),
    (["TRANSMITTAL"], "1.문서교신/2.TRANSMITTAL"),
    (["DDS"], "0.프로젝트관리/2.공정계획/Document Delivery Schedule (DDS)"),
    (["보안서약"], "0.프로젝트관리/2.공정계획/보안서약서 (업체대표용)"),
    (["공정일정", "세부일정"], "0.프로젝트관리/2.공정계획/세부 공정 일정표"),
    (["진도보고", "월간용역"], "0.프로젝트관리/7.진도보고/월간용역진도보고서"),
    (["기성", "매출"], "0.프로젝트관리/9.기성매출"),
    (["PHAR", "CVVR"], "3A.개념단계/21.개념단계입력물"),
    (["ANR"], "3M.단계공통/ANR"),
    (["RTM"], "3M.단계공통/RTM"),
    (["TER"], "3M.단계공통/TER"),
    (["매뉴얼", "코드분석", "참고"], "8.참고자료/내부작성")
]

# ==========================================
# 4. 핵심 함수 정의
# ==========================================
def preprocess_path(rel_path):
    """사전 정의된 경로 문자열 치환 적용"""
    for old, new in SPECIAL_FOLDER_MAP.items():
        if old in rel_path:
            rel_path = rel_path.replace(old, new)
    return rel_path

def classify(filepath, rel_path):
    """파일 경로를 분석하여 목적지 상대경로와 draft 여부 반환"""
    # 전처리 및 요소 분리
    rel_path = preprocess_path(rel_path)
    parts = rel_path.split(os.sep)
    filename = parts[-1]
    parents = parts[:-1][::-1] # 직계상위 -> 차상위 -> 차차상위 (역순 배열)
    
    system = ""
    rev_folder = ""
    is_draft = False
    base_folder = ""
    
    # [Step 1] 시스템 구분 추출
    check_str = filename + "_" + (parents[0] if parents else "")
    if "NSSS" in check_str.upper():
        system = "NSSS"
    elif any(k in check_str.upper() for k in ["QP", "QPSP", "QIAS"]):
        system = "QP"

    # [Step 2] 버전(Rev.) 추출
    rev_pattern = re.compile(r"Rev\.(\d+)", re.IGNORECASE)
    for target in [filename] + parents:
        match = rev_pattern.search(target)
        if match:
            rev_folder = f"Rev.{match.group(1).zfill(2)}"
            break

    # [Step 3] Draft 여부 판단
    fn_lower, p_lower = filename.lower(), (parents[0].lower() if parents else "")
    draft_fn_keys = ["_draft", "draft", "old", "이전", "수정", "비교"]
    draft_p_keys = ["_old", "old", "historyrev", "draft", "이전", "비교"]
    
    if any(k in fn_lower for k in draft_fn_keys) or any(k in p_lower for k in draft_p_keys):
        is_draft = True
        
    date_pattern1 = re.compile(r"^\d{2}\.\s*\d{4}")
    date_pattern2 = re.compile(r"^\d{8}")
    if any(date_pattern1.match(p) or date_pattern2.match(p) for p in parents):
        is_draft = True

    # [Step 4] 상위폴더명 완전일치 매핑
    for p in parents[:3]: # 최대 3단계 탐색
        clean_p = p.strip().lower()
        if clean_p in TEMPLATE_FOLDER_MAP:
            base_folder = TEMPLATE_FOLDER_MAP[clean_p]
            break

    # [Step 5] 문서 유형 -> 배치 폴더 매핑 (Step 4 실패 시에만)
    if not base_folder:
        for target in [filename] + parents[:2]: # 파일명 -> 상위 -> 차상위
            for keywords, dest in KEYWORD_MAP:
                if any(k.lower() in target.lower() for k in keywords):
                    base_folder = dest
                    break
            if base_folder: break

    # [Step 6] 최종 목적지 경로 조합
    if not base_folder:
        return os.path.join("_미분류", os.path.dirname(rel_path)), is_draft, False
        
    final_path = base_folder
    if system: final_path = os.path.join(final_path, system)
    if rev_folder: final_path = os.path.join(final_path, rev_folder)
    if is_draft: final_path = os.path.join(final_path, "draft")
    
    # 경로 정규화 (역슬래시/슬래시 통일)
    return os.path.normpath(final_path), is_draft, True

# ==========================================
# 5. 메인 실행 로직
# ==========================================
def main():
    print("파일 재배치 작업을 시작합니다...")
    
    # DST 및 표준 폴더 자동 생성
    for f in STANDARD_FOLDERS:
        os.makedirs(os.path.join(DST, os.path.normpath(f)), exist_ok=True)
        
    copy_count = 0
    unclassified_list = []
    
    for root, dirs, files in os.walk(SRC):
        for file in files:
            src_file_path = os.path.join(root, file)
            rel_path = os.path.relpath(src_file_path, SRC)
            
            dest_sub_path, is_draft, is_classified = classify(src_file_path, rel_path)
            dest_dir = os.path.join(DST, dest_sub_path)
            dest_file_path = os.path.join(dest_dir, file)
            
            # 목적지 폴더가 없으면 생성 (동적 생성되는 폴더 처리)
            os.makedirs(dest_dir, exist_ok=True)
            
            # 원본 손상 방지용 shutil.copy2
            shutil.copy2(src_file_path, dest_file_path)
            copy_count += 1
            
            # 결과 출력 포맷팅
            prefix = "[DRAFT]" if is_draft and is_classified else "[미분류]" if not is_classified else "[복사]"
            out_path = os.path.join(dest_sub_path, file).replace("\\", "/")
            print(f"{prefix} {out_path}")
            
            if not is_classified:
                unclassified_list.append(src_file_path)

    # 미분류 파일 목록 저장
    with open(UNCLASSIFIED_LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(unclassified_list))
        
    print(f"\n완료: 복사 {copy_count}개 / 미분류 {len(unclassified_list)}개")
    if unclassified_list:
        print(f"미분류 목록: {UNCLASSIFIED_LOG}")

if __name__ == "__main__":
    main()
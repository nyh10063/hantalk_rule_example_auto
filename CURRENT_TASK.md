# Current Task

## 현재 상태

- Current phase: Phase 1 pilot
- Current item: df003 `-(으)ㄴ 적이 있/없다`
- Current project goal: 300개 문법항목의 검색용 정규식 및 오탐 필터링 인코더용 positive/negative 예문 구축 자동화
- Current immediate goal: `datasets/gold/gold.xlsx` 원본 형식을 확정한 뒤, df003에 대해 정규식 골드 50개 기준 recall=1 검색용 정규식을 만들고, corpus hit 검수표까지 생성하는 최소 Python CLI pipeline 준비

## 현재까지 완료

- `plan0429.md`에 전체 계획 작성됨
- 장기 작업 기준 문서 구조 결정됨
- Phase 1에서는 무거운 도구를 도입하지 않기로 결정함
- 기준 문서 4개 생성:
  - `AGENTS.md`
  - `PROJECT_SPEC.md`
  - `CURRENT_TASK.md`
  - `DECISIONS.md`
- 기본 작업 폴더 생성:
  - `configs/`
  - `exported_gold/`
  - `regex/`
  - `hits/`
  - `labels/`
  - `datasets/`
  - `logs/`
  - `src/`
- `configs/grammar_items.yaml` 초안 작성 완료
- `exported_gold/df003_gold_50.jsonl` 형식 확정 및 50개 positive gold 변환 완료
- 정규식 gold의 장기 원본은 `datasets/gold/gold.xlsx`로 관리하고, item별 JSONL은 자동 생성 산출물로 두기로 문서화함
- `PROJECT_SPEC.md`의 df003 gold schema를 실제 JSONL 형식에 맞게 업데이트함

## 이번에 테스트한 것

- 기존 `정규식 골드/정규식 골드_df003.xlsx`에서 positive gold가 50개인지 확인함
- 각 gold record의 `target_spans`가 sentence의 문자 구간에서 `target_text`로 추출되는지 확인함
- `df003_gold_50.jsonl`이 JSONL 50줄로 생성되도록 검증함

## 다음 작업

1. `datasets/gold/gold.xlsx` 템플릿과 sheet schema 확정
2. `gold.xlsx`에서 `exported_gold/{item_id}_gold_50.jsonl`을 생성하는 export 흐름 설계
3. df003 정규식 v1 초안 작성
4. `src/test_gold.py` 구현
5. gold 50개 기준 recall, FN report 출력 형식 구현
6. `regex/df003_versions.jsonl`에 정규식 버전 기록 구조 구현

## 주의사항

- 현재는 인코더 fine-tuning을 하지 않습니다.
- Phase 1에서는 Label Studio, Prefect, DVC, MLflow를 도입하지 않습니다.
- LLM이 만든 TP/FP 판단은 임시 참고용이며 gold label이 아닙니다.
- 사람이 만든 gold와 human review 파일은 명시 요청 없이 덮어쓰지 않습니다.
- 정규식 recall=1은 사람이 만든 gold 50개 기준입니다.

## 미해결 문제

- 사용할 일반 말뭉치 위치와 형식이 아직 확정되지 않았습니다.
- df003 span 기준은 기존 df003 gold span을 변환해 사용했지만, 최종 교육적 span 정책은 사람이 확인해야 합니다.


## 2026-04-30 업무 시작 점검

- 읽은 기준 문서: `AGENTS.md` → `PROJECT_SPEC.md` → `DECISIONS.md` → `CURRENT_TASK.md`
- 기준 문서상 현재 Phase: Phase 1 pilot
- 기준 문서상 현재 항목: df003 `-(으)ㄴ 적이 있/없다`
- 기준 문서상 현재 목표: df003 gold 50개 기준 recall=1 검색용 정규식과 최소 Python CLI pipeline 준비
- 현재 허용되는 다음 작업: df003 정규식 v1 초안, `src/test_gold.py`, FN report, `regex/df003_versions.jsonl` 구조 구현
- 현재 금지/보류: Label Studio, Prefect, DVC, MLflow, LangGraph, 인코더 fine-tuning
- 이번 점검에서 새로운 결정 사항은 없음. 따라서 `DECISIONS.md`는 업데이트하지 않음.


## 2026-04-30 item_id 정리

- `ㄴ/은 적 있/없(경험 유무 서술)` pilot 항목의 item_id를 `df003`으로 통일함.
- 기준 문서, config, gold JSONL, 파일명, 계획 문서 안의 pilot item 표기를 함께 정리함.
- gold 파일명은 `exported_gold/df003_gold_50.jsonl`로 변경됨.
- 다음 작업은 `df003` 정규식 v1 초안과 `src/test_gold.py` 구현임.


## 2026-04-30 ID 네이밍 규칙 기록

- 신규 문법항목 ID 부여 규칙을 `PROJECT_SPEC.md`의 `문법항목 ID 네이밍 규칙` 섹션에 기록함.
- 결정 이유와 접두어 목록을 `DECISIONS.md`에 기록함.
- 현재 pilot ID는 새 네이밍 규칙에 따라 `df003`으로 확정됨.


## 2026-04-30 df003 migration

- `ㄴ/은 적 있/없(경험 유무 서술)` pilot 항목 ID를 새 네이밍 규칙에 맞춰 `df003`으로 최종 통일함.
- 기준 문서, config, JSONL, 계획 문서, 관련 파일명을 함께 정리함.
- gold 파일명은 `exported_gold/df003_gold_50.jsonl`로 변경됨.
- 다음 작업은 `df003` 정규식 v1 초안과 `src/test_gold.py` 구현임.

## 2026-04-30 dict.xlsx detect_rules 단순화

- `PROJECT_SPEC.md`에 `dict.xlsx` 설계 원칙을 추가함.
- `detect_rules` 시트는 검색용 표면 정규식 전용으로 두기로 함.
- 사람이 관리하는 `detect_rules` 시트에서는 `comp_id`, `rule_type`, `engine`을 제거하기로 함.
- 내부 로더가 `rule_type=surface_regex`, `engine=re`를 자동 보충하도록 향후 구현할 예정임.
- `rule_components.comp_id`는 component span 탐색에 필요하므로 유지함.

## 2026-05-01 items.group 기록

- `PROJECT_SPEC.md`에 `items` 시트의 `group` 열 정의를 추가함.
- `group=a`: 오탐제거가 필요 없는 문법항목.
- `group=b`: 오탐제거가 필요하지만 다의의미 분별이 필요 없는 문법항목.
- `group=c`: 오탐제거 및 다의의미 분별이 필요한 문법항목.
- 한톡 프로젝트는 사용자의 실시간 발화 분석에서는 기본적으로 다의의미 분별을 하지 않기로 함.
- 다의의미 분별이 필요한 항목은 문법항목 사용 제안 패널이나 발화 오류 수정 제안에서 활용하기 위해 `group=c`로 구분함.

## 2026-05-01 detect_rules.scope 제거 기록

- `PROJECT_SPEC.md`의 `detect_rules` 제거 열 목록에 `scope`를 추가함.
- `DECISIONS.md`에 `detect_rules.scope` 제거 이유를 기록함.
- 이전 프로젝트의 `scope`는 실버 라벨 구축용 규칙과 추론용 규칙을 분리하기 위한 열이었음.
- HanTalk 프로젝트에서는 실버 라벨을 만들지 않으므로 사람이 관리하는 `detect_rules` 시트에서 `scope`를 제거하기로 함.

## 2026-05-01 detect_rules 실행 원칙 기록

- `PROJECT_SPEC.md`에 `detect_rules` 실행 원칙을 추가함.
- `detect_rules`는 `stage` 순서대로 `detect` → `verify`를 실행함.
- `stage=detect`는 후보 생성을 담당하며 recall을 우선하여 넓게 잡음.
- `stage=verify`는 후보 생성에 쓰지 않고 hard_fail 용도로만 사용함.
- verify hard_fail은 100% 확실한 오탐일 때만 적용함.
- 같은 stage 안에서는 `priority`가 작은 규칙부터 실행함.
- 한 행은 하나의 규칙으로 취급함.

## 2026-05-01 detect_rules.target 허용값 기록

- `PROJECT_SPEC.md`에 `stage`별 `target` 허용값을 추가함.
- `stage=detect`인 규칙은 `target=raw_sentence`만 허용함.
- `stage=verify`인 규칙은 `target=raw_sentence` 또는 `target=char_window`만 허용함.
- `DECISIONS.md`에 `detect_rules.target` 허용값 제한 이유를 기록함.

## 2026-05-01 token_window 명칭 변경 예정 기록

- 기존 프로젝트의 `token_window`가 실제로는 후보 span 주변 문자 단위 window로 동작한다는 점을 반영함.
- 새 HanTalk 규칙 모듈에서는 `token_window` 명칭을 `char_window`로 바꾸기로 함.
- `PROJECT_SPEC.md`의 verify target 허용값을 `raw_sentence` 또는 `char_window`로 기록함.
- `DECISIONS.md`에 `token_window` → `char_window` 명칭 변경 결정을 기록함.
- 지금은 코드 변경을 하지 않고, 나중에 규칙 모듈을 따로 만들 때 반영함.

## 2026-05-01 confidence_delta 제거 기록

- `PROJECT_SPEC.md`의 `detect_rules` 제거 열 목록에 `confidence_delta`를 추가함.
- `DECISIONS.md`에 `detect_rules.confidence_delta` 제거 이유를 기록함.
- 새 규칙 모듈에서는 `verify`를 점수 조정이 아니라 hard_fail 전용으로 사용할 예정임.
- 따라서 `detect_rules`에서 점수 누적/조정용 `confidence_delta`를 사용하지 않기로 함.

## 2026-05-01 HanTalk 상위 구성과 속도 원칙 기록

- `PROJECT_SPEC.md`에 HanTalk 상위 구성과 원칙 섹션을 추가함.
- 중요 주제로 문법항목 기반, 끊기지 않는 대화, 교수 내용의 패널형 간접 제시를 기록함.
- 학습자 발화 진단 항목으로 문법항목 출현, 목표 문법항목 사용 기회, 실제 사용, 부정확 사용, 회피/대체 사용을 기록함.
- 변경점 2-(4): 대화 주제 조건에 따라 LLM이 대화를 주도할 수 있도록 하고, RAG 등 적합한 방식을 탐색하기로 기록함.
- 변경점 3-(2): 응답 속도에 영향을 줄 수 있는 요소는 가급적 빠른 방식으로 실현하기로 기록함.
- `DECISIONS.md`에 대화 주제 조건 기반 LLM 주도와 응답 속도 우선 구현 결정을 추가함.

## 2026-05-01 gold.xlsx 원본 관리 원칙 기록

- `PROJECT_SPEC.md`에 `gold.xlsx` 설계 원칙을 추가함.
- 정규식 gold 원본은 `datasets/gold/gold.xlsx`로 사람이 관리하기로 함.
- `exported_gold/{item_id}_gold_50.jsonl`은 `gold.xlsx`에서 자동 생성되는 item별 검증용 산출물로 정리함.
- item별 JSONL은 앱 응답속도 목적이 아니라 개발/검증 속도와 재현성을 위한 파일로 기록함.
- `DECISIONS.md`에 `gold.xlsx` 원본 관리 및 item별 JSONL 자동 생성 결정을 추가함.

## 2026-05-01 gold.xlsx 보강 기록

- `AGENTS.md`의 프로젝트 핵심 원칙에 `datasets/gold/gold.xlsx`가 정규식 gold의 사람 관리 원본임을 추가함.
- `PROJECT_SPEC.md`의 파일 구조에 `datasets/gold/gold.xlsx`와 `datasets/dict/dict.xlsx` 위치를 명시함.
- `CURRENT_TASK.md`의 현재 목표와 다음 작업에 `gold.xlsx` 템플릿 및 export 흐름 확정을 먼저 수행하도록 반영함.

## 2026-05-01 워킹 폴더 및 산출물 폴더 기록

- 메인 워킹 폴더를 `/Users/yonghyunnam/coding/HanTalk_group/HanTalk/rule_example_auto`로 기록함.
- Git에 올리지 않는 artifact 저장 폴더를 `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti`로 기록함.
- Git에 올리지 않는 작업 데이터 폴더를 `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_work`로 기록함.
- `gold.xlsx`에서 자동 생성되는 item별 gold JSONL 폴더명을 `gold/`에서 `exported_gold/`로 바꾼 원칙을 반영함.
- `PROJECT_SPEC.md`, `DECISIONS.md`, `CURRENT_TASK.md`, `AGENTS.md`의 관련 경로 표기를 점검 및 갱신함.

## 2026-05-01 Git/Colab 운영 원칙 기록

- 기본 작업 흐름을 `로컬 컴퓨터 작업 → GitHub main push → Colab pull → Colab 실행/검증`으로 기록함.
- Colab에서는 원칙적으로 코드를 직접 수정하지 않고, 수정이 필요하면 로컬에서 고친 뒤 GitHub를 통해 반영하기로 함.
- Phase 1에서는 브랜치를 늘리지 않고 `main` 중심으로 운영할 수 있음을 기록함.
- `PROJECT_SPEC.md`, `DECISIONS.md`, `CURRENT_TASK.md`, `AGENTS.md`에 관련 운영 원칙을 반영함.

# Agent Instructions

이 문서는 HanTalk 문법항목 검색 규칙 및 예문 구축 자동화 프로젝트에서 Codex가 작업할 때 반드시 먼저 읽어야 하는 운영 규칙입니다.

## 시작 루틴

코드나 문서를 수정하기 전에 항상 아래 파일을 순서대로 읽습니다.

1. `AGENTS.md`
2. `PROJECT_SPEC.md`
3. `DECISIONS.md`
4. `CURRENT_TASK.md`

대화 기록만 믿고 작업하지 않습니다. 장기 프로젝트의 기준은 저장소 안의 문서입니다.

## 프로젝트 핵심 원칙

- 목표는 300개 한국어 문법항목에 대해 `검색용 정규식 + 오탐 필터링 인코더` 구축을 위한 positive/negative 예문을 반자동으로 만드는 것입니다.
- Phase 1에서는 `-(으)ㄴ 적이 있/없다` 계열인 df003 pilot 하나를 끝까지 완성합니다.
- 현재 단계의 목표는 예문 구축 자동화이며, 인코더 미세조정은 아직 수행하지 않습니다.
- 정규식의 `recall=1`은 전체 한국어에서의 절대 recall이 아니라, 사람이 만든 정규식 골드 50개 기준의 recall=1을 뜻합니다.
- 정규식 gold의 사람 관리 원본은 `datasets/gold/gold.xlsx`입니다.
- `exported_gold/{item_id}_gold_50.jsonl`은 `gold.xlsx`에서 자동 생성되는 검증용 산출물이며, 사람이 직접 관리하는 원본으로 취급하지 않습니다.
- LLM은 정규식 초안, FN 원인 분석, 수정안 제안, TP/FP 임시 판단에 사용할 수 있지만, 최종 gold label을 결정하지 않습니다.
- TP/FP 최종 판정과 애매한 사례의 기준 확정은 사람이 합니다.

## Phase 1 금지 사항

명시적 요청이 없는 한 Phase 1에서는 아래를 도입하지 않습니다.

- Label Studio
- Prefect
- DVC
- MLflow
- LangGraph
- 인코더 fine-tuning
- 복잡한 multi-agent workflow

Phase 1은 Python CLI, CSV/Excel 검수표, JSONL/CSV 로그 중심으로 작게 구현합니다.

## 변경 규칙

- 파일 schema를 바꾸면 반드시 `PROJECT_SPEC.md`를 함께 업데이트합니다.
- 중요한 설계 결정을 하면 반드시 `DECISIONS.md`에 날짜와 이유를 기록합니다.
- 실질적인 변경을 마친 뒤에는 반드시 `CURRENT_TASK.md`를 업데이트합니다.
- 기존 사람이 작성한 gold, labels 파일은 명시 요청 없이 덮어쓰지 않습니다.
- 자동 생성 파일과 사람이 확정한 파일을 파일명이나 폴더로 구분합니다.

## 작업 완료 시 CURRENT_TASK.md 업데이트 항목

작업이 끝나면 `CURRENT_TASK.md`에 아래 내용을 갱신합니다.

- 변경한 것
- 테스트한 것
- 다음에 할 것
- 미해결 문제
- 사람이 확인해야 할 것

코딩은 Codex가 한다. Claude Code는 계획, 분석, 판단, 수정 제안 등을 수행한다. chatGPT는 사령탑 역할을 맡는다.

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
- Phase 1에서는 df003 pilot을 완료했고, 현재는 ps_id 기반 polyset task인 `ps_ce002`까지 같은 자동화 구조를 확장합니다.
- 현재 단계의 목표는 예문 구축 자동화이며, 인코더 미세조정은 아직 수행하지 않습니다.
- 정규식의 `recall=1`은 전체 한국어에서의 절대 recall이 아니라, 사람이 만든 정규식 골드 50개 기준의 recall=1을 뜻합니다.
- 정규식 gold의 사람 관리 원본은 Excel입니다. 현재 반복 자동화에서는 `datasets/gold/gold_ps_??.xlsx` 같은 item/polyset-specific skeleton Excel도 받을 수 있고, 장기 aggregate로 `gold.xlsx`를 둘 수 있습니다.
- `exported_gold/{unit_id}_gold_50.jsonl`은 gold Excel에서 자동 생성되는 검증용 산출물이며, 사람이 직접 관리하는 원본으로 취급하지 않습니다.
- 문법항목 사전의 사람 관리 원본도 Excel입니다. 단일 item은 `e_id`, polyset task는 `ps_id`를 detect/encoder task unit으로 사용하며, runtime은 항상 Excel에서 생성한 detector bundle을 읽습니다.
- LLM은 정규식 초안, FN 원인 분석, 수정안 제안, TP/FP 임시 판단에 사용할 수 있지만, 최종 gold label을 결정하지 않습니다.
- TP/FP 최종 판정과 애매한 사례의 기준 확정은 사람이 합니다.
- 검색용 정규식은 gold recall=1을 유지하는 조건에서만 말뭉치 FP를 줄이는 방향으로 수정합니다.
- 검색용 정규식 단계에서는 먼저 넓은 정규식으로 gold recall=1을 확보합니다. 브릿지는 문법항목별 정규식 복붙이 아니라 `rule_components.bridge_id`와 공용 bridge registry로 연결하며, gold recall과 corpus FP/span 품질에 실제 도움이 될 때 채택합니다.
- 일반 말뭉치 검색은 공통 prepared corpus batch를 만든 뒤 DetectorEngine으로 검색합니다. batch_002부터 예문 구축 batch 비율은 일상대화 5,000행, 뉴스 700행, 비출판물 2,000행, 학습자 말뭉치 2,500행입니다. batch_000/001은 이전 비율로 생성된 산출물이므로 그대로 보존합니다.
- gold recall=1을 통과한 unit의 corpus search와 human/Codex review 파일 생성은 `src/run_corpus_review_batch.py`를 우선 사용합니다. 이 wrapper는 bundle을 생성하지 않고, 이미 생성된 `--bundle`과 `--gold`를 다시 평가해 gold gate를 통과한 경우에만 검색을 실행합니다.
- `run_corpus_review_batch.py`는 `*_codex_review.*` 이후 `*_codex_review_first_pass.*`를 생성합니다. 사람이 실제로 열어 작업할 기준 파일은 first-pass 파일입니다. 해당 unit의 first-pass profile이 없으면 실패가 아니라 `skipped_no_profile`로 기록하고, blank/no-profile 템플릿을 사람 검수용으로 넘깁니다.
- 규칙 수정은 gold FN 또는 사람이 확정한 systematic FP를 근거로만 수행합니다. Codex/LLM 임시 판단만으로 dict rule을 수정하지 않습니다.
- corpus review 후 `FP/TP <= 2`이면 규칙 다듬기를 멈추고 결과를 제출합니다. `FP/TP > 2`이고 `processed_batches < 3`이면 안전한 systematic FP 제거 규칙만 검토합니다.
- `processed_batches >= 3`이면 batch 추가와 규칙 다듬기를 중단하고 현재 확보량으로 다음 판단을 합니다. `processed_batches`는 검색된 batch 수가 아니라 사람이 labeled review를 완료해 summary에 반영한 batch 수입니다.
- 규칙을 수정한 뒤에는 반드시 bundle을 재생성하고 gold 50 recall test를 다시 실행합니다. gold recall이 1보다 낮아지는 수정은 채택하지 않습니다.

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
- 기본 작업 흐름은 `로컬 컴퓨터 작업 → GitHub main push → Colab pull`입니다.
- Colab은 실행/검증 환경으로 사용하고, 코드와 기준 문서는 로컬 워킹 폴더에서 수정한 뒤 GitHub를 통해 Colab에 반영합니다.

## 작업 완료 시 CURRENT_TASK.md 업데이트 항목

작업이 끝나면 `CURRENT_TASK.md`에 아래 내용을 갱신합니다.

- 변경한 것
- 테스트한 것
- 다음에 할 것
- 미해결 문제
- 사람이 확인해야 할 것

코딩은 Codex가 한다. Claude Code는 계획, 분석, 판단, 수정 제안 등을 수행한다. chatGPT는 사령탑 역할을 맡는다.

# Project Spec

## 최종 주제

```text
LLM-based dialogue-based ICALL system
Grammar-guided conversational ICALL system
```

HanTalk은 한톡 구현과 연구를 함께 수행하는 프로젝트입니다. 최종 주제는 문법항목 기반 대화형 ICALL 시스템이며, 아래 요소를 핵심 주제로 둡니다.

중요 주제:

- 문법항목 기반
- 난이도 제어
- 끊기지 않는 대화. 녹음 버튼 없이 자연스럽게 이어지는 대화 경험을 포함합니다.
- 교수 내용의 패널형 간접 제시
- 주제 유지 연속 대화

구성 및 연구항목:

1. 300개 한국어 문법항목에 대한 정규식 및 인코더 학습용 예문 반자동 생성
2. 문법항목 기반 대화 난이도 제어. 연구항목입니다.
3. 학습자에 대한 문법항목 발화 유도 및 발화의 문법항목 사용 양상 진단. 연구항목입니다.
4. 문법항목 조건부 패널 피드백 및 연습 생성. 연구항목입니다.
5. 대화 주제 조건에 의거하여 LLM이 대화를 주도할 수 있도록 하는 기능. RAG 등 가장 적합한 방식을 찾고 활용할 예정이며, 연구항목입니다.

학습자 발화의 문법항목 사용 양상 진단에서는 아래 항목을 다룹니다.

- 문법항목의 출현
- 목표 문법항목 사용 기회
- 실제 사용
- 부정확 사용
- 회피, 대체 사용

추가 목표:

- 실제 학습자가 사용할 수 있어야 합니다.
- 응답 속도에 영향을 줄 수 있는 요소들은 가급적 빠른 방식으로 실현합니다.

현재 이 저장소에서 수행 중인 작업은 위 구성 중 `1. 300개 한국어 문법항목에 대한 정규식 및 인코더 학습용 예문 반자동 생성`입니다.

## 현재 프로젝트 목표

이 프로젝트의 목표는 300개 한국어 문법항목에 대해 다음 과정을 반자동화하는 것입니다.

```text
문법항목 정의
→ 검색용 정규식 생성
→ 정규식 골드 50개에서 recall 확인
→ FN 원인 분석 및 정규식 수정
→ 일반 말뭉치에서 후보 검색
→ 사람이 TP/FP/span 검수
→ 인코더 오탐 필터링 학습용 positive/negative 예문 구축
```

현재는 인코더 미세조정 전 단계입니다. 우선 문법항목별 positive/negative 예문 구축 자동화를 목표로 합니다.


## 로컬 작업 경로

현재 메인 워킹 폴더는 아래 경로입니다.

```text
/Users/yonghyunnam/coding/HanTalk_group/HanTalk/rule_example_auto
```

관련 로컬 폴더는 아래처럼 구분합니다.

| 경로 | 역할 | Git 포함 여부 |
| --- | --- | --- |
| `/Users/yonghyunnam/coding/HanTalk_group/HanTalk/rule_example_auto` | 규칙/예문 반자동화 코드와 문서가 들어가는 메인 워킹 폴더 | 포함 |
| `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti` | 실행 결과, 모델 산출물, 큰 artifact 저장 폴더 | 제외 |
| `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_work` | 말뭉치, 중간 작업 데이터, 비공개/대용량 데이터 폴더 | 제외 |

원칙:

- `HanTalk_arti`와 `HanTalk_work`는 Git에 올리지 않습니다.
- 코드와 기준 문서, 사람이 관리하는 작은 설정 파일은 `rule_example_auto` 안에서 관리합니다.
- 자동 생성 결과와 큰 중간 산출물은 필요에 따라 `HanTalk_arti` 또는 `HanTalk_work`에 둡니다.

## Git/Colab 운영 원칙

이 프로젝트의 기본 작업 흐름은 아래 단방향 흐름을 따릅니다.

```text
로컬 컴퓨터 작업
→ GitHub main push
→ Colab pull
→ Colab에서 실행/검증
```

원칙:

- 코드, 기준 문서, 작은 설정 파일은 로컬 컴퓨터의 메인 워킹 폴더에서 수정합니다.
- GitHub는 로컬 작업물을 Colab으로 전달하는 기준 원격 저장소로 사용합니다.
- Colab은 실행/검증 환경으로 사용하고, 원칙적으로 Colab에서 직접 코드를 수정하지 않습니다.
- Colab에서 수정이 필요하다고 판단되면, 로컬에서 수정한 뒤 다시 GitHub에 push하고 Colab에서 pull합니다.
- Phase 1에서는 브랜치를 늘리지 않고 `main` 중심으로 운영할 수 있습니다.


## 단계별 계획

| Phase | 범위 | 도구 | 목표 |
| --- | --- | --- | --- |
| Phase 1 | df003 완료 + ps_ce002 확장 | Codex + Python CLI + CSV/Excel | item/polyset 자동화 경로 검증 |
| Phase 2 | 10개 항목 | Python package/CLI + CSV/Sheets | 반복 구조 안정화 |
| Phase 3 | 50개 항목 | Prefect/Label Studio 선택 도입 | 상태 관리와 검수량 처리 |
| Phase 4 | 300개 항목 | DVC/MLflow 선택 도입 | 데이터/실험 버전관리 |

Phase 1에서는 무거운 도구를 도입하지 않습니다.


## 문법항목 ID 네이밍 규칙

2026-04-30 이후 새로 부여하는 문법항목 고유 ID는 아래 접두어 체계를 따릅니다.

| 문법항목 유형 | ID 형식 | 예시 |
| --- | --- | --- |
| 조사 | `pt###` | `pt001` |
| 연결어미 | `ce###` | `ce001` |
| 종결어미 | `fe###` | `fe001` |
| 의존어 구성(연결표현) | `dc###` | `dc001` |
| 의존어 구성(종결표현) | `df###` | `df001` |
| 선어말어미 | `pf###` | `pf001` |
| 관형사형어미 | `ae###` | `ae001` |

원칙:

- `###`은 유형별 3자리 순번입니다.
- 새 문법항목을 추가할 때는 반드시 이 표의 접두어 중 하나를 사용합니다.
- 기존 프로젝트에서 가져온 항목도 새 네이밍 규칙에 맞게 migration한 뒤 사용합니다.
- 현재 Phase 1 pilot의 `df003`은 의존어 구성(종결표현) 유형의 pilot ID입니다.

## Pilot 및 현재 task unit

| 필드 | 값 |
| --- | --- |
| completed item_id | df003 |
| name | `ㄴ/은 적 있/없` |
| meaning | 경험 유무 서술 |
| status | 정규식, bridge/component span, corpus review, encoder example export 경로 검증 완료 |
| current task_unit_id | ps_ce002 |
| current task name | `ㄴ/은/는데` polyset task (`ce002`, `ce003`) |
| current goal | ps_id 기반 dict/gold skeleton에서 bundle, gold recall, corpus review, encoder export까지 반복 자동화하기 |

포함 예시는 다음과 같습니다.

```text
가 본 적이 있다
먹어 본 적이 있어요
만난 적이 있었어요
들어 본 적 있니?
해 본 적은 없어요
경험한 적 없는
```

제외 예시는 다음과 같습니다.

```text
적이 많다
일반적이지 않은 관점이다
적을 만들다
옛적
적어도
적다
그 사람은 내 적이다
```

## 사람과 자동화의 역할

| 영역 | 사람 | 자동화/Codex/Python |
| --- | --- | --- |
| 문법항목 정의 | 의미, 포함/제외 기준 확정 | schema에 맞게 저장 |
| 정규식 골드 | 50개 positive gold 작성 | 형식 검증 |
| 정규식 생성 | 최종 승인 | 초안 생성, gold test, FN 분석, 수정안 제안 |
| corpus search | 말뭉치 선택 | DetectorEngine 기반 후보 검색, span 추출, 중복 제거 |
| TP/FP 검수 | 최종 라벨 확정 | 검수표 생성, 임시 판단 보조 |
| dataset export | 품질 확인 | positive/negative JSONL 생성 |

## 검색용 정규식 및 예문 구축 루프

Phase 1 pilot부터 아래 반자동 루프를 기준으로 합니다. df003처럼 단일 `e_id` item도, ps_ce002처럼 여러 teaching item을 묶는 `ps_id` polyset task도 같은 루프를 사용합니다.

초기 입력:

```text
datasets/dict/dict_{unit_id}.xlsx 또는 dict_ps_??.xlsx
datasets/gold/gold_{unit_id}.xlsx 또는 gold_ps_??.xlsx
```

원칙:

- 사용자가 제공하는 dict/gold Excel은 skeleton 상태일 수 있습니다.
- skeleton dict에서 `polysets.detect_ruleset_id`, `detect_rules` 행, gap/verify rule이 비어 있을 수 있습니다.
- Codex/자동화는 먼저 working dict Excel을 채우고, bundle은 항상 그 Excel에서 재생성합니다.
- detector bundle을 직접 수정한 뒤 Excel로 되돌리는 방식은 사용하지 않습니다.

### 1. 검색용 정규식 완성

목표는 precision을 가능한 한 높이면서, 사람이 만든 정규식 gold 50개 기준 recall=1인 검색용 정규식을 만드는 것입니다.

절차:

1. skeleton dict에 필요한 최소 detect 연결을 채웁니다.
   - polyset이면 `polysets.detect_ruleset_id`를 생성합니다.
   - `detect_rules`에 1차 detect rule을 추가합니다.
   - `verify_ruleset_id`, verify rule, component gap은 필요할 때만 채웁니다.
2. gold Excel을 `exported_gold/{unit_id}_gold_50.jsonl`로 변환합니다.
3. dict Excel에서 detector bundle을 생성합니다.
4. gold 50 recall을 계산합니다.
5. FN이 있으면 FN 원인을 분석하고 detect rule을 수정합니다.
6. gold recall=1이 될 때까지 반복합니다.

주의:

- gold recall=1은 전체 한국어에서의 절대 recall=1이 아니라, 사람이 만든 정규식 gold 50개 기준의 recall=1입니다.
- gold recall=1이 되기 전에는 corpus search 단계로 넘어가지 않습니다.
- 정규식 초안과 수정 이력은 가능하면 `regex/{unit_id}_versions.jsonl`에 남깁니다.

브릿지 원칙:

- 브릿지는 문법항목별 정규식에 복붙하지 않고 `rule_components.bridge_id`와 공용 bridge registry로 연결합니다.
- 브릿지/component span 조립은 detect regex hit 주변의 제한된 window에서만 수행합니다.
- 브릿지가 gold recall=1을 유지하고 span 경계 또는 corpus FP 분석에 실제 도움이 되면 채택합니다.
- 효과가 작고 복잡도만 늘면 보류하거나 historical note로 남깁니다.
- 브릿지 추가 여부는 dict Excel의 `rule_components.bridge_id`, detector bundle report, 관련 decision에 기록합니다.

### 2. 말뭉치 기반 FP 감소 및 학습 예문 후보 구축

gold recall=1을 만족한 정규식은 일반 말뭉치에서 실제 hit 후보를 검색하는 데 사용합니다.

절차:

1. 검색용 정규식으로 공통 prepared corpus batch를 검색하여 hit 후보를 수집합니다. batch_002부터 예문 구축 batch는 일상대화 5,000행, 뉴스 700행, 비출판물 2,000행, 학습자 말뭉치 2,500행으로 구성합니다. batch_000/001은 이전 비율인 일상대화 5,000행, 뉴스 2,000행, 비출판물 2,000행, 학습자 말뭉치 1,000행으로 생성된 산출물입니다.
2. hit 후보를 사람이 TP/FP로 검수합니다. LLM은 임시 판단과 이유를 제공할 수 있지만 최종 라벨이 아닙니다.
3. 검수된 FP 유형을 근거로, gold recall=1을 유지하는 조건에서 정규식을 수정하여 FP를 줄입니다.
4. 더 이상 안전하게 FP를 줄이기 어렵다고 판단되면 해당 정규식을 검색용 정규식 후보로 확정합니다.
5. 확정된 검색용 정규식으로 다음 prepared corpus batch를 추가 검색합니다.
6. 사람이 TP/FP/span을 검수하여 positive/negative 예문을 각각 100개 모을 때까지 반복합니다.

문법항목별 기본 수집 정책:

- `target_pos=100`
- `target_neg=100`
- `max_processed_batches=3`

CLI 호환성:

- `summarize_review.py`의 CLI 인자는 기존 명령과 Colab 실행 호환을 위해 `--max-batches`를 유지합니다.
- 단, 이 값의 의미는 “검색한 batch 수”가 아니라 “사람 labeled review가 완료되어 summary에 반영된 processed batch 수”입니다.
- summary JSON의 기준 key는 `collection_policy.max_processed_batches`입니다.

수집 중단 기준:

- TP와 FP가 모두 목표 개수 이상이면 수집을 중단하고 encoder example export로 이동합니다.
- 최대 3개 processed labeled batch를 처리했는데도 한쪽이 부족하면 무한히 batch를 추가하지 않고, 현재 확보량으로 encoder 필요성 또는 추가 전략을 재판단합니다.
- `processed_batches`는 생성된 batch 수가 아니라, 실제 labeled review 입력으로 집계에 들어간 batch 수입니다. 예를 들어 batch_001 labeled 파일이 없고 batch_000과 batch_002만 사용하면 `processed_batches=2`입니다.

규칙 다듬기 중단/수정 기준:

- `FP/TP <= 2`이면 현재 규칙을 더 좁히지 않고 결과를 제출합니다.
- `FP/TP > 2`이고 `processed_batches < 3`이면 사람이 확정한 FP 중 systematic FP 유형이 있는지 검토합니다.
- systematic FP가 있더라도 정규식 또는 verify hard_fail로 안전하게 제거할 수 있고 gold recall=1을 유지할 가능성이 있을 때만 dict rule 수정을 시도합니다.
- `processed_batches >= 3`이면 FP/TP와 관계없이 batch 추가와 규칙 다듬기를 중단하고 현재 확보량으로 다음 판단을 합니다.
- `TP=0, FP>0`이면 `FP/TP=inf`로 보고 systematic FP 검토 대상입니다. `TP=0, FP=0`이면 비율을 계산하지 않고 추가 검색 또는 gold/rule 재검토가 필요합니다.
- `summarize_review.py`는 `rule_refinement_status.should_consider_rule_update`와 `reason`을 report에 남깁니다. 이 필드는 자동 수정 지시가 아니라 사람이 systematic FP 유형을 검토해야 하는지 알려주는 신호입니다.
- `rule_refinement_status`에는 별도 `next_action`을 두지 않습니다. top-level `next_action`과 `collection_status.next_action`은 예문 수집/encoder export 흐름 판단용으로 유지합니다.

원칙:

- 정규식을 수정할 때마다 반드시 gold recall test를 다시 실행합니다.
- gold recall이 1보다 낮아지는 수정은 검색용 정규식으로 확정하지 않습니다.
- 말뭉치 batch에서 나온 TP/FP는 후보이며, 최종 TP/FP와 span은 사람이 확정합니다.
- DetectorEngine은 가능한 경우 `component_spans`를 저장하고, component 조립 실패 시 `regex_match_fallback`으로 후보를 유지합니다.
- Kiwi 등 형태소 분석 기반 보정은 아직 도입하지 않았으며, 필요한 경우 후속 단계에서 비교합니다.
- 현재 단계에서는 인코더 fine-tuning을 수행하지 않고, positive/negative 예문 구축까지만 목표로 합니다.
- encoder example export 단계에서는 TP/FP downsampling을 적용하지 않습니다. 사람이 확정한 TP/FP pool은 있는 그대로 보존하고, class balancing은 실제 학습 결과를 본 뒤 loss weight, sampler, train subset 등의 방식으로 별도 판단합니다.

## 형태소 분석 및 브릿지 cache 설계 메모

기본 detector 경로는 Kiwi 같은 형태소 분석기를 호출하지 않는 문자 기반 `detect_rules` + `rule_components` + 공용 bridge 방식으로 둡니다. df003 pilot에서 `adnominal_n` bridge는 Kiwi 없이 gold 50개 기준 recall과 span exact를 만족했으므로, Phase 1과 초기 300개 규칙 구축에서는 Kiwi를 기본 경로에서 제외합니다.

형태소 분석은 문자 기반 bridge로 안정적인 span 조립이 어렵거나, 특정 문법항목에서 규칙만으로는 FP/FN을 줄이기 어려운 경우에만 예외적으로 검토합니다. 실시간 HanTalk에서는 형태소 분석을 문법항목마다 반복하면 응답 속도에 악영향을 줄 수 있으므로, 예외적으로 도입하더라도 문장 단위 1회 분석 후 필요한 규칙이 공유하는 cache 구조를 우선 검토합니다.

장기 검토 후보 구조:

```text
문장 입력
→ 형태소 분석 1회 수행
→ token/span/cache 생성
→ 필요한 규칙들이 분석 결과 공유
→ 후보만 인코더로 전달
```

원칙:

- 기본 runtime detector는 형태소 분석기를 호출하지 않습니다.
- Kiwi 등 형태소 분석 기반 처리는 정말 필요한 항목에서만 예외적으로 사용합니다.
- 예외 사용 여부는 gold recall, span 품질, 말뭉치 FP 감소량, 응답속도 영향을 비교한 뒤 결정합니다.
- 형태소 분석 결과는 가능하면 문장 단위로 한 번 만들고 재사용합니다.
- 모든 300개 규칙이 항상 같은 분석 결과를 공유해야 한다는 뜻은 아닙니다. 학습 단계, 난이도 단계, 목표 문법항목 범위에 따라 필요한 규칙만 공유할 수 있습니다.
- 예를 들어 초급 학습 모드에서는 300개 전체가 아니라 약 100개 안팎의 초급 관련 규칙만 분석 결과를 공유하여 속도를 줄일 수 있습니다.
- 형태소 분석기 후보는 Kiwi에 한정하지 않습니다. Kiwi의 상업 라이선스, 속도, 정확도, 배포 조건을 조사한 뒤 다른 형태소 분석기 사용 가능성도 비교합니다.
- 이 형태소 분석/cache 전략은 실시간 응답 속도에 직접 영향을 주므로, HanTalk 본 시스템 설계 단계에서 반드시 다시 검토합니다.

## 파일 구조

```text
.
├── AGENTS.md
├── PROJECT_SPEC.md
├── CURRENT_TASK.md
├── DECISIONS.md
├── configs/
│   └── corpus/
│       └── example_making_manifest.json
│   └── detector/
│       ├── detector_bundle.json
│       └── detector_bundle_ps_??.json
├── exported_gold/
├── regex/
├── hits/
├── labels/
├── datasets/
│   ├── dict/
│   │   ├── dict.xlsx
│   │   └── dict_ps_??.xlsx
│   └── gold/
│       ├── gold.xlsx
│       └── gold_ps_??.xlsx
├── logs/
└── src/
```

## 핵심 파일 인터페이스

| 파일/폴더 | 역할 | 만든 주체 | 읽는 주체 |
| --- | --- | --- | --- |
| `configs/grammar_items.yaml` | 초기 pilot 보조 config. 장기 SSOT는 아님 | 사람 + Codex | 필요 시 참고 |
| `configs/detector/detector_bundle.json` | 통합 dict Excel에서 생성한 runtime detector bundle | 자동화 | DetectorEngine |
| `configs/detector/detector_bundle_ps_??.json` | item/polyset skeleton dict에서 생성한 개발/검증용 detector bundle | 자동화 | DetectorEngine, gold test |
| `configs/corpus/example_making_manifest.json` | 예문 구축용 공통 말뭉치 batch 구성과 sampling 크기 | 사람 + Codex | `prepare_example_corpus.py` |
| `datasets/gold/gold.xlsx` | 장기 aggregate 정규식 gold 원본 관리 파일 | 사람 | gold export/validation CLI |
| `datasets/gold/gold_ps_??.xlsx` | item/polyset 자동화 시작용 정규식 gold skeleton | 사람 | `export_gold.py` |
| `datasets/dict/dict.xlsx` | 장기 aggregate dict Excel | 사람 | `export_bundle.py` |
| `datasets/dict/dict_ps_??.xlsx` | item/polyset 자동화 시작용 dict skeleton 또는 working dict | 사람 + Codex | `export_bundle.py` |
| `exported_gold/{unit_id}_gold_50.jsonl` | gold Excel에서 자동 생성한 unit별 정규식 gold positive 50개 | 자동화 | gold test CLI |
| `regex/df003_versions.jsonl` | 정규식 버전과 성능 로그 | 자동화 | regex iteration/report CLI |
| `HanTalk_work/corpus/example_making/prepared/example_making_batch_###.jsonl` | 여러 말뭉치에서 stable hash sampling으로 만든 공통 검색 batch | 자동화 | `search_corpus.py` |
| `HanTalk_arti/example_making/{unit_id}/{unit_id}_batch_###_detection.jsonl` | DetectorEngine 검색 결과 원본 | 자동화 | 사람 + 검수/분석 CLI |
| `HanTalk_arti/example_making/{unit_id}/{unit_id}_batch_###_human_review.csv` | 사람 검수용 후보 표 | 자동화 | 사람 검수 |
| `HanTalk_arti/example_making/{item_id}/{item_id}_batch_###_codex_review.csv` | Codex 1차 검토용 후보 표. 자동 TP/FP 판정은 포함하지 않음 | 자동화 | Codex 1차 검토 + 사람 최종 검수 |
| `HanTalk_arti/example_making/{item_id}/{item_id}_batch_###_codex_review.xlsx` | Codex 1차 검토용 Excel 사본 | 자동화 | Codex 1차 검토 + 사람 최종 검수 |
| `HanTalk_arti/example_making/{item_id}/{item_id}_batch_###_codex_review_report.json` | Codex 검토 파일 준비 상태와 span parse report | 자동화 | 사람 + Codex |
| `HanTalk_arti/example_making/{item_id}/{item_id}_batch_###_human_review_labeled.xlsx` | 사람이 확정한 TP/FP/span 검수 완료본 | 사람 | `summarize_review.py`, dataset export CLI |
| `HanTalk_arti/example_making/{item_id}/{item_id}_batch_###_human_review_labeled.csv` | 사람이 확정한 TP/FP/span 검수 완료본의 CSV 사본 | 사람 또는 자동 변환 | `summarize_review.py`, dataset export CLI |
| `HanTalk_arti/example_making/{item_id}/{item_id}_review_summary.json` | labeled review 파일 누적 집계와 목표 달성 여부 | 자동화 | 사람 + 다음 batch 판단 |
| `HanTalk_arti/example_making/{item_id}/{item_id}_encoder_examples.xlsx` | 인코더 학습 예문 사람이 확인하는 gold-like Excel 사본 | 자동화 | 사람 확인 |
| `HanTalk_arti/example_making/{item_id}/{item_id}_encoder_pair_examples.jsonl` | 인코더 pair-mode 학습용 기계친화 예문 SSOT | 자동화 | 향후 `train_encoder_pair.py` |
| `HanTalk_arti/example_making/{item_id}/{item_id}_encoder_examples_summary.json` | 인코더 예문 export 요약, split/role 분포, 목표 달성 여부 | 자동화 | 사람 + 학습 실행 판단 |
| `HanTalk_arti/example_making/all/all_encoder_pair_examples.jsonl` | item별 encoder pair JSONL을 병합해 자동 생성하는 전체 aggregate. SSOT가 아님 | 자동화 | 향후 전체 학습/검증 |
| `HanTalk_arti/example_making/all/all_encoder_examples.xlsx` | 전체 encoder 예문을 사람이 확인하는 ledger. 수동 append 금지 | 자동화 | 사람 확인 |
| `HanTalk_arti/example_making/all/all_encoder_examples_summary.json` | 전체 aggregate의 item/label/split/role 분포와 source policy | 자동화 | 사람 + 학습 실행 판단 |
| `logs/df003_regex_iterations.jsonl` | FN 분석과 수정 이력 | 자동화 | 사람 + Codex |


## gold Excel 설계 원칙

사람이 관리하는 정규식 gold 원본은 Excel입니다. 장기적으로는 `datasets/gold/gold.xlsx` 같은 aggregate 파일로 모을 수 있지만, 현재 반복 자동화에서는 사용자가 `datasets/gold/gold_ps_??.xlsx` 같은 item/polyset-specific skeleton Excel을 제공할 수 있습니다.

원칙:

- gold Excel은 사람이 직접 관리하는 원본입니다.
- `exported_gold/{unit_id}_gold_50.jsonl`은 gold Excel에서 자동 생성되는 검증용 산출물입니다.
- unit별 JSONL은 사람이 직접 편집하는 원본이 아니라, 정규식 테스트 CLI와 자동화가 빠르게 읽기 위한 파일입니다.
- gold 파일은 사용자 실시간 대화 응답 경로에서 사용하지 않습니다. 따라서 unit별 JSONL은 앱 응답속도 목적이 아니라 개발/검증 속도와 재현성을 위한 산출물입니다.
- 장기 aggregate `gold.xlsx`를 만들 때도 item/polyset-specific skeleton에서 검증된 내용을 흡수하는 방식으로 관리합니다.

## dict Excel 설계 원칙

사람이 관리하는 문법항목 사전 원본은 Excel입니다. 장기적으로는 통합 `dict.xlsx`를 둘 수 있지만, 현재 반복 자동화에서는 `datasets/dict/dict_ps_??.xlsx` 같은 item/polyset-specific skeleton 또는 working dict를 사용할 수 있습니다. `configs/grammar_items.yaml`은 필요하면 dict Excel에서 생성되는 기계 친화적 산출물로 둡니다.

dict Excel의 기본 시트는 단일 item과 polyset task에 따라 아래를 사용합니다.

```text
items
rule_components
detect_rules
polysets   # ps_id 기반 polyset task가 있을 때 사용
```

`items` 시트에는 `group` 열을 둡니다. `group`은 문법항목별 후처리 필요 수준을 나타냅니다.

| group | 의미 | 기본 처리 |
| --- | --- | --- |
| `a` | 오탐제거가 필요 없는 문법항목 | 규칙 검색 결과를 그대로 사용할 수 있음 |
| `b` | 오탐제거가 필요하지만 다의의미 분별이 필요 없는 문법항목 | 규칙 검색 후 오탐 필터링만 수행 |
| `c` | 오탐제거 및 다의의미 분별이 필요한 문법항목 | 사용자 발화 기본 판정에서는 다의의미 분별을 하지 않고, 문법항목 제안/오류 수정 패널에서만 다의의미 분별을 고려 |

운영 원칙:

- 한톡 프로젝트는 사용자의 실시간 발화 분석에서 기본적으로 다의의미 분별을 수행하지 않습니다.
- `group=c`는 실시간 사용자 발화 확정 판정을 위한 구분이 아니라, 문법항목 사용 제안이나 발화 오류 수정 제안에서 다의의미 분별이 필요한 항목을 표시하기 위한 구분입니다.
- `group=b`와 `group=c`는 모두 오탐제거가 필요하지만, `group=c`는 교육적 제안 단계에서 의미 구분이 추가로 필요합니다.

`detect_rules` 시트는 후보 생성과 hard_fail 검증에 사용하는 표면 정규식 규칙을 담습니다. 따라서 사람이 관리하는 Excel에서는 아래 열을 두지 않습니다.

```text
comp_id
scope
rule_type
engine
confidence_delta
```

내부 로더는 `detect_rules`를 읽을 때 아래 값을 자동으로 보충합니다.

```text
rule_type = surface_regex
engine = re
```

`detect_rules` 실행 원칙:

- 한 행은 하나의 규칙입니다.
- 규칙은 `stage` 순서대로 실행합니다: `detect` → `verify`.
- `stage=detect`는 후보 생성을 담당합니다. 후보 생성은 recall을 우선하여 넓게 수행합니다.
- `stage=verify`는 후보를 새로 만들지 않고, 이미 생성된 후보를 제거하는 hard_fail 용도로만 사용합니다.
- `verify` 규칙은 100% 확실한 오탐일 때만 hard_fail을 발생시킵니다.
- `stage=detect`인 규칙의 `target`은 항상 `raw_sentence`여야 합니다.
- `stage=verify`인 규칙의 `target`은 `raw_sentence`, `char_window`, `component_right_context`를 허용합니다.
- `target=component_right_context`는 candidate 안의 특정 component span 바로 오른쪽 문자열만 검증합니다. 이 target을 쓰는 rule은 `component_id`를 반드시 지정해야 합니다.
- `component_right_context`에서 해당 `component_id`의 span을 찾지 못하면, recall 보호를 위해 그 verify rule은 적용하지 않고 candidate를 유지합니다.
- 이전 프로젝트 코드의 `token_window`는 실제로 토큰 단위가 아니라 문자 단위 후보 주변 window이므로, 새 규칙 모듈을 만들 때 `char_window`로 이름을 바꿉니다.
- 같은 `stage` 안에서는 `priority`가 작은 규칙부터 실행합니다.
- `priority`의 숫자가 작을수록 더 강한 우선순위를 가집니다.

주의:

- `detect_rules.comp_id`는 사용하지 않습니다.
- `detect_rules.scope`는 사용하지 않습니다. 이전 프로젝트의 `scope`는 실버 라벨 구축용 규칙과 추론용 규칙을 분리하기 위한 열이었으나, HanTalk 프로젝트에서는 실버 라벨을 만들지 않습니다.
- `detect_rules.confidence_delta`는 사용하지 않습니다. 새 규칙 모듈에서 `verify`는 점수 조정이 아니라 hard_fail 전용으로 사용합니다.
- `rule_components.comp_id`는 component span 탐색과 디버깅에 필요하므로 유지합니다.
- Phase 1에서는 context rule을 사용하지 않습니다.

## Detector runtime 구현 원칙

사람이 관리하는 문법항목 사전의 SSOT는 dict Excel입니다. 단, runtime detector는 Excel을 직접 읽지 않습니다. 통합 `dict.xlsx` 또는 item/polyset-specific `dict_ps_??.xlsx`는 아래 명령으로 runtime bundle로 export합니다.

```bash
python3 -m src.detector.export_bundle \
  --dict datasets/dict/dict.xlsx \
  --out configs/detector/detector_bundle.json
```

개별 polyset task 개발 중에는 main bundle을 덮어쓰지 않기 위해 별도 bundle을 생성합니다.

```bash
python3 -m src.detector.export_bundle \
  --dict datasets/dict/dict_ps_ce002.xlsx \
  --out configs/detector/detector_bundle_ps_ce002.json
```

runtime detector는 `configs/detector/detector_bundle.json`을 읽고, 정규식을 초기화 시점에 compile/cache하여 사용합니다. 사용자 발화 detect 경로에서 Excel parsing을 반복하지 않는 것이 원칙입니다.

DetectorEngine 현재 구현 범위:

- `detector_bundle.json` 로딩
- `active_unit_ids` 기준 runtime unit 선택
- `stage=detect`, `target=raw_sentence` 표면 정규식 실행
- detect regex match 이후 `rule_components` 기반 component span 조립
- `stage=verify`, `target=raw_sentence`, `target=char_window`, `target=component_right_context` hard_fail 최소 구현
- candidate span을 `span_segments`로 출력

DetectorEngine 실행 안전장치:

- Phase 1에서는 `active_unit_ids`를 반드시 명시합니다.
- DetectorEngine 실행 정책은 크게 `offline`과 `realtime` 두 가지로만 구분합니다.
- `offline`은 기본값이며 gold 평가, corpus search, audit, 예문 구축에 사용합니다.
- `realtime`은 실제 사용자 발화 처리에 사용하며, `regex_match_fallback` 후보와 rejected/partial/debug 보조 정보를 최종 출력에서 숨깁니다.
- 전체 runtime unit 실행은 `allow_all=True`를 명시한 경우에만 허용합니다.
- polyset task unit은 기본적으로 자동 실행하지 않으며, `active_unit_ids`에 ps_id를 명시하고 `allow_polyset=True`를 넘긴 경우에만 실행합니다.
- 기존 실험용 옵션 `allow_experimental_polyset=True`는 호환용으로 남기되, ce002/ce003부터의 공식 경로는 `allow_polyset=True`입니다.
- rule 하나에서 match가 폭주하지 않도록 `max_matches_per_rule` 제한을 둡니다. 기본값은 50입니다.
- component 후보가 폭주하지 않도록 `max_candidates_per_component` 제한을 둡니다. 기본값은 20입니다.
- component 후보 조합 경로가 폭주하지 않도록 `max_component_paths` 제한을 둡니다. 기본값은 2000입니다.
- component span 조립은 문장 전체가 아니라 detect regex match 주변 `component_window_chars` 안에서만 수행합니다. 기본값은 좌우 각각 20자입니다.
- component/bridge 상세 debug는 기본 출력하지 않고 `include_debug=True`일 때만 포함합니다.
- 제한에 걸리면 detector result summary의 `n_matches_truncated`, `truncated_rules`에 기록합니다.
- detector result summary에는 component span 상태를 빠르게 확인할 수 있도록 `n_component_span_success`, `n_component_span_fallback`, `n_component_span_regex_only`, `span_source_counts`를 기록합니다.

## group=c polyset 2-ID 체계

ce002/ce003처럼 표면형은 같고 교수 의미가 나뉘는 group=c 항목은 아래 2-ID 체계로 운영합니다.

| 층위 | ID | 역할 |
| --- | --- | --- |
| teaching item | `e_id` (`ce002`, `ce003`) | 사람이 가르치는 문법항목 의미와 gloss를 보존 |
| task unit | `ps_id` (`ps_ce002`) | 정규식 detect, corpus search, human review, binary encoder 오탐 필터링 단위 |

원칙:

- HanTalk의 현재 사용자 발화 기본 판정은 다의의미 분별이 아니라 오탐 제거입니다.
- `ps_id`는 detect_unit_id이자 encoder_task_id입니다.
- `e_id`는 teaching_item_id이며, 교수 메시지와 의미별 gloss를 위한 metadata입니다.
- `primary_e_id`는 의미 대표가 아니라 stable ID anchor입니다.
- `polysets.note`는 사람이 보는 관리 메모이며 encoder 입력에는 사용하지 않습니다.
- binary encoder의 `text_b`는 polyset canonical form과 polyset encoder gloss를 사용합니다.

`dict_ps_ce002.xlsx`의 `polysets` 최소 schema:

```text
ps_id
primary_e_id
member_e_ids
ps_canonical_form
disconti_allowed
ps_comp_id
gloss_intro
detect_ruleset_id
verify_ruleset_id
note
```

`ps_ce002`의 encoder `text_b`는 아래 방식으로 생성합니다.

```text
{ps_canonical_form}
{gloss_intro} {member_e_id 순서의 items.gloss를 ; 로 연결}
```

예:

```text
ㄴ/은/는데
다음 의미를 포함하는 연결어미: 앞절의 상황·배경을 제시하고 뒤절로 이어지게 하는 연결어미; 앞절과 뒤절이 대조·대립 혹은 양보적 전환, 반전되는 관계로 이어질 때 쓰는 연결어미
```

DetectorEngine span 정책:

- `span_segments`는 detector output의 canonical span 표현입니다.
- span은 Python 0-based `[start, end)` 규칙을 따릅니다.
- 불연속 표현은 여러 segment로 보존합니다.
- candidate에는 원래 detect regex가 잡은 `regex_match_span`, `regex_match_text`를 보존합니다.
- component span 조립이 성공하면 `span_source=component_spans`, `component_span_enabled=true`로 기록합니다.
- component span 조립이 실패하면 후보를 버리지 않고 `span_source=regex_match_fallback`으로 유지합니다. 이는 gold recall 보호를 위한 fallback입니다.
- component 일부만 찾은 경우에는 `partial_component_spans`, `partial_span_segments`, `partial_span_text`, `matched_component_ids`, `missing_required_component_ids`를 보조 정보로 기록할 수 있습니다.
- partial component span은 검수, 오류 분석, component 단위 verify rule에 쓰는 보조 정보이며 canonical span으로 승격하지 않습니다.
- 따라서 full component path가 성공한 경우에만 `span_source=component_spans`이고, 실패한 경우의 canonical `span_segments`는 계속 regex fallback span입니다.
- `origin_e_id`는 component lookup 기준입니다. group=c polyset 확장 시 `unit_id`와 `origin_e_id`가 달라질 수 있으므로 지금부터 보존합니다.

Component bridge 원칙:

- 여러 문법항목이 공유하는 브릿지는 문법항목별 정규식에 복붙하지 않고 공용 registry에서 관리합니다.
- `rule_components.bridge_id`는 optional 열입니다. 없으면 일반 surface component만 사용합니다.
- `bridge_id`가 있으면 `src/detector/bridges.py`의 공용 matcher를 사용합니다.
- 알 수 없는 `bridge_id`는 bundle export fatal error입니다.
- bridge는 기본적으로 Kiwi 없이 문자 기반으로 구현합니다. 형태소 분석이 필요한 bridge는 예외로 분리하고, 응답속도 영향을 비교한 뒤 채택합니다.
- 현재 구현된 bridge는 `adnominal_n`, `nde`, `thing`입니다.
- `adnominal_n`은 `본`, `간`, `한`처럼 종성 ㄴ을 가진 음절과 명시적 `은`/`ㄴ`을 가볍게 찾습니다.
- `nde`는 `는데`, `은데`, `은 데`, `는 데`, `한데`처럼 `ㄴ/은/는데` 연결어미 component를 문자 기반으로 찾습니다.
- `thing`은 향후 `것`, `거`, `게`, `건`, `걸`류 의존명사 구성 요소를 찾는 데 사용합니다.
- 브릿지는 candidate를 직접 만들지 않고 component 후보 span만 반환합니다.
- `src/detector/component_locator.py`가 `rule_components`와 bridge 후보를 조합하여 최종 component span을 만듭니다.

Component order 정책:

- `rule_components.comp_order`는 component span 조립의 기본 순서입니다.
- `rule_components.order_policy=fx`이면 `comp_order` 순서를 반드시 지킵니다. 기본값도 `fx`입니다.
- `rule_components.order_policy=fl`이면 기본 `comp_order`를 우선하되, 인접한 `fl` component끼리만 1회 adjacent swap을 허용합니다.
- `fx` component는 움직이지 않으며, `fl` component라도 anchor component는 움직이지 않습니다.
- anchor component는 `anchor_rank`가 가장 큰 required component로 봅니다.
- 모든 component 탐색은 detect regex match 주변 `component_window_chars` 안에서만 수행하고, `max_candidates_per_component`, `max_component_paths` 제한을 적용합니다.

DetectorEngine output에는 아래 필드를 넣지 않습니다.

```text
aliases
route
relation_type
span_start
span_end
```

이유:

- `aliases`는 사람이 이해하기 위한 사전 정보이지 detector 후보 출력에는 중복입니다.
- `route`, `relation_type`은 Phase 1 실시간/예문 구축 경로에 필요하지 않으며 응답속도와 복잡도를 늘릴 수 있습니다.
- span은 불연속 표현을 지원해야 하므로 단일 `span_start`, `span_end` 대신 `span_segments`를 사용합니다.

`char_window`의 `window_chars`는 후보 span envelope 기준 좌우 각각 N자를 뜻합니다.

`component_right_context`의 `window_chars`는 지정한 component span 끝 위치 기준 오른쪽 N자를 뜻합니다. 예를 들어 df003의 `component_id=c2`는 실제 선택된 `적` component를 가리키며, `pattern=^\s*(?:으로|인|일|에)`는 그 `적` 바로 뒤가 `으로`, `인`, `일`, `에`일 때만 hard fail을 발생시킵니다. 이 target은 먼저 full `component_spans[component_id]`를 보고, 없으면 보조 정보인 `partial_component_spans[component_id]`를 봅니다. 둘 다 없으면 recall 보호를 위해 해당 verify rule을 skip합니다.

`export_bundle.py` validation 원칙:

- regex compile 실패는 fatal error입니다.
- 필수 sheet/column 누락, 중복 ID, 잘못된 group/stage/target도 fatal error입니다.
- `detect_rules`와 `rule_components`의 task unit은 `unit_id` → `ps_id` → `e_id` 순서로 해석합니다.
- `e_id` 기반 rule/component는 반드시 `items.e_id`에 존재해야 합니다.
- `ps_id` 기반 rule/component는 반드시 `polysets.ps_id`에 존재해야 합니다.
- item/polyset이 참조한 `detect_ruleset_id`와 `verify_ruleset_id` 안의 rule은 같은 task unit에 속해야 합니다.
- `items.detect_ruleset_id`는 detect rule을 1개 이상 포함해야 합니다.
- `items.verify_ruleset_id`가 있으면 verify rule을 1개 이상 포함해야 합니다.
- 같은 `ruleset_id` 안에 detect/verify stage가 섞이면 fatal error입니다.
- Excel header row 중간에 빈 header가 있으면 값과 header가 어긋날 수 있으므로 fatal error입니다.
- pattern이 `r"..."` 같은 Python literal처럼 보이는 경우, group=c인데 `ps_id` 또는 legacy `polyset_id`가 없는 경우, verify rule인데 hard_fail=false인 경우는 warning입니다.

## 예문 구축용 prepared corpus batch

예문 구축용 말뭉치 batch는 item별로 따로 만들지 않고 공통 prepared corpus로 만듭니다. 같은 batch를 여러 문법항목에 반복 적용해야 300개 문법항목의 hit 수, FP 유형, span 품질을 같은 입력 집합 위에서 비교할 수 있습니다.

현재 manifest 파일:

```text
configs/corpus/example_making_manifest.json
```

현재 정규식 다듬기 및 예문 제작용 통합 말뭉치 폴더는 아래 Git 제외 경로입니다.

```text
/Users/yonghyunnam/coding/HanTalk_group/HanTalk_work/corpus/example_making
```

현재 `example_making_manifest.json`이 참조하는 통합 입력 파일은 아래 네 개입니다.

| corpus_domain | 파일명 |
| --- | --- |
| `daily_conversation` | `일상대화말뭉치(2023_2024).txt` |
| `news` | `신문말뭉치(2024).txt` |
| `non_published` | `비출판물말뭉치.txt` |
| `learner_spoken_5_6` | `학습자말뭉치(구어_5_6급).txt` |

`신문말뭉치(2024).txt`는 작업 속도를 위해 2024년 신문 JSON 5개 파일만 사용해 다시 생성한 축소 통합 파일입니다. 생성 원본 폴더와 확인용 산출물은 아래와 같습니다.

```text
/Users/yonghyunnam/coding/HanTalk_group/HanTalk_work/corpus/example_making/news_paper(2024)
/Users/yonghyunnam/coding/HanTalk_group/HanTalk_work/corpus/example_making/news_paper(2024)/news_paper_2024_form_source.txt
```

축소 통합 파일은 `form;source` 형식이며, header 제외 1,215,885행입니다.

현재 batch 구성(batch_002 이후):

| corpus_domain | sample size |
| --- | ---: |
| `daily_conversation` | 5,000 |
| `news` | 700 |
| `non_published` | 2,000 |
| `learner_spoken_5_6` | 2,500 |

이 비율은 문장 수 기준 sampling에서 실제 문장량이 과도하게 흔들리는 것을 줄이기 위한 조정입니다. 뉴스 말뭉치 문장은 다른 말뭉치 문장보다 대체로 2~3배 길고, 학습자 말뭉치 문장은 짧아서 문장 수를 단순히 `5:2:2:1`로 두면 실제 텍스트량과 학습자 발화 비중이 의도와 다르게 나올 수 있습니다.

원칙:

- manifest에는 절대경로를 넣지 않습니다.
- 실제 말뭉치 폴더는 CLI의 `--corpus-root`로 전달합니다.
- `example_making_manifest.json`은 `sampling_schedules`를 지원합니다. batch_000/001은 초기 비율로 재생성 가능하게 보존하고, batch_002 이후는 조정된 비율로 생성합니다.
- 입력 통합 파일은 `text;source` 계열 형식으로 읽습니다. header가 있으면 `sentence`, `form`, `text`, `raw_text`를 text column 후보로, `source`를 source column 후보로 봅니다.
- header가 예상과 다르면 첫 번째 열을 text, 마지막 열을 source로 해석합니다.
- 데이터 line은 문장 안의 세미콜론을 보호하기 위해 마지막 delimiter 기준으로 `rsplit(delimiter, 1)` 방식으로 분리합니다.
- 대용량 말뭉치를 메모리에 모두 올리지 않고, stable hash streaming sampling으로 domain별 batch를 구성합니다.
- 같은 `seed`, `batch_index`, 입력 파일이면 prepared JSONL은 재현 가능해야 합니다.
- 기본 동작에서 `batch_index=k`는 domain별 hash 순서에서 `kN`부터 `(k+1)N` 구간을 선택합니다. 단, `sampling_schedules`에 `rank_start_offsets`가 있으면 이전 비율로 이미 사용한 hash rank를 건너뛰고 새 비율 batch를 이어서 선택합니다.

생성 명령 예:

```bash
python3 -m src.prepare_example_corpus \
  --manifest configs/corpus/example_making_manifest.json \
  --corpus-root /Users/yonghyunnam/coding/HanTalk_group/HanTalk_work/corpus/example_making \
  --batch-index 0 \
  --out /Users/yonghyunnam/coding/HanTalk_group/HanTalk_work/corpus/example_making/prepared/example_making_batch_000.jsonl \
  --report /Users/yonghyunnam/coding/HanTalk_group/HanTalk_work/corpus/example_making/prepared/example_making_batch_000_report.json
```

prepared JSONL 한 줄은 아래 필드를 포함합니다.

```json
{"text_id":"daily_conversation_b000_000001","batch_id":"example_making_batch_000","batch_index":0,"corpus_domain":"daily_conversation","source":"일상대화말뭉치(2024년)","source_file":"일상대화말뭉치(2023_2024).txt","source_row_index":0,"source_line_no":2,"sample_hash":"...","raw_text":"..."}
```

## Corpus search output

`src/search_corpus.py`는 prepared corpus JSONL을 읽고, 정규식을 직접 실행하지 않고 반드시 `DetectorEngine`을 호출합니다.

실행 예:

```bash
python3 -m src.search_corpus \
  --bundle configs/detector/detector_bundle.json \
  --input-jsonl /Users/yonghyunnam/coding/HanTalk_group/HanTalk_work/corpus/example_making/prepared/example_making_batch_000.jsonl \
  --active-unit-id df003 \
  --artifact-root /Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making
```

원칙:

- `--active-unit-id`는 여러 번 줄 수 있습니다. Phase 1 실행은 우선 `df003` 하나로 합니다.
- `--artifact-root`를 주면 item별 산출물은 `HanTalk_arti/example_making/{item_id}/` 아래에 자동 저장됩니다.
- 예를 들어 위 명령은 `df003/df003_batch_000_detection.jsonl`, `df003/df003_batch_000_human_review.csv`, `df003/df003_batch_000_search_report.json`을 생성합니다.
- 여러 `--active-unit-id`를 한 번에 검색할 때는 item별 폴더를 자동으로 정할 수 없으므로 `--out-jsonl`, `--review-csv`, `--report-json`을 명시합니다.
- detection JSONL은 hit가 있는 문장만 저장합니다.
- human review CSV는 candidate 하나를 한 행으로 펼쳐 사람이 `human_label`, `span_status`, `corrected_span_segments`, `memo`, `reviewer`를 채울 수 있게 합니다.
- 검수 편의를 위해 `raw_text`, `regex_match_text`, `human_label` 열을 서로 붙여 배치합니다.
- LLM 검수 보조를 붙일 가능성에 대비해 `llm_temp_label`, `llm_note` 열을 비워 둡니다. 이 값은 최종 라벨이 아니라 임시 참고용입니다.
- human review CSV는 Excel에서 한국어가 깨지지 않도록 `utf-8-sig`로 저장합니다.
- review CSV는 `span_segments`, `span_key`, `span_text`, `span_source`, `component_span_status`, `applied_bridge_ids`, `detect_rule_ids`를 포함합니다.
- search report는 domain별 candidate 수, span source count, component span status count, 실행 시간을 기록합니다.

## Codex 1차 검토용 review 준비

`src/prepare_codex_review.py`는 `search_corpus.py`가 만든 `*_human_review.csv/xlsx`를 읽어 Codex 1차 검토용 `*_codex_review.csv`, `*_codex_review.xlsx`, `*_codex_review_report.json`을 생성합니다.

이 스크립트는 의미판정을 하지 않습니다.

원칙:

- 자동 TP/FP suggestion을 만들지 않습니다.
- `codex_review_label`, `codex_review_span_status`, `codex_review_reason`, `codex_review_note`, `codex_checked`는 Codex가 직접 1차 검토 후 채우는 참고 열입니다.
- `human_label`, `span_status`, `corrected_span_segments`, `corrected_span_text`는 사람이 최종 확정하는 열입니다.
- `summarize_review.py`와 `export_encoder_examples.py`는 Codex 검토 열이 아니라 사람이 확정한 `human_label`과 `span_status`만 최종 기준으로 사용합니다.
- `hit_id`, `raw_text`, `span_segments`는 필수 열입니다. `hit_id`가 비어 있거나 중복되면 이후 누적 집계와 encoder export 연결이 흔들리므로 오류로 처리합니다.

`prepare_codex_review.py`가 수행하는 기계적 검사는 아래로 제한합니다.

- `span_segments` parse 가능 여부 확인
- `[start,end)` 범위와 `raw_text` boundary 확인
- segment 오름차순과 overlap 여부 확인
- `span_extracted_text`, `span_parse_status`, `span_parse_note` 생성
- `span_source`, `component_span_status`, 기존 `human_label` blank count 등 준비 상태 report 생성

## Labeled review summary

사람 검수가 끝난 파일은 자동 생성 검수표와 구분하기 위해 `_labeled` suffix를 붙입니다.

예:

```text
/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003_batch_000_human_review_labeled.xlsx
/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003_batch_000_human_review_labeled.csv
```

신규 산출물은 item별 폴더를 기준으로 둡니다.

```text
/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003/df003_batch_000_human_review_labeled.xlsx
/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003/df003_batch_000_human_review_labeled.csv
```

`/Users/yonghyunnam/Downloads/for_codex2` 같은 전달용 폴더는 임시 확인 폴더로만 사용하고, 자동화의 기준 입력으로 삼지 않습니다. 기준 labeled 파일은 `HanTalk_arti/example_making/{item_id}` 아래에 둡니다.

다음 자동화 단계에서는 `src/summarize_review.py`를 만들어 labeled xlsx/csv 파일을 하나 이상 읽고 누적 집계를 생성합니다.

입력:

```text
--input .../{item_id}_batch_000_human_review_labeled.xlsx
--input .../{item_id}_batch_001_human_review_labeled.xlsx
```

출력:

```text
/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/{item_id}_review_summary.json
```

신규 summary 산출물은 아래 item별 폴더를 기준으로 합니다.

```text
/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/{item_id}/{item_id}_review_summary.json
```

`summarize_review.py`의 최소 집계 항목:

- 입력 파일 수와 총 후보 행 수
- `--item-id`와 row의 `origin_e_id` 또는 `unit_id` 일치 검증
- `human_label` 정규화 결과별 count: `tp`, `fp`, `unclear`, invalid/blank
- `span_status` 정규화 결과별 count
- `corpus_domain`별 TP/FP count
- `span_source`별 TP/FP count
- `component_span_status`별 TP/FP count
- `positive_100`, `negative_100` 달성 여부

주의:

- `human_label`이 최종 기준입니다. LLM 임시 라벨은 최종 라벨로 쓰지 않습니다.
- `origin_e_id` 또는 `unit_id`가 `--item-id`와 모두 다르면 잘못된 labeled 파일을 넣은 것으로 보고 error 처리합니다.
- `origin_e_id`와 `unit_id`가 둘 다 없으면 item 일치 검증을 건너뛰되 summary warning으로 남깁니다.
- FP 후보의 `span_status=ok`는 허용합니다. 현재 df003 batch_000 labeled 파일은 FP에도 검수자가 span 확인을 완료했다는 뜻으로 `ok`를 넣을 수 있습니다.
- positive 후보는 기본적으로 `human_label=tp`이고 `span_status=ok`인 행입니다.
- negative 후보는 기본적으로 `human_label=fp`인 행입니다. negative export 단계에서는 `span_status=ok`, `not_applicable`, 빈값 허용 여부를 별도로 정책화합니다.

## 향후 detector 설계 검토 메모

이 섹션은 SSOT가 아닙니다. 프로젝트 초반에는 파일 schema, detector 출력 형식, profile 방식이 바뀔 가능성이 크므로, 아래 내용은 확정 설계가 아니라 다음 구현 단계에서 반드시 다시 검토할 후보 목록으로 둡니다.

아래 3개는 구현 완료된 1차 기반입니다.

```text
src/detector/export_bundle.py
DetectorEngine 기반 구현
src/test_gold.py의 DetectorEngine 기반 리팩터링
```

component bridge 공용화와 df003 component span 조립도 Phase 1에서 구현되었습니다. ce002/ce003부터는 `ps_id` 기반 polyset task unit의 gold recall 평가 경로도 열었습니다. 아래 항목들은 아직 당장 구현하지 않고, 다음 단계에서 실행 가능성과 schema 안정성을 검토합니다.

- `group=c` 항목을 사용자 실시간 발화 detect에서 어느 profile 범위까지 `ps_id` 단위 runtime unit으로 켤지 정하는 구조.
- `group=c`의 특정 의미 판정은 실시간 detect에서 하지 않고, 교수용 패널이나 오류 수정 제안에서 `teaching_target_e_id`로 다루는 구조.
- `detect_profiles.xlsx` 또는 profile JSON으로 외부에서 detect할 항목 목록을 조절하는 구조.
- 사람이 관리하는 profile은 `e_id` 기준으로 두되, runtime에서는 `active_unit_ids`와 `teaching_target_e_ids`로 나누어 사용하는 구조.
- corpus search의 primary output을 CSV 하나가 아니라 detection JSONL과 사람 검수용 CSV로 나누는 구조.
- human review CSV와 encoder 후보 JSONL에 `unit_id`, `unit_type`, `member_e_ids`, `group`, `span_segments`, `span_key`, `span_text`, `detect_rule_ids`, `hard_fail_rule_ids`를 포함하는 구조.
- 새 문법항목이나 새 규칙을 추가할 때 기존 규칙과의 충돌, hit 수 폭증, 같은 span의 다중 unit 후보, 처리 시간 증가를 점검하는 offline `audit_rules.py`.
- `group=c` polyset runtime에서 member별 verify 규칙을 그대로 합치면 의미 구분용 verify가 잘못된 hard_fail을 만들 수 있으므로, 의미 중립 hard_fail만 적용하거나 polyset 공통 verify 규칙을 따로 두는 방안.

검토 기준:

- 실시간 사용자 발화 detect 경로에서는 응답속도를 우선합니다.
- 학습용 예문 구축 경로와 HanTalk 실시간 detect 경로가 서로 다른 detector 로직으로 갈라지지 않게 합니다.
- 다만 Phase 1에서는 과도한 일반화보다 df003 pilot이 실제로 끝까지 도는 것을 우선합니다.

## `configs/grammar_items.yaml` 보조 config 메모

`configs/grammar_items.yaml`은 Phase 1 초기에 만든 pilot 보조 config입니다. 현재 장기 SSOT는 사람이 관리하는 dict/gold Excel입니다. 통합 `dict.xlsx`/`gold.xlsx`와 item/polyset-specific `dict_ps_??.xlsx`/`gold_ps_??.xlsx`는 모두 Excel SSOT 계열이며, JSONL과 bundle은 자동 생성 산출물입니다.

원칙:

- 새 schema나 runtime 동작은 dict Excel → detector bundle 경로를 기준으로 구현합니다.
- `configs/grammar_items.yaml`은 필요할 때 사람이 읽는 보조 설명 또는 dict Excel에서 생성되는 산출물로만 둡니다.
- 문법항목 상태와 detect rule의 최신 여부는 dict Excel, `regex/{unit_id}_versions.jsonl`, `logs/` report를 기준으로 확인합니다.

## `exported_gold/df003_gold_50.jsonl` schema

각 줄은 하나의 JSON object입니다. df003 파일은 기존 `정규식 골드/정규식 골드_df003.xlsx`의 positive 정규식 gold 50개를 변환한 것입니다.

```json
{"item_id":"df003","example_id":"df003-GOLD-001","sentence":"대한상의는 보고서를 통해 ... 경험한 적 없는 저성장 ...","target_text":"한 적 없","target_spans":[{"start":32,"end":37,"text":"한 적 없"}],"source_e_id":"df003","source_example_id":"g0478","source":"신문말뭉치2024","split":"dev","pattern_type":"conti","gold_example_role":"pos_conti","note":"converted from df003 regex gold positive examples"}
```

필수 필드:

- `item_id`
- `example_id`
- `sentence`
- `target_text`
- `target_spans`
- `source_e_id`
- `source_example_id`
- `source`
- `pattern_type`
- `gold_example_role`

`target_spans`는 문자 단위 `[start, end)` 구간입니다. 불연속 표현은 여러 span object로 저장하고, `target_text`는 span text를 ` ... `로 연결합니다.

Detector output의 `span_text`도 같은 표기 원칙을 따릅니다. 불연속 `span_segments`를 사람이 읽기 쉽게 표시할 때는 공용 gap marker `" ... "`를 사용하고, canonical span 자체는 항상 `span_segments`입니다.

## `regex/df003_versions.jsonl` schema

```json
{"item_id":"df003","regex_version":"v1","pattern":"...","gold_total":50,"gold_matched":43,"gold_recall":0.86,"created_by":"llm","note":"initial draft"}
```

## 말뭉치 검색 산출물 schema

말뭉치 검색의 primary output은 detection JSONL입니다. 사람 검수용 CSV는 이 JSONL에서 후보 단위로 펼쳐 자동 생성합니다.

### `hits/{item_id}_{corpus}_batch###_detection.jsonl`

문장 하나당 한 줄을 사용합니다.

```json
{"text_id":"news_000001","raw_text":"저는 제주도에 가 본 적이 있어요.","corpus_name":"news","batch_id":"batch000","candidates":[{"unit_id":"df003","origin_e_id":"df003","unit_type":"item","member_e_ids":["df003"],"group":"b","canonical_form":"ㄴ/은 적 있/없","regex_match_span":[12,16],"regex_match_text":"적이 있","span_segments":[[10,13],[15,16]],"span_key":"10:13|15:16","span_text":"본 적 ... 있","span_source":"component_spans","component_span_status":"ok","detect_rule_ids":["r_df003_d01"],"hard_fail_rule_ids":[]}]}
```

### `hits/{item_id}_{corpus}_batch###_review.csv` 필수 열

```text
unit_id
origin_e_id
unit_type
member_e_ids
group
canonical_form
hit_id
text_id
corpus_name
batch_id
raw_text
regex_match_span
regex_match_text
span_segments
span_key
span_text
span_source
component_span_status
partial_span_text
matched_component_ids
missing_required_component_ids
partial_component_spans
partial_span_segments
detect_rule_ids
hard_fail_rule_ids
llm_temp_label
llm_note
human_label
span_status
corrected_span_segments
corrected_span_text
memo
reviewer
```

`llm_temp_label`은 참고용입니다. 최종 라벨이 아닙니다. `human_label`과 최종 span은 사람이 확정합니다.

`human_label` 값:

```text
TP
FP
unclear
```

`span_status` 값:

```text
ok
span_wrong
not_applicable
```

## `{item_id}_encoder_pair_examples.jsonl` schema

인코더 학습 경로에서는 Excel을 읽지 않습니다. 사람이 검수하거나 확인하는 파일은 `.xlsx`/`.csv`로 유지하되, 학습과 이후 runtime 입력 생성은 `detector_bundle.json`과 `encoder_pair_examples.jsonl`을 기준으로 합니다.

`text_b`는 dict Excel을 직접 읽지 않고 detector bundle에서 생성합니다. 단일 item은 `items_by_e_id[item_id]` 또는 `runtime_units[item_id]`의 `canonical_form`/`gloss`를 사용하고, polyset task는 `runtime_units[ps_id]`의 `canonical_form`/`gloss`를 사용합니다.

```json
{"schema_version":"hantalk_encoder_pair_example_v1","input_construction_version":"hantalk_binary_pair_v1","item_id":"df003","example_id":"df003-pos-0001","label":1,"label_name":"positive","example_role":"pos_disconti","negative_type":null,"split":"train","text_a":"저는 제주도에 가 [SPAN]본 적[/SPAN]이 [SPAN]있[/SPAN]어요.","text_b":"ㄴ/은 적 있/없\n어떤 행위나 상태를 해 본 경험이 있거나 없음을 나타냄.","raw_text":"저는 제주도에 가 본 적이 있어요.","span_segments":[[10,13],[15,16]],"span_key":"10:13|15:16","span_text":"본 적 ... 있","canonical_form":"ㄴ/은 적 있/없","gloss":"어떤 행위나 상태를 해 본 경험이 있거나 없음을 나타냄.","pattern_type":"disconti","source_hit_id":"daily_conversation_b000_000001-cand01","corpus_domain":"daily_conversation","detect_rule_ids":["r_df003_d01"]}
```

`label` 값:

- `1`: positive / TP
- `0`: negative / FP

`example_role` 값:

- `pos_conti`: TP이며 span segment가 1개인 예문
- `pos_disconti`: TP이며 span segment가 2개 이상인 예문
- `neg_target_absent`: FP 예문. detector가 잡은 span을 그대로 보존하되 label은 0으로 둠

원칙:

- 새 HanTalk 산출물의 span 문자열 표현은 JSON list 형식인 `[[10,13],[15,16]]`으로 통일합니다.
- parser는 과거 호환을 위해 `[(10,13),(15,16)]`도 읽을 수 있지만, writer는 항상 JSON list 형식만 출력합니다.
- `conf_e_id`, `neg_boundary`, `neg_confusable`는 새 HanTalk 인코더 예문 export 경로에서 사용하지 않습니다.
- split은 `pos_conti`, `pos_disconti`, `neg_target_absent` role별 stable hash 정렬 후 배정합니다.
- 학습용 `.jsonl`은 기계친화 SSOT이고, `.xlsx`는 사람이 확인하기 위한 gold-like 사본입니다.

## 전체 encoder 예문 aggregate

문법항목별 `{item_id}_encoder_pair_examples.jsonl`은 item별 학습 예문 SSOT입니다. 여러 문법항목이 쌓이면 `src.merge_encoder_examples`가 item별 SSOT를 읽어 전체 aggregate와 사람이 보는 ledger를 자동 생성합니다.

출력:

```text
HanTalk_arti/example_making/all/all_encoder_pair_examples.jsonl
HanTalk_arti/example_making/all/all_encoder_examples.xlsx
HanTalk_arti/example_making/all/all_encoder_examples_summary.json
```

원칙:

- item별 `{item_id}_encoder_pair_examples.jsonl`은 item별 SSOT입니다.
- `all_encoder_pair_examples.jsonl`은 item별 JSONL을 병합해 만든 자동 생성 aggregate이며, SSOT가 아닙니다.
- `all_encoder_examples.xlsx`는 전체 encoder pair input을 사람이 확인하기 위한 ledger입니다.
- 전체 `all_encoder_*` 파일은 수동 append하거나 직접 수정하지 않습니다. item별 JSONL이 바뀌면 `src.merge_encoder_examples`로 전체 파일을 다시 생성합니다.
- merge 단계에서는 `example_id`, `(item_id, example_id)`, `(item_id, label, raw_text, span_key)` 중복을 fatal error로 처리합니다.
- 인코더 학습은 개별 문법항목 하나가 끝날 때마다 바로 실행하지 않고, 문법항목별 TP/FP export가 충분히 쌓인 뒤 전체 aggregate를 기준으로 실행합니다.

## `src/train_encoder_pair.py` 학습 실행 파일

HanTalk binary encoder 학습은 `src/train_encoder_pair.py`를 기준 실행 파일로 합니다. 이 스크립트는 Excel을 읽지 않고, `src.export_encoder_examples`가 생성한 `{item_id}_encoder_pair_examples.jsonl`만 학습 입력으로 사용합니다.

모델 구조:

```text
AutoTokenizer
AutoModel
→ pooling(masked_mean 기본, cls 선택 가능)
→ Linear(hidden_size, 1) head
→ BCEWithLogitsLoss
→ sigmoid + threshold=0.5 평가
```

기본 원칙:

- backbone은 `--model-name-or-path`로 지정하며 특정 모델에 고정하지 않습니다.
- tokenizer는 `--tokenizer-name-or-path`가 없으면 model path를 그대로 사용합니다.
- 목표는 F1=1을 달성할 수 있는 모델 중 응답속도가 가장 빠른 모델을 찾는 것입니다.
- train DataLoader만 seed 기반 shuffle을 사용하고, dev/test는 debug prediction 재현성을 위해 고정 순서로 평가합니다.
- best checkpoint는 `dev_loss_mean` 최소, 동률이면 `dev_balanced_acc` 최대, 다시 동률이면 earlier epoch 기준으로 선택합니다.
- dev split은 정식 학습에서 필수입니다. train/dev에는 label 0/1이 모두 있어야 합니다.
- test split에 label 0/1 중 한쪽이 없으면 기본 warning이며, `--strict-splits`에서는 fatal로 처리합니다.

주요 CLI 예:

```bash
python3 -m src.train_encoder_pair \
  --examples-jsonl /Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003/df003_encoder_pair_examples.jsonl \
  --out-dir /Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/models/df003_encoder_pair_klue_roberta_base \
  --model-name-or-path klue/roberta-base \
  --seed 42 \
  --shuffle-seed 42 \
  --batch-size 8 \
  --eval-batch-size 16 \
  --epochs 10 \
  --lr 2e-5 \
  --weight-decay 0.01 \
  --warmup-ratio 0.0 \
  --max-length 256 \
  --threshold 0.5 \
  --early-stop-patience 4 \
  --wandb-mode disabled
```

학습 실행 전 데이터 검증만 할 때:

```bash
python3 -m src.train_encoder_pair \
  --examples-jsonl /Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003/df003_encoder_pair_examples.jsonl \
  --out-dir /private/tmp/hantalk_train_encoder_pair_validate \
  --model-name-or-path klue/roberta-base \
  --seed 42 \
  --shuffle-seed 42 \
  --validate-only \
  --overwrite
```

학습 산출물:

```text
out_dir/
  train_config.json
  data_summary.json
  metrics_by_epoch.jsonl
  train_log.jsonl
  train_encoder_pair_report.json
  checkpoints/
    best/
      encoder/
      tokenizer/
      head.pt
      runtime_encoder_config.json
      checkpoint_meta.json
    last/
      encoder/
      tokenizer/
      head.pt
      runtime_encoder_config.json
      checkpoint_meta.json
  predictions/
    dev_predictions_epoch_###.jsonl
    test_predictions_best.jsonl
    test_errors_best.jsonl
  debug/
    debug_predictions_latest.jsonl
    debug_predictions_latest.csv
```

`runtime_encoder_config.json`은 나중 HanTalk runtime이 오늘의 대화 맥락 없이도 같은 방식으로 inference를 재현하기 위한 파일입니다. 반드시 아래 정보를 포함합니다.

```json
{"schema_version":"hantalk_runtime_encoder_config_v1","input_construction_version":"hantalk_binary_pair_v1","span_marker_style":"[SPAN]...[/SPAN]","model_type":"pair_binary_encoder","pooling":"masked_mean","threshold":0.5,"max_length":256,"encoder_path":"encoder","tokenizer_path":"tokenizer","head_path":"head.pt"}
```

학습 report는 성능뿐 아니라 속도 지표도 기록합니다.

```text
n_parameters
n_trainable_parameters
device
avg_train_step_sec
avg_eval_batch_sec
avg_inference_example_sec
eval_examples_per_sec
```

초기 speed 측정은 tokenizer/collator/DataLoader overhead를 포함한 end-to-end eval latency로 기록하며, report에 `includes_tokenization=true`, `includes_dataloader_overhead=true`를 명시합니다.

또한 tokenizer truncation 위험을 확인하기 위해 split별 truncation 통계를 저장합니다.

```text
n_truncated_train/dev/test
truncation_rate
max_tokenized_length_observed
truncated_examples_sample
```

## Phase 1 CLI 목표

Phase 1에서 아래 명령 계열이 동작하는 것을 목표로 합니다. df003 단일 item 경로는 이미 검증했고, ps_ce002부터는 `--allow-polyset`과 별도 bundle을 사용해 polyset task 경로를 검증합니다.

```bash
python3 src/test_gold.py --item-id df003 --bundle configs/detector/detector_bundle.json --active-unit-id df003 --fail-on-fn
python3 -m src.detector.export_bundle --dict datasets/dict/dict_ps_ce002.xlsx --out configs/detector/detector_bundle_ps_ce002.json
python3 src/test_gold.py --item-id ps_ce002 --gold exported_gold/ps_ce002_gold_50.jsonl --bundle configs/detector/detector_bundle_ps_ce002.json --active-unit-id ps_ce002 --allow-polyset --bundle-match-policy overlap --fail-on-fn
python3 -m src.prepare_example_corpus --manifest configs/corpus/example_making_manifest.json --corpus-root /Users/yonghyunnam/coding/HanTalk_group/HanTalk_work/corpus/example_making --batch-index 2 --out /Users/yonghyunnam/coding/HanTalk_group/HanTalk_work/corpus/example_making/prepared/example_making_batch_002.jsonl --report /Users/yonghyunnam/coding/HanTalk_group/HanTalk_work/corpus/example_making/prepared/example_making_batch_002_report.json
python3 -m src.search_corpus --bundle configs/detector/detector_bundle.json --input-jsonl /Users/yonghyunnam/coding/HanTalk_group/HanTalk_work/corpus/example_making/prepared/example_making_batch_002.jsonl --active-unit-id df003 --artifact-root /Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making
python3 -m src.summarize_review --item-id df003 --input /Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003/df003_batch_002_human_review_labeled.xlsx --artifact-root /Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making
python3 -m src.export_encoder_examples --item-id df003 --bundle configs/detector/detector_bundle.json --input /Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003/df003_batch_000_human_review_labeled.xlsx --artifact-root /Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making
```

실제 모듈명과 명령어는 구현 과정에서 조정할 수 있지만, 조정 시 이 문서를 업데이트해야 합니다.

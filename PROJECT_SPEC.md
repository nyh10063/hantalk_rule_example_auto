# Project Spec

## 프로젝트 목표

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


## HanTalk 상위 구성과 원칙

HanTalk의 중요 주제는 다음 세 가지입니다.

```text
문법항목 기반
끊기지 않는 대화
교수 내용의 패널형 간접 제시
```

`끊기지 않는 대화`에는 녹음 버튼 없이 자연스럽게 이어지는 대화 경험도 포함합니다.

HanTalk의 주요 구성은 다음과 같습니다.

1. 문법항목 기반 대화 난이도 제어
2. 학습자 발화의 문법항목 사용 양상 진단
3. 문법항목 조건부 패널 피드백 및 연습 생성
4. 대화 주제 조건에 의거하여 LLM이 대화를 주도할 수 있도록 하는 기능

학습자 발화 진단에서는 아래 항목을 다룹니다.

- 문법항목의 출현
- 목표 문법항목 사용 기회
- 실제 사용
- 부정확 사용
- 회피, 대체 사용

대화 주제 조건 기반 LLM 주도 기능은 RAG 등 가장 적합한 방식을 찾아 활용합니다.

추가 목표:

- 실제 학습자가 사용할 수 있어야 합니다.
- 응답 속도에 영향을 줄 수 있는 요소들은 가급적 응답 속도를 빠르게 하는 방식으로 실현합니다.

## 단계별 계획

| Phase | 범위 | 도구 | 목표 |
| --- | --- | --- | --- |
| Phase 1 | 1개 항목 pilot | Codex + Python CLI + CSV/Excel | df003 end-to-end 자동화 검증 |
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

## Pilot 항목

| 필드 | 값 |
| --- | --- |
| item_id | df003 |
| name | `ㄴ/은 적 있/없` |
| meaning | 경험 유무 서술 |
| current goal | component span 조립이 붙은 DetectorEngine을 일반 말뭉치 batch 검색에 적용하기 |

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

Phase 1 pilot부터 아래 반자동 루프를 기준으로 합니다.

### 1. 검색용 정규식 완성

목표는 precision을 가능한 한 높이면서, 사람이 만든 정규식 gold 50개 기준 recall=1인 검색용 정규식을 만드는 것입니다.

절차:

1. LLM 또는 사람이 1차 정규식 초안을 만듭니다.
2. `exported_gold/{item_id}_gold_50.jsonl`에서 정규식 검색 recall을 계산합니다.
3. FN이 있으면 FN 원인을 분석하고 정규식을 수정합니다.
4. gold recall=1이 될 때까지 반복합니다.

주의:

- gold recall=1은 전체 한국어에서의 절대 recall=1이 아니라, 사람이 만든 정규식 gold 50개 기준의 recall=1입니다.
- 정규식 초안과 수정 이력은 `regex/{item_id}_versions.jsonl`에 남깁니다.

브릿지 원칙:

- 먼저 넓은 정규식으로 gold recall=1을 확보합니다.
- 브릿지 후보를 붙인 버전 또는 `rule_components.bridge_id` 기반 component bridge 버전도 별도로 만듭니다.
- 브릿지 후보 버전이 gold recall=1을 유지하는지 확인합니다.
- gold recall=1을 유지한 후보에 대해 5,000행 말뭉치에서 FP 감소량을 확인합니다.
- FP 감소 효과가 있거나 span 경계가 좋아지면 채택합니다.
- 효과가 작고 복잡도만 늘면 보류합니다.
- 브릿지 추가 여부는 정규식 버전 이력, `dict.xlsx`의 `bridge_id`, detector bundle report 중 해당 단계에 맞는 위치에 기록합니다.

### 2. 말뭉치 기반 FP 감소 및 학습 예문 후보 구축

gold recall=1을 만족한 정규식은 일반 말뭉치에서 실제 hit 후보를 검색하는 데 사용합니다.

절차:

1. 검색용 정규식으로 공통 prepared corpus batch를 검색하여 hit 후보를 수집합니다. 현재 예문 구축 batch는 일상대화 5,000행, 뉴스 2,000행, 비출판물 2,000행, 학습자 말뭉치 1,000행으로 구성합니다.
2. hit 후보를 사람이 TP/FP로 검수합니다. LLM은 임시 판단과 이유를 제공할 수 있지만 최종 라벨이 아닙니다.
3. 검수된 FP 유형을 근거로, gold recall=1을 유지하는 조건에서 정규식을 수정하여 FP를 줄입니다.
4. 더 이상 안전하게 FP를 줄이기 어렵다고 판단되면 해당 정규식을 검색용 정규식 후보로 확정합니다.
5. 확정된 검색용 정규식으로 다음 prepared corpus batch를 추가 검색합니다.
6. 사람이 TP/FP/span을 검수하여 positive/negative 예문을 각각 100개 모을 때까지 반복합니다.

원칙:

- 정규식을 수정할 때마다 반드시 gold recall test를 다시 실행합니다.
- gold recall이 1보다 낮아지는 수정은 검색용 정규식으로 확정하지 않습니다.
- 말뭉치 batch에서 나온 TP/FP는 후보이며, 최종 TP/FP와 span은 사람이 확정합니다.
- DetectorEngine은 가능한 경우 `component_spans`를 저장하고, component 조립 실패 시 `regex_match_fallback`으로 후보를 유지합니다.
- Kiwi 등 형태소 분석 기반 보정은 아직 도입하지 않았으며, 필요한 경우 후속 단계에서 비교합니다.
- 현재 단계에서는 인코더 fine-tuning을 수행하지 않고, positive/negative 예문 구축까지만 목표로 합니다.

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
│   └── detector/
│       └── detector_bundle.json
│   └── corpus/
│       └── example_making_manifest.json
├── exported_gold/
├── regex/
├── hits/
├── labels/
├── datasets/
│   ├── dict/
│   │   └── dict.xlsx
│   └── gold/
│       └── gold.xlsx
├── logs/
└── src/
```

## 핵심 파일 인터페이스

| 파일/폴더 | 역할 | 만든 주체 | 읽는 주체 |
| --- | --- | --- | --- |
| `configs/grammar_items.yaml` | 초기 pilot 보조 config. 장기 SSOT는 아님 | 사람 + Codex | 필요 시 참고 |
| `configs/detector/detector_bundle.json` | `dict.xlsx`에서 생성한 runtime detector bundle | 자동화 | DetectorEngine |
| `configs/corpus/example_making_manifest.json` | 예문 구축용 공통 말뭉치 batch 구성과 sampling 크기 | 사람 + Codex | `prepare_example_corpus.py` |
| `datasets/gold/gold.xlsx` | 정규식 gold 50개 원본 관리 파일 | 사람 | gold export/validation CLI |
| `exported_gold/df003_gold_50.jsonl` | `gold.xlsx`에서 자동 생성한 item별 정규식 gold positive 50개 | 자동화 | gold test CLI |
| `regex/df003_versions.jsonl` | 정규식 버전과 성능 로그 | 자동화 | regex iteration/report CLI |
| `HanTalk_work/corpus/example_making/prepared/example_making_batch_###.jsonl` | 여러 말뭉치에서 stable hash sampling으로 만든 공통 검색 batch | 자동화 | `search_corpus.py` |
| `HanTalk_arti/example_making/{item_id}_batch_###_detection.jsonl` | DetectorEngine 검색 결과 원본 | 자동화 | 사람 + 검수/분석 CLI |
| `HanTalk_arti/example_making/{item_id}_batch_###_human_review.csv` | 사람 검수용 후보 표 | 자동화 | 사람 검수 |
| `HanTalk_arti/example_making/{item_id}_batch_###_human_review_labeled.xlsx` | 사람이 확정한 TP/FP/span 검수 완료본 | 사람 | `summarize_review.py`, dataset export CLI |
| `HanTalk_arti/example_making/{item_id}_batch_###_human_review_labeled.csv` | 사람이 확정한 TP/FP/span 검수 완료본의 CSV 사본 | 사람 또는 자동 변환 | `summarize_review.py`, dataset export CLI |
| `HanTalk_arti/example_making/{item_id}_review_summary.json` | labeled review 파일 누적 집계와 목표 달성 여부 | 자동화 | 사람 + 다음 batch 판단 |
| `datasets/df003_encoder_candidates.jsonl` | 인코더 학습 후보 데이터 | 자동화 | 향후 fine-tuning |
| `logs/df003_regex_iterations.jsonl` | FN 분석과 수정 이력 | 자동화 | 사람 + Codex |


## `gold.xlsx` 설계 원칙

사람이 관리하는 정규식 gold 원본은 장기적으로 `datasets/gold/gold.xlsx`로 관리합니다.

`gold.xlsx`는 문법항목별 정규식 recall 평가에 사용하는 gold 예문을 담습니다. 300개 문법항목으로 확장하면 Excel 한 파일에서 사람이 전체 gold를 관리하고, CLI가 item별 JSONL을 자동 생성합니다.

원칙:

- `gold.xlsx`는 사람이 직접 관리하는 원본입니다.
- 300개 문법항목으로 확장할 때도 정규식 gold는 item별 흩어진 원본 파일이 아니라 `gold.xlsx`를 기준으로 관리합니다.
- `exported_gold/{item_id}_gold_50.jsonl`은 `gold.xlsx`에서 자동 생성되는 item별 검증용 산출물입니다.
- item별 JSONL은 사람이 직접 편집하는 원본이 아니라, 정규식 테스트 CLI와 자동화가 빠르게 읽기 위한 파일입니다.
- gold 파일은 사용자 실시간 대화 응답 경로에서 사용하지 않습니다. 따라서 item별 JSONL은 앱 응답속도 목적이 아니라 개발/검증 속도와 재현성을 위한 산출물입니다.
- `gold.xlsx`를 만들지 않은 상태에서 item별 JSONL만 계속 늘리는 방식은 장기 운영 기준으로 삼지 않습니다.

## `dict.xlsx` 설계 원칙

사람이 관리하는 문법항목 사전은 장기적으로 `dict.xlsx`로 관리합니다. `configs/grammar_items.yaml`은 필요하면 `dict.xlsx`에서 생성되는 기계 친화적 산출물로 둡니다.

`dict.xlsx`의 기본 시트는 아래 3개입니다.

```text
items
rule_components
detect_rules
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

사람이 관리하는 문법항목 사전의 SSOT는 `datasets/dict/dict.xlsx`입니다. 단, runtime detector는 Excel을 직접 읽지 않습니다. `dict.xlsx`는 아래 명령으로 runtime bundle로 export합니다.

```bash
python3 -m src.detector.export_bundle \
  --dict datasets/dict/dict.xlsx \
  --out configs/detector/detector_bundle.json
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
- `group=c` polyset runtime unit은 아직 실험 단계이므로 기본 실행을 막습니다.
- polyset unit은 명시적 실험에서 `allow_experimental_polyset=True`를 넘긴 경우에만 실행합니다.
- rule 하나에서 match가 폭주하지 않도록 `max_matches_per_rule` 제한을 둡니다. 기본값은 50입니다.
- component 후보가 폭주하지 않도록 `max_candidates_per_component` 제한을 둡니다. 기본값은 20입니다.
- component 후보 조합 경로가 폭주하지 않도록 `max_component_paths` 제한을 둡니다. 기본값은 2000입니다.
- component span 조립은 문장 전체가 아니라 detect regex match 주변 `component_window_chars` 안에서만 수행합니다. 기본값은 좌우 각각 20자입니다.
- component/bridge 상세 debug는 기본 출력하지 않고 `include_debug=True`일 때만 포함합니다.
- 제한에 걸리면 detector result summary의 `n_matches_truncated`, `truncated_rules`에 기록합니다.
- detector result summary에는 component span 상태를 빠르게 확인할 수 있도록 `n_component_span_success`, `n_component_span_fallback`, `n_component_span_regex_only`, `span_source_counts`를 기록합니다.

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
- 현재 구현된 bridge는 `adnominal_n`, `thing`입니다.
- `adnominal_n`은 `본`, `간`, `한`처럼 종성 ㄴ을 가진 음절과 명시적 `은`/`ㄴ`을 가볍게 찾습니다.
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
- `detect_rules.e_id`와 `rule_components.e_id`는 반드시 `items.e_id`에 존재해야 합니다.
- `items.detect_ruleset_id`는 detect rule을 1개 이상 포함해야 합니다.
- `items.verify_ruleset_id`가 있으면 verify rule을 1개 이상 포함해야 합니다.
- 같은 `ruleset_id` 안에 detect/verify stage가 섞이면 fatal error입니다.
- Excel header row 중간에 빈 header가 있으면 값과 header가 어긋날 수 있으므로 fatal error입니다.
- pattern이 `r"..."` 같은 Python literal처럼 보이는 경우, group=c인데 polyset_id가 없는 경우, verify rule인데 hard_fail=false인 경우는 warning입니다.

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

현재 batch 구성:

| corpus_domain | sample size |
| --- | ---: |
| `daily_conversation` | 5,000 |
| `news` | 2,000 |
| `non_published` | 2,000 |
| `learner_spoken_5_6` | 1,000 |

원칙:

- manifest에는 절대경로를 넣지 않습니다.
- 실제 말뭉치 폴더는 CLI의 `--corpus-root`로 전달합니다.
- 입력 통합 파일은 `text;source` 계열 형식으로 읽습니다. header가 있으면 `sentence`, `form`, `text`, `raw_text`를 text column 후보로, `source`를 source column 후보로 봅니다.
- header가 예상과 다르면 첫 번째 열을 text, 마지막 열을 source로 해석합니다.
- 데이터 line은 문장 안의 세미콜론을 보호하기 위해 마지막 delimiter 기준으로 `rsplit(delimiter, 1)` 방식으로 분리합니다.
- 대용량 말뭉치를 메모리에 모두 올리지 않고, stable hash streaming sampling으로 domain별 batch를 구성합니다.
- 같은 `seed`, `batch_index`, 입력 파일이면 prepared JSONL은 재현 가능해야 합니다.
- `batch_index=k`는 domain별 hash 순서에서 `kN`부터 `(k+1)N` 구간을 선택합니다.

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
  --out-jsonl /Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003_batch_000_detection.jsonl \
  --review-csv /Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003_batch_000_human_review.csv \
  --report-json /Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003_batch_000_search_report.json
```

원칙:

- `--active-unit-id`는 여러 번 줄 수 있습니다. Phase 1 실행은 우선 `df003` 하나로 합니다.
- detection JSONL은 hit가 있는 문장만 저장합니다.
- human review CSV는 candidate 하나를 한 행으로 펼쳐 사람이 `human_label`, `span_status`, `corrected_span_segments`, `memo`, `reviewer`를 채울 수 있게 합니다.
- 검수 편의를 위해 `raw_text`, `regex_match_text`, `human_label` 열을 서로 붙여 배치합니다.
- LLM 검수 보조를 붙일 가능성에 대비해 `llm_temp_label`, `llm_note` 열을 비워 둡니다. 이 값은 최종 라벨이 아니라 임시 참고용입니다.
- human review CSV는 Excel에서 한국어가 깨지지 않도록 `utf-8-sig`로 저장합니다.
- review CSV는 `span_segments`, `span_key`, `span_text`, `span_source`, `component_span_status`, `applied_bridge_ids`, `detect_rule_ids`를 포함합니다.
- search report는 domain별 candidate 수, span source count, component span status count, 실행 시간을 기록합니다.

## Labeled review summary

사람 검수가 끝난 파일은 자동 생성 검수표와 구분하기 위해 `_labeled` suffix를 붙입니다.

예:

```text
/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003_batch_000_human_review_labeled.xlsx
/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003_batch_000_human_review_labeled.csv
```

`/Users/yonghyunnam/Downloads/for_codex2` 같은 전달용 폴더는 임시 확인 폴더로만 사용하고, 자동화의 기준 입력으로 삼지 않습니다. 기준 labeled 파일은 `HanTalk_arti/example_making` 아래에 둡니다.

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

`summarize_review.py`의 최소 집계 항목:

- 입력 파일 수와 총 후보 행 수
- `human_label` 정규화 결과별 count: `tp`, `fp`, `unclear`, invalid/blank
- `span_status` 정규화 결과별 count
- `corpus_domain`별 TP/FP count
- `span_source`별 TP/FP count
- `component_span_status`별 TP/FP count
- `positive_100`, `negative_100` 달성 여부

주의:

- `human_label`이 최종 기준입니다. LLM 임시 라벨은 최종 라벨로 쓰지 않습니다.
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

component bridge 공용화와 df003 component span 조립도 Phase 1에서 구현되었습니다. 아래 항목들은 아직 당장 구현하지 않고, 다음 단계에서 실행 가능성과 schema 안정성을 검토합니다.

- `group=c` 항목을 사용자 실시간 발화 detect에서는 개별 `e_id`가 아니라 `polyset_id` 단위 runtime unit으로 합치는 구조.
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

`configs/grammar_items.yaml`은 Phase 1 초기에 만든 pilot 보조 config입니다. 현재 장기 SSOT는 `datasets/dict/dict.xlsx`와 `datasets/gold/gold.xlsx`입니다.

원칙:

- 새 schema나 runtime 동작은 `dict.xlsx` → `detector_bundle.json` 경로를 기준으로 구현합니다.
- `configs/grammar_items.yaml`은 필요할 때 사람이 읽는 보조 설명 또는 `dict.xlsx`에서 생성되는 산출물로만 둡니다.
- 문법항목 상태와 detect rule의 최신 여부는 `dict.xlsx`, `regex/{item_id}_versions.jsonl`, `logs/` report를 기준으로 확인합니다.

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

## `datasets/df003_encoder_candidates.jsonl` schema

```json
{"unit_id":"df003","origin_e_id":"df003","unit_type":"item","member_e_ids":["df003"],"group":"b","canonical_form":"ㄴ/은 적 있/없","example_id":"df003-TP-001","raw_text":"저는 제주도에 가 본 적이 있어요.","span_segments":[[10,13],[15,16]],"span_key":"10:13|15:16","span_text":"본 적 ... 있","label":1,"source_hit_id":"df003-HIT-0001","detect_rule_ids":["r_df003_d01"]}
```

`label` 값:

- `1`: positive / TP
- `0`: negative / FP

## Phase 1 CLI 목표

Phase 1에서 최종적으로 아래 명령이 동작하는 것을 목표로 합니다.

```bash
python3 src/test_gold.py --item-id df003 --bundle configs/detector/detector_bundle.json --active-unit-id df003 --fail-on-fn
python3 -m src.search_corpus --item-id df003 --corpus news --batch-size 5000
python3 -m src.export_review_sheet --item-id df003
python3 -m src.export_encoder_data --item-id df003 --pos 100 --neg 100
```

실제 모듈명과 명령어는 구현 과정에서 조정할 수 있지만, 조정 시 이 문서를 업데이트해야 합니다.

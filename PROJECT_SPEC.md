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
| current goal | 정규식 골드 50개 기준 recall=1 검색용 정규식 만들기 |

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
| corpus search | 말뭉치 선택 | regex search, span 추출, 중복 제거 |
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
- 브릿지 후보를 붙인 버전도 별도로 만듭니다.
- 브릿지 후보 버전이 gold recall=1을 유지하는지 확인합니다.
- gold recall=1을 유지한 후보에 대해 5,000행 말뭉치에서 FP 감소량을 확인합니다.
- FP 감소 효과가 있거나 span 경계가 좋아지면 채택합니다.
- 효과가 작고 복잡도만 늘면 보류합니다.
- 브릿지 추가 여부도 정규식 버전 이력에 기록합니다.

### 2. 말뭉치 기반 FP 감소 및 학습 예문 후보 구축

gold recall=1을 만족한 정규식은 일반 말뭉치에서 실제 hit 후보를 검색하는 데 사용합니다.

절차:

1. 검색용 정규식으로 뉴스 말뭉치와 일상 대화 말뭉치를 각각 5,000행 단위 batch로 검색하여 hit 후보를 수집합니다.
2. hit 후보를 사람이 TP/FP로 검수합니다. LLM은 임시 판단과 이유를 제공할 수 있지만 최종 라벨이 아닙니다.
3. 검수된 FP 유형을 근거로, gold recall=1을 유지하는 조건에서 정규식을 수정하여 FP를 줄입니다.
4. 더 이상 안전하게 FP를 줄이기 어렵다고 판단되면 해당 정규식을 검색용 정규식 후보로 확정합니다.
5. 확정된 검색용 정규식으로 다음 5,000행 batch를 추가 검색합니다.
6. 사람이 TP/FP/span을 검수하여 positive/negative 예문을 각각 100개 모을 때까지 반복합니다.

원칙:

- 정규식을 수정할 때마다 반드시 gold recall test를 다시 실행합니다.
- gold recall이 1보다 낮아지는 수정은 검색용 정규식으로 확정하지 않습니다.
- 말뭉치 batch에서 나온 TP/FP는 후보이며, 최종 TP/FP와 span은 사람이 확정합니다.
- 스팬은 처음에는 정규식 match span을 저장하고, 필요한 단계에서 Kiwi 등 형태소 분석 기반 보정 또는 span 검수를 붙입니다.
- 현재 단계에서는 인코더 fine-tuning을 수행하지 않고, positive/negative 예문 구축까지만 목표로 합니다.

## 형태소 분석 및 브릿지 cache 설계 메모

브릿지를 사용하는 규칙은 형태소 분석 결과나 token/span 정보를 참조할 수 있습니다. 실시간 HanTalk에서는 형태소 분석을 문법항목마다 반복하면 응답 속도에 악영향을 줄 수 있으므로, 장기적으로 아래 구조를 검토합니다.

```text
문장 입력
→ 형태소 분석 1회 수행
→ token/span/cache 생성
→ 필요한 규칙들이 분석 결과 공유
→ 후보만 인코더로 전달
```

원칙:

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
| `configs/grammar_items.yaml` | 문법항목 정의와 상태 | 사람 + Codex | 모든 CLI |
| `configs/detector/detector_bundle.json` | `dict.xlsx`에서 생성한 runtime detector bundle | 자동화 | DetectorEngine |
| `datasets/gold/gold.xlsx` | 정규식 gold 50개 원본 관리 파일 | 사람 | gold export/validation CLI |
| `exported_gold/df003_gold_50.jsonl` | `gold.xlsx`에서 자동 생성한 item별 정규식 gold positive 50개 | 자동화 | gold test CLI |
| `regex/df003_versions.jsonl` | 정규식 버전과 성능 로그 | 자동화 | regex iteration/report CLI |
| `hits/df003_corpus_hits.csv` | 말뭉치 검색 hit와 span | 자동화 | 사람 검수 |
| `labels/df003_human_review.csv` | 사람이 확정한 TP/FP/span | 사람 | dataset export CLI |
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
- `stage=verify`인 규칙의 `target`은 `raw_sentence` 또는 `char_window`만 허용합니다.
- 이전 프로젝트 코드의 `token_window`는 실제로 토큰 단위가 아니라 문자 단위 후보 주변 window이므로, 새 규칙 모듈을 만들 때 `char_window`로 이름을 바꿉니다.
- 같은 `stage` 안에서는 `priority`가 작은 규칙부터 실행합니다.
- `priority`의 숫자가 작을수록 더 강한 우선순위를 가집니다.

주의:

- `detect_rules.comp_id`는 사용하지 않습니다.
- `detect_rules.scope`는 사용하지 않습니다. 이전 프로젝트의 `scope`는 실버 라벨 구축용 규칙과 추론용 규칙을 분리하기 위한 열이었으나, HanTalk 프로젝트에서는 실버 라벨을 만들지 않습니다.
- `detect_rules.confidence_delta`는 사용하지 않습니다. 새 규칙 모듈에서 `verify`는 점수 조정이 아니라 hard_fail 전용으로 사용합니다.
- `rule_components.comp_id`는 component span 탐색과 디버깅에 필요하므로 유지합니다.
- Phase 1에서는 context rule을 사용하지 않습니다.

## Detector runtime 1차 구현 원칙

사람이 관리하는 문법항목 사전의 SSOT는 `datasets/dict/dict.xlsx`입니다. 단, runtime detector는 Excel을 직접 읽지 않습니다. `dict.xlsx`는 아래 명령으로 runtime bundle로 export합니다.

```bash
python3 -m src.detector.export_bundle \
  --dict datasets/dict/dict.xlsx \
  --out configs/detector/detector_bundle.json
```

runtime detector는 `configs/detector/detector_bundle.json`을 읽고, 정규식을 초기화 시점에 compile/cache하여 사용합니다. 사용자 발화 detect 경로에서 Excel parsing을 반복하지 않는 것이 원칙입니다.

DetectorEngine 1차 구현 범위:

- `detector_bundle.json` 로딩
- `active_unit_ids` 기준 runtime unit 선택
- `stage=detect`, `target=raw_sentence` 표면 정규식 실행
- `stage=verify`, `target=raw_sentence` 또는 `target=char_window` hard_fail 최소 구현
- candidate span을 `span_segments`로 출력

DetectorEngine 1차 구현의 span 정책:

- `span_segments`는 detector output의 canonical span 표현입니다.
- span은 Python 0-based `[start, end)` 규칙을 따릅니다.
- 불연속 표현은 여러 segment로 보존합니다.
- 1차 DetectorEngine은 아직 component 기반 교육적 span을 조립하지 않습니다.
- 1차 candidate의 `span_source`는 `regex_match`이고, `component_span_enabled`는 `false`입니다.
- 따라서 df003 `ㄴ/은 적 있/없`의 1차 출력이 `적이 있`일 수 있습니다. 이는 최종 교육적 span인 `본 적 ... 있`을 완성했다는 뜻이 아닙니다.

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

## 향후 detector 설계 검토 메모

이 섹션은 SSOT가 아닙니다. 프로젝트 초반에는 파일 schema, detector 출력 형식, profile 방식이 바뀔 가능성이 크므로, 아래 내용은 확정 설계가 아니라 다음 구현 단계에서 반드시 다시 검토할 후보 목록으로 둡니다.

바로 다음 구현 범위는 아래 3개로 제한합니다.

```text
src/detector/export_bundle.py
DetectorEngine 최소형
src/test_gold.py의 DetectorEngine 기반 리팩터링
```

위 3개를 제외한 아래 항목들은 당장 구현하지 않고, 다음 단계에서 실행 가능성과 schema 안정성을 검토합니다.

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

## `configs/grammar_items.yaml` 초안 schema

```yaml
df003:
  source_e_id: "df003"
  name: "ㄴ/은 적 있/없"
  display_name: "ㄴ/은 적 있/없(경험 유무 서술)"
  meaning: "경험 유무 서술"
  aliases:
    - "ㄴ 적 있"
    - "은 적 있"
    - "ㄴ 적 없"
    - "은 적 없"
    - "본 적 있"
    - "본 적 없"
  include_criteria:
    - "과거 경험의 존재 또는 부재를 나타내는 구성"
    - "있다, 없다, 있었다, 없었다, 있는, 없는 등 활용형 포함"
    - "적과 있/없 사이에 은, 는, 도, 만 등 보조사가 삽입된 경우 포함"
  exclude_criteria:
    - "'적'이 enemy 의미인 경우"
    - "'적다' 계열"
    - "'적어도' 부사"
    - "'옛적'처럼 어휘 내부에 포함된 경우"
  target_span_policy: "경험 표현의 핵심 형태 span. 불연속 표현은 target_spans에 여러 구간으로 보존한다."
  gold_file: "exported_gold/df003_gold_50.jsonl"
  gold_count: 50
  status:
    gold: ready
    regex: pending
    corpus_hits: pending
    human_review: pending
    dataset: pending
```

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

## `regex/df003_versions.jsonl` schema

```json
{"item_id":"df003","regex_version":"v1","pattern":"...","gold_total":50,"gold_matched":43,"gold_recall":0.86,"created_by":"llm","note":"initial draft"}
```

## `hits/df003_corpus_hits.csv` 필수 열

```text
item_id
hit_id
corpus_name
sentence
match_text
span_start
span_end
left_context
right_context
regex_version
llm_temp_label
llm_note
```

`llm_temp_label`은 참고용입니다. 최종 라벨이 아닙니다.

## `labels/df003_human_review.csv` 필수 열

```text
item_id
hit_id
sentence
match_text
span_start
span_end
human_label
span_status
memo
reviewer
```

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
{"item_id":"df003","example_id":"df003-TP-001","sentence":"저는 제주도에 가 본 적이 있어요.","span_start":8,"span_end":17,"label":1,"source_hit_id":"df003-HIT-0001"}
```

`label` 값:

- `1`: positive / TP
- `0`: negative / FP

## Phase 1 CLI 목표

Phase 1에서 최종적으로 아래 명령이 동작하는 것을 목표로 합니다.

```bash
python -m src.test_gold --item df003
python -m src.search_corpus --item df003 --corpus news
python -m src.export_review_sheet --item df003
python -m src.export_encoder_data --item df003 --pos 100 --neg 100
```

실제 모듈명과 명령어는 구현 과정에서 조정할 수 있지만, 조정 시 이 문서를 업데이트해야 합니다.

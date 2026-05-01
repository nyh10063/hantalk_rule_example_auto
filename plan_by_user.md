# 챗지피티 반자동화 추천 260429

핵심 방향은 이겁니다.

> **1개 항목 pilot에서는 최대한 가볍게 시작하고, 10개·50개·300개로 커질수록 도구를 단계적으로 붙인다.**
> 
> 
> 처음부터 Prefect, Label Studio, DVC, MLflow를 모두 넣지 않는다.
> 

---

# 전체 목표

300개 한국어 문법항목에 대해 다음 구조를 구축합니다.

```
문법항목별 검색용 정규식
→ recall 1에 가깝게 후보 검색
→ 일반 말뭉치에서 TP/FP 후보 수집
→ 사람이 최종 검수
→ 인코더 오탐 필터링 모델 학습용 positive/negative 예문 구축
```

현재는 **인코더 미세조정은 아직 하지 않고**, 우선은 **문법항목별 positive/negative 예문 구축 자동화**가 목표입니다.

---

# Phase 1. Pilot: “-(으)ㄴ 적이 있다” 1개 항목

## 사용할 앱 조합

```
Codex
+ Python CLI
+ Excel 또는 Google Sheets
+ GitHub private repo
+ JSONL/CSV 로그
```

## 앱별 역할

| 앱/도구 | 할 일 |
| --- | --- |
| **Codex** | Python 스크립트 작성, 정규식 테스트 코드 작성, 말뭉치 검색 코드 작성, CSV/JSONL export 코드 작성 |
| **Python CLI** | 정규식 실행, gold 예문 recall 계산, FN 출력, 일반 말뭉치 검색, span 추출 |
| **Excel / Google Sheets** | 사람이 hit 결과를 보고 TP/FP/unclear 판정 |
| **GitHub private repo** | 코드, 설정 파일, 정규식 버전, 실행 로그 관리 |
| **JSONL/CSV 로그** | 모든 정규식 버전, gold test 결과, corpus hit 결과 저장 |

Codex는 코드 생성·코드베이스 이해·코드 리뷰·버그 수정에 적합한 코딩 에이전트이므로, 지금처럼 Python pipeline을 빠르게 만드는 작업에 잘 맞습니다. ([OpenAI Developers](https://developers.openai.com/codex?utm_source=chatgpt.com))

## 내가 할 일

이 단계에서 사람인 네가 반드시 해야 할 일은 많습니다.

```
1. “-(으)ㄴ 적이 있다” 문법항목 정의 작성
2. 포함 기준 / 제외 기준 작성
3. 정규식 골드 positive 예문 50개 작성
4. 각 예문에서 target span 기준 정하기
5. LLM이 만든 정규식이 문법적으로 너무 넓거나 좁은지 판단
6. 일반 말뭉치 hit 결과를 보고 TP/FP/unclear 판정
7. 최종 검색용 정규식 승인
```

특히 pilot에서 가장 중요한 것은 **문법항목 해석 기준 고정**입니다.

예를 들어 “-(으)ㄴ 적이 있다”는 다음처럼 기준을 잡아야 합니다.

```
포함:
가 본 적이 있다
먹어 본 적이 있어요
만난 적이 있었어요
들어 본 적 있니?
해 본 적은 없어요

제외:
적이 많다
적을 만들다
옛적
적어도
적다
그 사람은 내 적이다
```

## 자동화가 할 일

```
1. LLM/Codex가 1차 정규식 생성
2. Python이 gold 50개에서 정규식 실행
3. recall 계산
4. FN 예문 출력
5. FN 원인 분석 prompt 생성
6. 수정 정규식 후보 생성
7. recall=1까지 반복
8. 일반 말뭉치 검색
9. hit sentence, matched span, 앞뒤 문맥 추출
10. CSV/Excel 검수표 생성
11. 사람이 붙인 TP/FP 라벨을 JSONL로 변환
```

## Pilot 산출물

```
regex_final/df003.json
gold/df003_gold_50.jsonl
logs/df003_regex_iterations.jsonl
hits/df003_corpus_hits.csv
labels/df003_human_review.csv
datasets/df003_encoder_candidates.jsonl
```

---

# Phase 2. 10개 문법항목 확장

## 사용할 앱 조합

```
Codex
+ Python package/CLI
+ Excel 또는 Google Sheets
+ GitHub private repo
```

필요할 때만:

```
+ Label Studio
```

## 이 단계의 목표

1개 pilot에서 만든 구조가 10개 항목에서도 작동하는지 확인합니다.

이때부터는 코드가 단순 스크립트가 아니라 작은 Python package가 되어야 합니다.

```
hantalk_regex/
  regex_draft.py
  regex_test.py
  corpus_search.py
  span_extract.py
  review_export.py
  dataset_export.py
```

## 내가 할 일

```
1. 10개 문법항목 선정
2. 각 항목별 정의·포함 기준·제외 기준 작성
3. 각 항목별 정규식 골드 50개 작성
4. 사람이 TP/FP 검수
5. 정규식 버전 중 최종본 승인
6. 오류 유형 메모 작성
```

## Codex가 할 일

```
1. 반복되는 CLI 구조 정리
2. grammar_items.yaml schema 만들기
3. 항목별 batch 실행 코드 작성
4. CSV 검수표 자동 생성
5. 라벨 파일을 encoder 학습용 JSONL로 변환
6. 정규식 버전별 성능 리포트 생성
```

## Excel/Google Sheets 유지 기준

10개 항목까지는 Excel/Sheets가 빠릅니다.

Label Studio는 아직 필수는 아닙니다.

다만 다음 문제가 나타나면 Label Studio로 넘어갑니다.

```
span을 사람이 자주 고쳐야 함
한 문장에 후보 span이 여러 개 있음
검수자가 2명 이상임
IAA 또는 adjudication이 필요함
TP/FP 외에 세부 오류 유형 라벨이 많아짐
```

---

# Phase 3. 50개 문법항목 확장

## 사용할 앱 조합

```
Codex
+ Python pipeline
+ Prefect
+ Label Studio
+ GitHub private repo
+ DVC 선택
```

## 왜 Prefect를 도입하나

50개부터는 단순 CLI만으로 상태 관리가 어려워집니다.

예를 들어 각 문법항목이 서로 다른 상태에 있을 수 있습니다.

```
df003: gold 완료, regex 완료, corpus hit 완료, human review 완료
G002: gold 완료, regex FN 있음
G003: corpus search 실패
G004: human review 대기
G005: TP 부족, 추가 corpus search 필요
```

Prefect는 Python 함수를 workflow로 만들고, state tracking, failure handling, monitoring을 제공하는 orchestration engine입니다. 또 LLM API 실패나 검색 실패처럼 재시도가 필요한 task에 retries를 설정할 수 있습니다. ([Prefect](https://docs.prefect.io/v3/get-started?utm_source=chatgpt.com))

따라서 50개부터는 Prefect가 Snakemake보다 실용적일 가능성이 큽니다.

## Prefect가 맡을 일

```
1. 문법항목별 workflow 상태 관리
2. LLM 정규식 생성 실패 재시도
3. corpus search 실패 재시도
4. TP/FP 수 부족 시 추가 검색 자동 실행
5. human review 대기 상태 표시
6. 각 항목별 완료 여부 dashboard화
```

## Label Studio가 맡을 일

Label Studio는 텍스트 span labeling, relation, annotation project 구성을 지원합니다. span 경계 검수가 중요해지면 Excel보다 훨씬 낫습니다. ([Label Studio](https://labelstud.io/guide/labeling?utm_source=chatgpt.com))

Label Studio에서 검수할 라벨은 다음 정도로 설계합니다.

```
TP
FP
unclear
span_wrong
duplicate
bad_sentence
```

필요하면 FP 유형도 붙입니다.

```
surface_homograph
wrong_function
wrong_boundary
lexical_false_positive
parser_error
```

## 내가 할 일

```
1. 50개 문법항목별 gold 50개 작성 또는 검수
2. Label Studio에서 TP/FP/span 검수
3. unclear 사례 판정 기준 확정
4. 문법항목별 제외 기준 업데이트
5. 최종 regex 승인
```

## Codex가 할 일

```
1. Prefect flow 코드 작성
2. Label Studio import/export 코드 작성
3. 검수 완료 여부 확인 코드 작성
4. TP/FP 부족 항목 자동 재검색 코드 작성
5. 항목별 리포트 자동 생성
```

---

# Phase 4. 300개 문법항목 전체 확장

## 사용할 앱 조합

```
Codex
+ Python pipeline
+ Prefect
+ Label Studio
+ GitHub private repo
+ DVC
+ MLflow
```

## DVC 도입 시점

DVC는 데이터와 모델을 Git-like 방식으로 관리하기 위한 도구입니다. 말뭉치, 라벨 데이터, 모델 파일이 커질 때 도입하면 됩니다. ([DVC](https://dvc.org/?utm_source=chatgpt.com))

300개 단계에서는 DVC가 필요해질 가능성이 큽니다.

DVC로 관리할 것:

```
corpora/
hits/
labels/
datasets/
model_checkpoints/
```

Git으로 관리할 것:

```
코드
설정 파일
정규식 metadata
작은 sample data
README
```

## MLflow 도입 시점

MLflow는 parameter, code version, metric, output file을 기록하고 시각화하는 tracking 도구입니다. ([MLflow AI Platform](https://mlflow.org/docs/latest/ml/tracking/?utm_source=chatgpt.com))

현재는 인코더 미세조정을 하지 않으므로 당장 필요하지 않습니다.

하지만 다음을 시작하면 도입합니다.

```
BERT verifier 실험
DeBERTa verifier 실험
문법항목별 threshold 실험
latency 측정
precision/recall/F1 비교
```

MLflow에 기록할 것:

```
item_id
regex_version
dataset_version
model_name
pooling_method
learning_rate
threshold
precision
recall
f1
latency_ms
```

---

# 전체 workflow 설계

## 1. 문법항목 설정 파일

모든 항목은 `grammar_items.yaml`에 넣습니다.

```yaml
df003:
  name: "-(으)ㄴ 적이 있다"
  meaning: "경험"
  aliases:
    - "ㄴ 적 있다"
    - "은 적 있다"
    - "본 적 있다"
  include_criteria:
    - "과거 경험 여부를 나타내는 구성"
  exclude_criteria:
    - "'적'이 enemy 의미인 경우"
    - "'적다' 계열"
    - "'적어도' 부사"
  target_span_policy: "문법항목 전체 표현 span"
  status:
    gold: ready
    regex: in_progress
    review: pending
```

## 2. 정규식 생성·수정 workflow

```
input:
  grammar_items.yaml
  gold 50 examples

process:
  1차 regex 생성
  gold test
  FN 추출
  FN 원인 분석
  regex 수정
  recall=1까지 반복

output:
  final_regex
  iteration_log
  FN history
```

## 3. corpus search workflow

```
input:
  final_regex
  news corpus
  dialogue corpus

process:
  regex search
  span 추출
  중복 제거
  주변 문맥 저장
  LLM 임시 TP/FP 판정 선택 가능

output:
  corpus_hits.csv
```

## 4. human review workflow

```
input:
  corpus_hits.csv

process:
  Excel/Sheets 또는 Label Studio에서 사람이 검수

output:
  human_labels.csv
```

## 5. dataset export workflow

```
input:
  human_labels.csv

process:
  TP 100개
  FP 100개
  span 포함
  train/dev/test 분할

output:
  encoder_dataset.jsonl
```

---

# 사람과 자동화의 역할 분담

## 네가 해야 하는 일

| 단계 | 네 역할 |
| --- | --- |
| 문법항목 정의 | 각 문법항목의 의미·형태·포함/제외 기준 확정 |
| 골드 제작 | 정규식 gold 50개 작성 |
| span 정책 | 어디부터 어디까지 span으로 볼지 결정 |
| 정규식 승인 | LLM이 만든 정규식의 과잉/과소 포착 판단 |
| TP/FP 검수 | corpus hit를 보고 최종 라벨 부여 |
| hard case 판정 | unclear, 중의적 사례의 처리 기준 확정 |
| 교육적 우선순위 | 300개 중 먼저 만들 항목 순서 결정 |

## Codex가 할 일

| 단계 | Codex 역할 |
| --- | --- |
| 코드 작성 | Python CLI, Prefect flow, Label Studio export/import 코드 작성 |
| 정규식 생성 보조 | LLM prompt와 regex draft 자동화 |
| 오류 분석 보조 | FN 목록을 보고 수정 후보 제안 |
| 반복 실행 | gold test, corpus search, report 생성 |
| 리포트 생성 | 항목별 recall, hit 수, TP/FP 수, 상태 출력 |
| 확장 자동화 | 1개 항목 코드를 10개·50개·300개 구조로 일반화 |

## 자동화가 할 수 없는 것

```
문법항목 의미 판단
한국어교육 관점의 포함/제외 기준 확정
진짜 TP/FP gold 판정
정규식이 교육적으로 적절한지 판단
오탐 유형의 이론적 분류
```

이 부분은 반드시 사람이 해야 합니다.

---

# 단계별 도구 도입표

| 단계 | 항목 수 | 도구 | 목표 |
| --- | --- | --- | --- |
| Phase 1 | 1개 | Codex + Python CLI + Excel/CSV | pilot 성공 |
| Phase 2 | 10개 | Codex + Python package + Excel/Sheets | 반복 구조 안정화 |
| Phase 3 | 50개 | Prefect + Label Studio 추가 | 상태 관리·검수량 처리 |
| Phase 4 | 300개 | DVC + MLflow 추가 | 데이터·실험 버전관리 |

---

# Pilot “-(으)ㄴ 적이 있다”의 구체적 실행 순서

## Step 0. 사람이 준비

```
df003 정의
positive gold 50개
제외 기준
span 기준
뉴스/대화 말뭉치 준비
```

## Step 1. Codex에게 요청

```
df003의 정의와 gold 예문을 보고 Python re 문법으로 검색용 정규식 초안을 만들어라.
정규식은 recall을 최우선으로 하되, 명백한 '적다/적어도/적(enemy)' 오탐은 피하라.
```

## Step 2. Python 실행

```bash
python -m hantalk_regex.test_gold --item df003
```

출력:

```
recall: 0.86
FN examples: 7개
matched examples: 43개
```

## Step 3. Codex가 FN 분석

```
FN 원인:
- '해 본 적은'처럼 보조사 '은' 삽입
- '가 본 적도'처럼 보조사 '도' 삽입
- '있었나요' 변형 누락
```

## Step 4. 정규식 수정

```bash
python -m hantalk_regex.test_gold --item df003 --regex-version v2
```

반복해서 recall=1 달성.

## Step 5. 일반 말뭉치 검색

```bash
python -m hantalk_regex.search_corpus --item df003 --corpus news
python -m hantalk_regex.search_corpus --item df003 --corpus dialogue
```

## Step 6. 검수표 생성

```bash
python -m hantalk_regex.export_review_sheet --item df003
```

## Step 7. 사람이 TP/FP 검수

Excel/Sheets에서:

```
TP
FP
unclear
span_wrong
memo
```

## Step 8. positive/negative 100개씩 export

```bash
python -m hantalk_regex.export_encoder_data --item df003 --pos 100 --neg 100
```

---

# 최종 추천

Codex의 제안을 반영한 최종 계획은 다음입니다.

```
지금 바로:
Codex + Python CLI + Excel/CSV + GitHub private

10개 항목:
Python package화 + 검수표 자동화

50개 항목:
Prefect + Label Studio 도입

300개 항목:
DVC + MLflow 도입
```

가장 중요한 운영 원칙은 이것입니다.

> **자동화는 “후보 생성·검색·반복 테스트·로그화”를 맡고, 사람은 “문법항목 기준 확정·골드 제작·TP/FP 최종 판정”을 맡는다.**
> 

이 방식이 실제 수행 가능성이 가장 높습니다.
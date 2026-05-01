# Decisions

이 문서는 프로젝트의 중요한 결정과 이유를 짧게 기록합니다. 너무 형식적인 ADR이 아니라, 나중에 방향을 잃지 않기 위한 작업 로그입니다.

## 2026-04-29

### Decision: 기준 문서는 4개로 시작한다.

- `AGENTS.md`
- `PROJECT_SPEC.md`
- `CURRENT_TASK.md`
- `DECISIONS.md`

Reason: 장기 프로젝트에서 Codex가 대화 기록에만 의존하면 방향이 흔들릴 수 있으므로, 저장소 안에 항상 먼저 읽는 기준 문서를 둔다. 다만 pilot 단계에서는 문서를 너무 많이 나누지 않는다.

### Decision: Phase 1은 df003 pilot 하나로 시작한다.

df003은 `ㄴ/은 적 있/없` 계열 문법항목이다.

Reason: 300개 전체 자동화 전에 1개 항목에서 end-to-end pipeline을 검증해야 한다.

### Decision: Phase 1에서는 Python CLI + CSV/Excel 검수표를 사용한다.

Reason: pilot 1개 항목에서는 Label Studio, Prefect, DVC, MLflow 도입 비용이 더 크다. 먼저 파일 기반 pipeline을 안정화한다.

### Decision: Phase 1에서는 Label Studio, Prefect, DVC, MLflow, LangGraph를 도입하지 않는다.

Reason: 초기에는 도구 운영보다 정규식 생성, gold recall 평가, corpus search, 검수표 export의 핵심 흐름을 완성하는 것이 중요하다.

### Decision: LLM 라벨은 임시판정으로만 사용한다.

Reason: 인코더 오탐 필터링 학습 데이터의 품질을 보장하기 위해 TP/FP 최종 판정은 사람이 해야 한다.

### Decision: 현재 단계에서는 인코더 fine-tuning을 수행하지 않는다.

Reason: 지금 목표는 300개 문법항목의 positive/negative 예문 구축 자동화이다. 모델 학습은 데이터 구축 pipeline이 안정된 뒤 수행한다.

### Decision: 정규식 recall=1은 gold 50개 기준으로 정의한다.

Reason: 전체 한국어 문장 공간에서의 절대 recall=1은 현실적으로 검증할 수 없다. 사람이 만든 정규식 gold 50개를 기준으로 반복 개선한다.


### Decision: df003 이름은 `ㄴ/은 적 있/없`으로 기록한다.

Reason: 문법항목 명명은 필수 구성성분만 포함하는 방향으로 통일한다. 기존 df003 정규식 gold에는 `있다`, `있는`, `없다`, `없는`, `없었다`처럼 다양한 활용형이 포함되어 있지만, 항목명과 config name은 핵심 구성인 `ㄴ/은 적 있/없`으로 기록하고 활용형은 예문과 포함 기준에서 다룬다.

### Decision: df003 gold 50개는 기존 df003 정규식 gold positive 예문을 변환해 사용한다.

Reason: 이전 프로젝트에서 사람이 만든 df003 정규식 gold가 이미 존재하며, Phase 1 pilot의 기준 자료로 재사용하기에 적합하다. 원본 파일은 `정규식 골드/정규식 골드_df003.xlsx`이다.


## 2026-04-30

### Decision: pilot item_id는 `df003`으로 통일한다.

Reason: pilot 항목은 이전 문법항목 체계에서 이미 `df003`으로 관리되던 `ㄴ/은 적 있/없(경험 유무 서술)`이다. 장기 프로젝트에서도 기존 문법항목 ID를 그대로 사용해야 이후 데이터, 정규식, 인코더 학습 자료와 연결이 안정적이다.


### Decision: 신규 문법항목 ID는 유형별 접두어 체계를 따른다.

Reason: 300개 문법항목으로 확장할 때 ID만 보고 문법항목 유형을 빠르게 파악하고, 정규식/예문/인코더 데이터 파일을 안정적으로 연결하기 위해 유형별 접두어를 사용한다. 새 ID는 조사 `pt###`, 연결어미 `ce###`, 종결어미 `fe###`, 의존어 구성(연결표현) `dc###`, 의존어 구성(종결표현) `df###`, 선어말어미 `pf###`, 관형사형어미 `ae###` 형식을 따른다. pilot ID는 의존어 구성(종결표현) 접두어 규칙에 따라 `df003`으로 사용한다.


### Decision: pilot item_id는 `df003`으로 최종 통일한다.

Reason: `ㄴ/은 적 있/없(경험 유무 서술)`은 의존어 구성(종결표현)에 해당하므로 신규 ID 네이밍 규칙의 `df###` 접두어를 따른다. 따라서 Phase 1 pilot과 관련 산출물은 `df003`을 기준 ID로 사용한다.

### Decision: `detect_rules` 시트는 표면 정규식 전용으로 단순화한다.

Reason: 새 HanTalk 프로젝트에서는 context rule을 Phase 1 범위에서 제외하고, `detect_rules`는 후보 생성 및 hard_fail 검증에 사용하는 표면 정규식 규칙만 담는다. 따라서 사람이 관리하는 `dict.xlsx`의 `detect_rules` 시트에서는 `comp_id`, `rule_type`, `engine`을 제거한다. 내부 로더가 `rule_type=surface_regex`, `engine=re`를 자동 보충한다. 단, `rule_components.comp_id`는 component span 탐색에 필요하므로 유지한다.

## 2026-05-01

### Decision: `items.group`으로 문법항목 처리 수준을 구분한다.

Reason: 300개 문법항목을 모두 같은 방식으로 처리하면 불필요한 오탐 필터링 또는 위험한 다의의미 분별이 섞일 수 있다. 따라서 `items` 시트의 `group` 열에 `a`(오탐제거 불필요), `b`(오탐제거 필요, 다의의미 분별 불필요), `c`(오탐제거 및 다의의미 분별 필요)를 기록한다. 한톡 프로젝트는 사용자의 실시간 발화 분석에서는 기본적으로 다의의미 분별을 하지 않는다. 이전 프로젝트에서 다의의미 판별 최고 확률이 약 80% 수준이었기 때문에 실시간 판정에 쓰기에는 위험이 크다. 다만 문법항목 사용 제안 패널이나 발화 오류 수정 제안에서는 교육적 정확성이 필요하므로, 다의의미 분별이 필요한 항목을 `group=c`로 구분한다.

### Decision: `detect_rules.scope`를 제거한다.

Reason: 이전 프로젝트의 `scope`는 실버 라벨 구축용 규칙과 추론용 규칙을 분리하기 위한 열이었다. HanTalk 프로젝트에서는 실버 라벨을 만들지 않고, `detect_rules`를 후보 생성 및 hard_fail 검증에 사용하는 표면 정규식 규칙으로 단순화하므로 사람이 관리하는 `dict.xlsx`의 `detect_rules` 시트에서 `scope`를 제거한다.

### Decision: `detect_rules`는 `detect → verify` 순서로 실행한다.

Reason: HanTalk 프로젝트의 규칙 프로세스는 후보를 넓게 생성한 뒤 확실한 오탐만 제거하는 구조를 따른다. 따라서 `stage=detect` 규칙은 recall을 우선하여 후보를 생성하고, `stage=verify` 규칙은 후보 생성에는 사용하지 않으며 100% 확실한 경우에만 hard_fail로 후보를 제거한다. 같은 `stage` 안에서는 `priority`가 작은 규칙부터 실행하고, 한 행은 하나의 규칙으로 취급한다.

### Decision: `detect_rules.target` 허용값은 `stage`별로 제한한다.

Reason: 후보 생성 단계와 검증 단계의 검색 범위가 다르므로 `target` 허용값을 명확히 제한한다. `stage=detect`는 전체 문장에서 후보를 넓게 찾는 단계이므로 `target=raw_sentence`만 허용한다. `stage=verify`는 이미 생성된 후보를 검증하는 단계이므로 전체 문장 기준 검증을 위한 `raw_sentence`와 후보 주변 문자 창 기준 검증을 위한 `char_window`를 허용한다.

### Decision: 이전 프로젝트의 `token_window` 명칭을 `char_window`로 바꾼다.

Reason: 기존 코드에서 `token_window`는 실제 토큰 단위 window가 아니라 후보 span 주변의 문자 단위 window로 동작했다. 이름과 동작이 어긋나면 새 규칙 모듈과 `dict.xlsx` 관리 과정에서 혼동이 생기므로, HanTalk 규칙 모듈을 따로 만들 때 `token_window` 명칭을 `char_window`로 바꾼다. 현재는 기록만 남기고 코드 변경은 나중에 수행한다.

### Decision: `detect_rules.confidence_delta`를 제거한다.

Reason: 이전 프로젝트에서는 규칙별 점수 조정을 위해 `confidence_delta`를 사용했지만, HanTalk 규칙 모듈에서는 후보 생성과 확실한 오탐 제거를 분리한다. `stage=detect`는 후보를 넓게 생성하고, `stage=verify`는 점수 조정 없이 100% 확실한 경우에만 hard_fail을 적용한다. 따라서 사람이 관리하는 `dict.xlsx`의 `detect_rules` 시트에서 `confidence_delta`를 제거한다.

### Decision: HanTalk은 대화 주제 조건에 따라 LLM이 대화를 주도할 수 있게 설계한다.

Reason: HanTalk은 단순한 문법항목 검출기가 아니라 한국어 대화형 학습기이다. 따라서 문법항목 기반 난이도 제어와 학습자 발화 진단뿐 아니라, 대화 주제 조건에 맞춰 LLM이 대화를 자연스럽게 이끌 수 있어야 한다. 이를 위해 RAG를 포함해 가장 적합한 구현 방식을 탐색하고 활용한다.

### Decision: 응답 속도에 영향을 주는 요소는 빠른 방식으로 실현한다.

Reason: HanTalk의 핵심 경험은 끊기지 않는 대화이다. 실제 학습자가 사용할 수 있으려면 문법항목 진단, 피드백, 연습 생성, 대화 주도 기능이 응답 지연을 크게 만들지 않아야 한다. 따라서 정확도를 높이더라도 실시간 대화 흐름을 해칠 가능성이 있는 요소는 빠른 방식으로 구현하거나 비동기/패널형 제시 등으로 분리한다.

### Decision: 정규식 gold 원본은 `gold.xlsx`로 관리하고 item별 JSONL은 자동 생성한다.

Reason: 300개 문법항목의 gold 예문을 사람이 관리하려면 Excel 원본이 필요하다. 따라서 정규식 gold의 원본은 `datasets/gold/gold.xlsx`로 두고, `exported_gold/{item_id}_gold_50.jsonl`은 `gold.xlsx`에서 자동 생성되는 검증용 산출물로 둔다. item별 JSONL은 앱 응답속도 목적이 아니라 특정 문법항목 정규식 테스트, Git diff, 자동화 재현성, 병렬 처리 편의를 위한 파일이다.

### Decision: 로컬 폴더는 Git 포함 워킹폴더와 Git 제외 작업 폴더로 분리한다.

Reason: 장기 프로젝트에서 코드/문서, 실행 artifact, 비공개 또는 대용량 작업 데이터를 섞으면 Git 공개 범위와 재현 경로가 흔들릴 수 있다. 따라서 규칙/예문 반자동화의 메인 워킹 폴더는 `/Users/yonghyunnam/coding/HanTalk_group/HanTalk/rule_example_auto`로 두고 Git에 포함한다. 실행 결과와 큰 artifact는 `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti`, 비공개/대용량 작업 데이터는 `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_work`에 두며 두 폴더는 Git에 올리지 않는다.

### Decision: `gold.xlsx`에서 생성한 item별 gold JSONL 폴더명은 `exported_gold`로 한다.

Reason: `gold.xlsx`가 사람이 관리하는 원본이고 item별 JSONL은 자동 변환 산출물이므로, 원본처럼 보이는 `gold/`보다 `exported_gold/`가 역할을 더 명확히 드러낸다.

### Decision: 기본 작업 흐름은 `로컬 작업 → GitHub main push → Colab pull`로 한다.

Reason: Colab과 로컬에서 동시에 코드를 수정하면 파일 버전이 쉽게 갈라지고, 장기 프로젝트의 기준 문서와 실행 코드가 어긋날 수 있다. 따라서 코드와 기준 문서는 로컬 컴퓨터에서 수정하고, GitHub `main`에 push한 뒤 Colab에서는 pull하여 실행/검증한다. Phase 1에서는 브랜치 관리 비용을 줄이기 위해 `main` 중심 운영을 허용하되, 필요한 경우 Git commit history로 이전 버전을 확인하거나 되돌린다.

### Decision: 말뭉치 FP를 보며 gold recall=1 조건에서 정규식을 개선한다.

Reason: 정규식 gold 50개에서 recall=1을 달성해도 실제 일반 말뭉치에서는 정규식이 너무 넓어 FP가 많이 생길 수 있다. 따라서 gold recall=1을 만족한 뒤에도 뉴스 말뭉치와 일상 대화 말뭉치를 각각 5,000행 단위로 검색하고, 사람이 검수한 FP 유형을 바탕으로 정규식을 더 좁힌다. 단, 수정된 정규식은 반드시 gold recall=1을 유지해야 하며, LLM의 TP/FP 판단은 임시 참고로만 사용하고 최종 라벨과 span은 사람이 확정한다.

### Decision: 브릿지는 비교 실험 후 채택한다.

Reason: 넓은 표면 정규식은 gold recall=1을 확보하기 쉽지만 일반 말뭉치에서 FP를 늘릴 수 있고, FP가 늘어나면 후단 인코더 처리량과 실시간 응답 지연이 커질 수 있다. 반대로 브릿지를 무조건 넣으면 규칙 복잡도가 커지고 새로운 FN 위험이 생길 수 있다. 따라서 먼저 넓은 정규식으로 gold recall=1을 확보한 뒤, 브릿지 후보를 붙인 버전을 별도로 만들고 gold recall=1 유지 여부를 확인한다. 이후 5,000행 말뭉치에서 FP 감소량을 비교하여 FP 감소 효과가 있거나 span 경계가 좋아지면 채택하고, 효과가 작고 복잡도만 늘면 보류한다.

### Decision: 형태소 분석 결과는 필요한 규칙들이 공유하는 cache 구조를 검토한다.

Reason: 브릿지를 위해 형태소 분석을 규칙마다 반복하면 300개 문법항목 확장과 실시간 대화 응답속도에 부담이 될 수 있다. 따라서 장기적으로는 문장 단위 형태소 분석 결과를 token/span/cache로 만들고 필요한 규칙들이 공유하는 구조를 검토한다. 다만 모든 300개 규칙이 항상 공유해야 한다는 뜻은 아니며, 학습 단계나 목표 난이도에 따라 필요한 규칙만 공유할 수 있다. Kiwi는 후보 중 하나일 뿐이므로, 상업 라이선스, 속도, 정확도, 배포 조건을 조사하고 다른 형태소 분석기 사용 가능성도 비교한다. 이 문제는 HanTalk 본 시스템 설계 단계에서 반드시 다시 검토한다.

### Decision: 문법항목 명칭은 필수 구성성분 중심으로 기록한다.

Reason: 항목명에 `있다`, `없다`, `있어요`, `없는` 같은 활용형까지 넣으면 300개 문법항목 확장 과정에서 이름과 실제 detect 기준이 흔들릴 수 있다. 따라서 canonical name과 config name은 필수 구성성분 중심으로 기록하고, 활용형은 alias, include criteria, gold 예문, detect rule에서 다룬다. df003의 공식 명칭은 `ㄴ/은 적 있/없`으로 통일한다.

### Decision: `dict.xlsx`는 사람이 관리하는 SSOT이고 runtime은 detector bundle을 사용한다.

Reason: Excel은 사람이 문법항목, 구성요소, 탐지 규칙을 관리하기에는 적합하지만 HanTalk 실시간 사용자 발화 detect 경로에서 반복해서 읽기에는 느리고 불필요하다. 따라서 `datasets/dict/dict.xlsx`를 사람이 관리하는 SSOT로 두고, runtime detector는 자동 생성된 `configs/detector/detector_bundle.json`을 읽는다. DetectorEngine은 bundle을 로딩한 뒤 정규식을 compile/cache하여 사용한다.

### Decision: detector output의 canonical span 표현은 `span_segments`로 한다.

Reason: 한국어 문법항목에는 df003 `ㄴ/은 적 있/없`처럼 불연속 span이 필요한 항목이 있다. 단일 `span_start`, `span_end`만 사용하면 불연속 구성요소를 안정적으로 보존할 수 없으므로 detector output에서는 Python 0-based `[start, end)` segment 목록인 `span_segments`를 canonical span 표현으로 사용한다. `aliases`, `route`, `relation_type`은 Phase 1 detector output에 넣지 않는다.

### Decision: 1차 DetectorEngine의 span은 `regex_match`이며 교육적 최종 span이 아니다.

Reason: 이번 1차 구현은 `dict.xlsx` 기반 runtime bundle과 최소 DetectorEngine을 붙여 gold 문장에서 후보를 빠짐없이 찾는지 검증하는 단계이다. 아직 component 기반 span 조립을 구현하지 않았으므로, candidate에는 `span_source=regex_match`, `component_span_enabled=false`를 기록한다. 예를 들어 df003의 1차 span이 `적이 있`으로 나와도 이는 최종 교육적 span인 `본 적 ... 있`이 완성되었다는 뜻이 아니다.

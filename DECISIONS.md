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

Note: df003의 `adnominal_n`은 이후 공용 component bridge 방식으로 채택되었다. 이후 항목에서도 브릿지는 정규식 복붙보다 `rule_components.bridge_id`를 우선 검토하되, gold recall과 말뭉치 FP 감소량을 확인한다.

### Decision: 형태소 분석 결과는 필요한 규칙들이 공유하는 cache 구조를 검토한다.

Reason: 브릿지를 위해 형태소 분석을 규칙마다 반복하면 300개 문법항목 확장과 실시간 대화 응답속도에 부담이 될 수 있다. 따라서 장기적으로는 문장 단위 형태소 분석 결과를 token/span/cache로 만들고 필요한 규칙들이 공유하는 구조를 검토한다. 다만 모든 300개 규칙이 항상 공유해야 한다는 뜻은 아니며, 학습 단계나 목표 난이도에 따라 필요한 규칙만 공유할 수 있다. Kiwi는 후보 중 하나일 뿐이므로, 상업 라이선스, 속도, 정확도, 배포 조건을 조사하고 다른 형태소 분석기 사용 가능성도 비교한다. 이 문제는 HanTalk 본 시스템 설계 단계에서 반드시 다시 검토한다.

### Decision: 문법항목 명칭은 필수 구성성분 중심으로 기록한다.

Reason: 항목명에 `있다`, `없다`, `있어요`, `없는` 같은 활용형까지 넣으면 300개 문법항목 확장 과정에서 이름과 실제 detect 기준이 흔들릴 수 있다. 따라서 canonical name과 config name은 필수 구성성분 중심으로 기록하고, 활용형은 alias, include criteria, gold 예문, detect rule에서 다룬다. df003의 공식 명칭은 `ㄴ/은 적 있/없`으로 통일한다.

### Decision: `dict.xlsx`는 사람이 관리하는 SSOT이고 runtime은 detector bundle을 사용한다.

Reason: Excel은 사람이 문법항목, 구성요소, 탐지 규칙을 관리하기에는 적합하지만 HanTalk 실시간 사용자 발화 detect 경로에서 반복해서 읽기에는 느리고 불필요하다. 따라서 `datasets/dict/dict.xlsx`를 사람이 관리하는 SSOT로 두고, runtime detector는 자동 생성된 `configs/detector/detector_bundle.json`을 읽는다. DetectorEngine은 bundle을 로딩한 뒤 정규식을 compile/cache하여 사용한다.

### Decision: detector output의 canonical span 표현은 `span_segments`로 한다.

Reason: 한국어 문법항목에는 df003 `ㄴ/은 적 있/없`처럼 불연속 span이 필요한 항목이 있다. 단일 `span_start`, `span_end`만 사용하면 불연속 구성요소를 안정적으로 보존할 수 없으므로 detector output에서는 Python 0-based `[start, end)` segment 목록인 `span_segments`를 canonical span 표현으로 사용한다. `aliases`, `route`, `relation_type`은 Phase 1 detector output에 넣지 않는다.

### Superseded Decision: 1차 DetectorEngine의 span은 `regex_match`이며 교육적 최종 span이 아니다.

Reason: 이번 1차 구현은 `dict.xlsx` 기반 runtime bundle과 최소 DetectorEngine을 붙여 gold 문장에서 후보를 빠짐없이 찾는지 검증하는 단계이다. 아직 component 기반 span 조립을 구현하지 않았으므로, candidate에는 `span_source=regex_match`, `component_span_enabled=false`를 기록한다. 예를 들어 df003의 1차 span이 `적이 있`으로 나와도 이는 최종 교육적 span인 `본 적 ... 있`이 완성되었다는 뜻이 아니다.

Status: 이 결정은 이후 `브릿지는 공용 registry로 관리하고 component span 조립은 별도 모듈로 분리한다` 결정으로 대체되었다. 현재 df003은 component span 조립이 성공하면 `span_source=component_spans`를 사용하고, 실패할 때만 `regex_match_fallback`을 사용한다.

### Decision: DetectorEngine은 명시된 active unit만 실행한다.

Reason: `active_unit_ids`가 비어 있을 때 모든 runtime unit을 자동 실행하면 300개 문법항목 확장 단계에서 응답속도와 디버깅 안정성이 크게 흔들릴 수 있다. 따라서 Phase 1 DetectorEngine은 `active_unit_ids`를 필수로 요구하고, 전체 실행은 `allow_all=True`를 명시한 경우에만 허용한다. `group=c` polyset unit은 의미별 verify 정책이 아직 확정되지 않았으므로 `allow_experimental_polyset=True`가 없으면 실행하지 않는다.

### Decision: bundle export validation은 조용한 오작동보다 빠른 실패를 우선한다.

Reason: 300개 문법항목을 Excel로 관리하면 e_id 오타, 잘못된 ruleset 연결, header 밀림 같은 문제가 반드시 생길 수 있다. 따라서 `detect_rules.e_id`와 `rule_components.e_id`가 `items.e_id`에 없거나, detect/verify ruleset의 stage가 맞지 않거나, regex compile이 실패하면 bundle export를 중단한다. warning은 pattern literal 의심처럼 사람이 확인할 수 있지만 runtime을 즉시 깨뜨리지는 않는 경우로 제한한다.

### Decision: 브릿지는 공용 registry로 관리하고 component span 조립은 별도 모듈로 분리한다.

Reason: 관형형 브릿지나 `것` 브릿지처럼 여러 문법항목에서 반복될 로직을 각 문법항목 정규식에 복붙하면 300개 항목 확장 단계에서 유지보수가 깨질 수 있다. 따라서 `rule_components.bridge_id`를 optional 열로 두고, `src/detector/bridges.py`의 공용 matcher를 참조한다. DetectorEngine은 직접 브릿지 로직을 갖지 않고, `src/detector/component_locator.py`가 detect regex match 주변의 제한된 문자 window 안에서 component span을 조립한다. 조립 실패 시 후보는 버리지 않고 `regex_match_fallback`으로 유지하여 gold recall을 보호한다.

### Decision: df003 c1 `ㄴ/은`에는 `adnominal_n` bridge를 사용한다.

Reason: df003 `ㄴ/은 적 있/없`은 `본 적`, `간 적`, `한 적`처럼 관형사형 표지가 독립 문자열이 아니라 앞 음절의 종성 ㄴ으로 실현되는 경우가 많다. 따라서 `dict.xlsx`의 `rule_components` 시트에 optional `bridge_id` 열을 추가하고, df003 c1에 `adnominal_n`을 지정한다. 이 bridge는 Kiwi 없이 문자 기반으로 시작하여 응답속도 부담을 줄이고, 필요하면 향후 형태소 분석 cache 기반으로 고도화한다.

### Decision: Kiwi는 기본 detector 경로에서 제외하고 필요한 항목에서만 예외적으로 검토한다.

Reason: df003 `ㄴ/은 적 있/없` pilot에서 문자 기반 `adnominal_n` bridge만으로 gold 50개 기준 `gold_recall=1.0`, `span_exact_recall=1.0`, `component_span_success_count=50`을 달성했다. HanTalk의 핵심 경험은 끊기지 않는 대화이므로, 기본 runtime detector에서 Kiwi를 매번 호출하면 응답속도 위험이 커질 수 있다. 따라서 기본 경로는 regex/component/문자 기반 bridge로 두고, Kiwi나 다른 형태소 분석기는 문자 기반 방식으로 안정적인 span 조립이나 FP/FN 개선이 어려운 항목에서만 예외적으로 검토한다.

### Decision: component order는 `fx` 고정 순서를 기본으로 하고, `fl`은 인접 교환만 허용한다.

Reason: component span 조립에서 모든 순열을 허용하면 300개 문법항목 확장 단계에서 path 수가 폭증하고 응답속도가 흔들릴 수 있다. 따라서 `comp_order`를 기본 순서로 사용하고, `order_policy=fx`는 순서를 반드시 고정한다. `order_policy=fl`은 인접한 `fl` component끼리만 제한적으로 순서 뒤바뀜을 허용한다. anchor component는 `anchor_rank`가 가장 큰 component로 보고 항상 기본 위치에 고정한다.

### Decision: 예문 구축용 말뭉치는 공통 prepared corpus batch로 만든다.

Reason: 300개 문법항목을 item별로 서로 다른 말뭉치 batch에서 검색하면 hit 수와 FP 유형을 비교하기 어렵다. 따라서 일상대화, 뉴스, 비출판물, 학습자 말뭉치를 정해진 비율로 sampling한 공통 prepared corpus JSONL을 만들고, 각 문법항목의 `DetectorEngine` 검색은 이 공통 batch 위에서 실행한다. 초기 batch_000/001 비율은 일상대화 5,000행, 뉴스 2,000행, 비출판물 2,000행, 학습자 말뭉치 1,000행이었다. 이후 batch_002부터의 비율은 2026-05-02 결정으로 조정되었다.

### Decision: prepared corpus sampling은 stable hash streaming 방식으로 한다.

Reason: 신문 말뭉치처럼 수백만 행 규모의 입력 파일을 전체 메모리에 올려 shuffle하는 방식은 장기적으로 불안정하다. 따라서 각 행에 대해 seed, domain, source file, source line number, raw text 기반 SHA-256 hash를 계산하고, domain별로 필요한 hash 구간만 streaming으로 유지한다. 같은 seed와 batch_index를 사용하면 같은 prepared JSONL이 재생성되어야 하며, `batch_index`를 바꾸면 다음 hash 구간의 batch를 만들 수 있다.

### Decision: 특정 component 바로 오른쪽 검증은 `component_right_context` target으로 처리한다.

Reason: df003에서 `char_window` 전체에 `적\s*(?:으로|인|일|에)` hard fail을 적용하자 후보 span과 무관한 주변 `자주적으로`, `직접적으로`, `긍정적인`이 잡혀 gold recall이 0.92로 떨어졌다. 따라서 component 기반 후보에서는 특정 component의 오른쪽 context만 검증하는 `component_right_context`를 도입한다. 이 target은 `component_id`를 필수로 요구하며, 해당 component span을 찾지 못하면 recall 보호를 위해 verify rule을 적용하지 않는다.

### Decision: partial component span은 보조 정보로만 사용한다.

Reason: component 일부만 찾은 후보에서 partial span을 canonical `span_segments`로 승격하면, 사람이 보거나 encoder 후보로 export할 때 완전한 문법항목 span처럼 오해될 수 있다. 따라서 full component path가 성공한 경우에만 `span_source=component_spans`를 사용하고, 실패한 경우에는 canonical span을 `regex_match_fallback`으로 유지한다. 대신 `partial_component_spans`, `partial_span_segments`, `partial_span_text`, `matched_component_ids`, `missing_required_component_ids`를 검수와 오류 분석, component 단위 verify rule 보조 정보로 기록한다.

### Decision: DetectorEngine 실행 모드는 `offline`과 `realtime` 두 가지만 둔다.

Reason: gold 평가, corpus search, audit, 예문 구축은 detector core 입장에서는 모두 속도보다 분석 정보와 재현성이 중요한 비실시간 작업이다. 따라서 별도 mode를 여러 개 만들지 않고 기본 `offline` 동작으로 묶는다. 실제 사용자 발화 처리만 `realtime`으로 구분하며, realtime에서는 `regex_match_fallback` 후보와 rejected/partial/debug 보조 정보를 최종 출력에서 숨겨 응답속도와 사용자 노출 안정성을 우선한다.

## 2026-05-02

### Decision: batch_002부터 예문 구축용 prepared corpus 비율을 조정한다.

Reason: df003 batch_001 검색 결과에서 후보 출처가 일상대화 59, 뉴스 89, 비출판물 29, 학습자 말뭉치 5로 나타나 뉴스 후보가 상대적으로 많고 학습자 말뭉치 후보가 적었다. 또한 뉴스 말뭉치 문장은 다른 말뭉치 문장보다 대체로 2~3배 길고, 학습자 말뭉치 문장은 짧기 때문에 문장 수를 단순히 `5:2:2:1`로 두면 실제 텍스트량과 학습자 발화 비중이 의도한 비율에서 벗어날 수 있다. HanTalk은 실제 대화형 한국어 학습기이므로 학습자 말뭉치와 비출판물의 비중을 높이고 뉴스 비중을 낮춘다. batch_002부터 공통 prepared corpus는 일상대화 5,000행, 뉴스 700행, 비출판물 2,000행, 학습자 말뭉치 2,500행으로 만든다. batch_000/001은 이전 비율인 일상대화 5,000행, 뉴스 2,000행, 비출판물 2,000행, 학습자 말뭉치 1,000행으로 생성된 산출물이므로 그대로 보존한다.

### Decision: prepared corpus manifest는 sampling schedule과 rank offset을 지원한다.

Reason: batch_000/001을 이전 비율로 만든 뒤 batch_002부터 비율을 바꾸면, 단순히 새 sample size와 같은 `batch_index` 계산을 적용할 때 일부 domain에서 hash rank 구간이 겹치거나 건너뛰어질 수 있다. 따라서 `configs/corpus/example_making_manifest.json`에 `sampling_schedules`와 `rank_start_offsets`를 두어 이전 비율로 이미 사용한 domain별 hash rank를 건너뛰고, 새 비율 batch를 중복 없이 이어서 생성한다.

### Decision: 2024년 신문 말뭉치는 5개 JSON 기반 축소 통합 파일을 사용한다.

Reason: 기존 2024년 신문 통합 파일은 행 수가 매우 커서 prepared corpus 생성 속도를 떨어뜨렸다. df003 이후 반복 batch를 빠르게 돌리기 위해 `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_work/corpus/example_making/news_paper(2024)` 안의 5개 JSON 파일만 사용해 `신문말뭉치(2024).txt`를 다시 생성한다. 이 축소본은 `form;source` 형식이며 header 제외 1,215,885행이다.

### Decision: 예문 구축 검색 산출물은 item별 artifact 폴더에 저장한다.

Reason: 300개 문법항목으로 확장하면 `HanTalk_arti/example_making` 한 폴더에 모든 detection JSONL, human review CSV/XLSX, summary JSON이 섞여 관리가 어려워진다. 공통 prepared corpus는 여러 문법항목이 공유해야 하므로 `HanTalk_work/corpus/example_making/prepared`에 그대로 두고, 문법항목별 검색 산출물은 `HanTalk_arti/example_making/{item_id}/` 아래에 저장한다. `src/search_corpus.py`와 `src/summarize_review.py`는 `--artifact-root .../example_making`을 받으면 item별 폴더와 파일명을 자동으로 파생한다.

## 2026-05-03

### Decision: 인코더 학습 예문은 Excel이 아니라 JSONL을 기계친화 SSOT로 둔다.

Reason: Excel은 사람이 검수하고 확인하기에는 좋지만, 학습 loop나 HanTalk 실시간 사용자 발화 처리 경로에서 읽기에는 느리고 구조가 흔들릴 수 있다. 따라서 `*_encoder_examples.xlsx`는 사람이 확인하는 gold-like 사본으로만 두고, 인코더 학습과 이후 runtime pair 입력 생성은 `*_encoder_pair_examples.jsonl`과 `configs/detector/detector_bundle.json`을 기준으로 한다. `text_b`는 `dict.xlsx`를 직접 읽지 않고 bundle의 `canonical_form`과 `gloss`에서 생성한다.

### Decision: HanTalk 인코더 예문 export에서는 `conf_e_id`, `neg_boundary`, `neg_confusable`를 사용하지 않는다.

Reason: 이번 HanTalk Phase 1의 df003은 다의의미 분별이 아니라 오탐 제거용 binary filtering task이다. 사람이 확정한 TP는 label 1, FP는 label 0의 `neg_target_absent`로 처리하고, FP 문장의 detector span을 그대로 보존한다. 이전 프로젝트의 confusable negative나 boundary negative는 새 예문 export 경로에 포함하지 않는다.

### Decision: 새 HanTalk span 문자열 표현은 JSON list 형식으로 통일한다.

Reason: `[(10,13),(15,16)]` 같은 Python literal 형식은 사람이 보기에는 익숙하지만 JSONL, 웹, 다른 언어, 자동 검증 코드와 연결할 때 불리하다. 따라서 새로 생성하는 HanTalk Excel/CSV cell의 `span_segments`는 `[[10,13],[15,16]]` 형식으로 쓰고, JSONL에서는 실제 list로 저장한다. parser는 과거 호환을 위해 Python tuple 형식도 읽지만 writer는 JSON list 형식만 출력한다.

### Decision: 인코더 예문 split은 `example_role`별 stable hash로 배정한다.

Reason: positive 전체와 negative 전체만 나누면 `pos_conti`, `pos_disconti`, `neg_target_absent`가 특정 split에 몰릴 수 있다. 따라서 `src.export_encoder_examples`는 role별로 stable hash 정렬을 한 뒤 train/dev/test를 배정한다. role count가 10개 미만이면 dev/test를 억지로 만들지 않고 train에 두며 warning을 남긴다.

### Decision: HanTalk binary encoder 학습 실행 파일은 pair-mode 완전판 v1로 만든다.

Reason: 이전 A그룹 프로젝트에서 성공한 구조는 span-marked sentence와 문법항목 설명을 pair input으로 넣고, encoder의 masked mean pooling 출력에 binary head를 붙여 BCEWithLogitsLoss로 학습하는 방식이었다. HanTalk에서도 이 검증된 구조를 유지하되, Excel을 학습 경로에서 제거하고 `*_encoder_pair_examples.jsonl`을 기계친화 SSOT로 사용한다. 학습 실행 파일 `src/train_encoder_pair.py`는 모델 backbone을 고정하지 않고 `AutoModel` 기반으로 받아 F1=1을 달성 가능한 모델 중 응답속도가 가장 빠른 모델을 찾을 수 있게 한다.

### Decision: encoder checkpoint artifact 명칭은 `head.pt`로 유지한다.

Reason: 이전 A그룹 프로젝트와 추론 설명에서 binary classifier layer를 head로 불렀고, inference에서도 head logits를 기준으로 오탐 여부를 판단했다. 따라서 내부 구현 클래스명이 classifier와 유사하더라도 artifact 파일명은 `head.pt`로 저장한다. 이렇게 하면 기존 성공 구조와 HanTalk runtime 로딩 규칙이 일관된다.

### Decision: Codex 1차 검토 파일은 자동 TP/FP 판정을 만들지 않는다.

Reason: Codex가 먼저 후보를 검토하더라도 최종 학습 데이터의 라벨은 사람이 확정해야 한다. 자동 heuristic이나 auto label suggestion이 검수자 판단을 오염시키면 인코더 학습 데이터 품질이 흔들릴 수 있다. 따라서 `src/prepare_codex_review.py`는 `codex_review_label`, `codex_review_span_status`, `codex_review_reason`, `codex_review_note`, `codex_checked` 같은 빈 검토 열과 기계적 span parse report만 만들고, 의미 기반 TP/FP suggestion은 생성하지 않는다. `hit_id`는 이후 Codex review, human labeled file, summary, encoder export를 연결하는 key이므로 필수로 둔다.

### Decision: encoder 학습 report에는 truncation과 end-to-end speed 측정을 반드시 기록한다.

Reason: HanTalk의 목표는 응답속도가 빠른 범위에서 성능을 올리는 것이다. pair input에서 `[SPAN]...[/SPAN]` marker나 핵심 span이 max length 때문에 잘리면 모델 성능이 흔들릴 수 있으므로 split별 truncation 통계를 저장한다. 또한 모델 비교의 기준이 성능뿐 아니라 응답속도이므로 `avg_inference_example_sec`를 기록하되, 초기 측정은 tokenization, collator, DataLoader overhead를 포함한 end-to-end eval latency임을 report에 명시한다.

### Decision: 문법항목별 TP/FP 수집은 `target_pos=100`, `target_neg=100`, `max_batches=5`를 기본 정책으로 한다.

Reason: `다면`처럼 FP가 거의 없는 문법항목에서 무한히 batch를 추가하면 작업량이 커지고, 오히려 해당 항목에 오탐 필터 인코더가 필요한지 판단이 늦어진다. 따라서 기본 목표는 TP 100개와 FP 100개로 두되, 최대 5개 labeled batch까지만 수집한다. 5 batch 후에도 한쪽이 부족하면 무한 검색하지 않고 현재 확보량으로 encoder 필요성, 추가 말뭉치 전략, 또는 학습 방식 조정을 재판단한다.

### Decision: encoder example export 단계에서는 TP/FP downsampling을 적용하지 않는다.

Reason: 사람이 확정한 TP/FP pool은 나중에 학습 전략을 바꿀 때 다시 사용할 수 있는 원본 자료이다. export 단계에서 미리 downsampling하면 복구가 어렵고, 실제 모델 학습에서 불균형이 문제인지도 확인하기 어렵다. 따라서 `*_encoder_pair_examples.jsonl`에는 valid TP/FP를 모두 보존하고, class balancing은 실제 학습 결과를 본 뒤 `loss_pos_weight`, sampler, train subset sampling 등으로 별도 판단한다.

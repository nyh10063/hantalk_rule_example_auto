# Current Task

## 현재 상태

- Current phase: Phase 1 pilot
- Current item: df003 `ㄴ/은 적 있/없`
- Current project goal: 300개 문법항목의 검색용 정규식 및 오탐 필터링 인코더용 positive/negative 예문 구축 자동화
- Current immediate goal: df003 batch_000 + batch_002 labeled review로 인코더 학습용 TP/FP 예문 export를 완료했으므로, 다음은 encoder pair JSONL validate-only 확인 뒤 실제 encoder backbone 학습 비교로 넘어가기

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
- `configs/grammar_items.yaml` 초안 작성 완료. 단, 현재 장기 SSOT는 `dict.xlsx`/`gold.xlsx`이며 YAML은 보조 config로만 취급함
- `exported_gold/df003_gold_50.jsonl` 형식 확정 및 50개 positive gold 변환 완료
- 정규식 gold의 장기 원본은 `datasets/gold/gold.xlsx`로 관리하고, item별 JSONL은 자동 생성 산출물로 두기로 문서화함
- `PROJECT_SPEC.md`의 df003 gold schema를 실제 JSONL 형식에 맞게 업데이트함
- `regex/df003_versions.jsonl`에 df003 v1 정규식을 추가함
- `regex/df003_versions.jsonl`에 df003 v2 bridge candidate 정규식을 추가함
- df003 문법항목 명칭을 필수 구성성분 중심인 `ㄴ/은 적 있/없`으로 정리함
- `src/test_gold.py` 구현 완료
- df003 v1 정규식의 gold 50개 기준 recall이 1.0임을 확인함
- df003 v2 bridge candidate 정규식의 gold 50개 기준 recall이 1.0임을 확인함
- `src/detector/export_bundle.py` 구현 완료
- `src/detector/engine.py` DetectorEngine 기반 구현 완료
- `src/detector/span_utils.py` 구현 완료
- `configs/detector/detector_bundle.json` 생성 완료
- `src/test_gold.py`에 DetectorEngine bundle 평가 경로 추가 완료
- df003 bundle 경로의 gold 50개 기준 sentence recall과 span overlap recall이 1.0임을 확인함
- `export_bundle.py` validation 강화 완료
- DetectorEngine의 `active_unit_ids` 필수화, group=c polyset 기본 실행 차단, `max_matches_per_rule` 제한 추가 완료
- `src/detector/bridges.py` 추가 완료
- `src/detector/component_locator.py` 추가 완료
- component 탐색 폭주 방지를 위해 `max_candidates_per_component`, `max_component_paths` 제한 추가 완료
- `order_policy=fx/fl`를 component path 선택에 반영 완료
- `rule_components.bridge_id` optional 지원 추가 완료
- `dict.xlsx`의 `rule_components` 시트에 `bridge_id` 열을 추가하고 df003 c1에 `adnominal_n` 연결 완료
- DetectorEngine candidate에 `origin_e_id`, `regex_match_span`, `regex_match_text`, `component_span_status`, `component_spans`, `applied_bridge_ids` 추가 완료
- df003 component span 조립 성공 시 `span_source=component_spans`, 실패 시 `span_source=regex_match_fallback`으로 유지하도록 구현 완료
- `PROJECT_SPEC.md`, `DECISIONS.md`, `CURRENT_TASK.md`에서 dict/bundle/component span 중심의 현재 방향과 어긋나는 옛 표현을 정리함
- detector의 불연속 span 표시용 gap marker를 `DEFAULT_GAP_MARKER = " ... "`로 상수화하고, `span_utils.py`, `component_locator.py`, `engine.py`가 같은 값을 명시적으로 사용하도록 정리함
- DetectorEngine summary에 `n_component_span_success`, `n_component_span_fallback`, `n_component_span_regex_only`, `span_source_counts`, `span_source_counts_before_verify`를 추가함
- `src/test_gold.py` bundle 평가 report에 candidate-level `span_source_counts`를 추가함
- `dict.xlsx`의 `rule_components` 시트에서 중복된 `bridge_id` 헤더를 정리하고, `comp_id` 옆의 `bridge_id` 열 하나만 남김
- Kiwi는 기본 detector 경로에서 제외하고, 문자 기반 bridge로 해결하기 어려운 항목에서만 예외적으로 검토하기로 문서화함
- 일상대화말뭉치 2024년/2023년 JSON에서 `form`과 출처를 추출해 통합 작업 파일을 생성함:
  - `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_work/corpus/example_making/casual_dial/casual_dialogue_2023_2024_form_source.txt`
- 신문말뭉치 2024년 JSON에서 `form`을 추출하고 HTML 태그를 제거해 통합 작업 파일을 생성함:
  - `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_work/corpus/example_making/news_paper(2024)/news_paper_2024_form_source.txt`
- 비출판물말뭉치 SJML에서 `<text ...>`와 `</text>` 사이의 텍스트를 추출하고 문장 단위로 분리해 통합 작업 파일을 생성함:
  - `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_work/corpus/example_making/비출판물말뭉치/non_published_sentence_source.txt`
- 학습자말뭉치(구어 5~6급) 텍스트 파일의 각 문장에 출처를 붙여 통합 작업 파일을 생성함:
  - `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_work/corpus/example_making/learner_spoken_5_6_sentence_source.txt`
- 50개 정규식 gold 예문 후보 제작용 신문말뭉치 2022년 JSON에서 `form`을 추출하고 HTML 태그를 제거해 통합 작업 파일을 생성함:
  - `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_work/corpus/50sample_making/신문말뭉치(2022)/news_paper_2022_form_source.txt`
- 50개 정규식 gold 예문 후보 제작용 일상대화말뭉치 2022년 JSON에서 `form`을 추출해 통합 작업 파일을 생성함:
  - `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_work/corpus/50sample_making/일상대화말뭉치(2022)/casual_dialogue_2022_form_source.txt`
- `configs/corpus/example_making_manifest.json` 생성 완료
- `src/prepare_example_corpus.py` 구현 완료
  - 말뭉치 통합 파일을 `text;source` 계열로 읽음
  - header text 후보(`sentence`, `form`, `text`, `raw_text`)와 source 후보(`source`)를 우선 사용함
  - 데이터 line은 마지막 delimiter 기준 `rsplit(";", 1)`로 분리함
  - stable hash streaming sampling으로 공통 prepared corpus batch를 생성함
- `src/search_corpus.py` 구현 완료
  - prepared corpus JSONL을 읽고 DetectorEngine으로만 검색함
  - detection JSONL, 사람 검수용 CSV, search report JSON을 생성함
  - 여러 `--active-unit-id`를 받을 수 있게 구현함
  - `--artifact-root`를 주면 단일 `--active-unit-id` 기준으로 `example_making/{item_id}/` 아래 산출물 경로를 자동 생성함
  - 사람 검수용 CSV에 `llm_temp_label`, `llm_note` 빈 열을 추가함
  - 사람 검수용 CSV를 Excel 호환성을 위해 `utf-8-sig`로 저장하도록 수정함
  - 검수 편의를 위해 CSV 열 순서를 `raw_text`, `regex_match_text`, `human_label`이 붙어 보이도록 조정함
- batch_000/001 예문 구축용 batch 비율을 일상대화 5,000행, 뉴스 2,000행, 비출판물 2,000행, 학습자 말뭉치 1,000행으로 적용함
- 공통 prepared corpus batch 생성 완료:
  - `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_work/corpus/example_making/prepared/example_making_batch_000.jsonl`
  - `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_work/corpus/example_making/prepared/example_making_batch_000_report.json`
- df003 corpus search 산출물 생성 완료:
  - `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003_batch_000_detection.jsonl`
  - `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003_batch_000_human_review.csv`
  - `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003_batch_000_search_report.json`
- `dict.xlsx`에 df003 verify hard_fail rule `r_df003_v01`을 추가한 뒤 bundle을 다시 export하고 corpus search를 다시 실행함
- `r_df003_v01`은 `char_window` 방식에서 gold recall을 깨뜨렸으므로 `component_right_context` 방식으로 수정함
- `detect_rules` 시트에 optional `component_id` 열을 추가하고, df003 verify rule은 `component_id=c2`를 사용하도록 수정함
- `src/detector/export_bundle.py`가 `component_right_context`와 `component_id`를 읽고 검증하도록 수정함
- `src/detector/engine.py`가 candidate의 `component_spans[component_id]` 오른쪽 context만 hard fail 검증하도록 수정함
- 최신 df003 human review Excel 산출물을 생성함:
  - `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003_batch_000_human_review.xlsx`
- component span 조립 실패 시에도 부분 component 정보를 보조 필드로 남기도록 수정함
  - `partial_component_spans`
  - `partial_span_segments`
  - `partial_span_text`
  - `matched_component_ids`
  - `missing_required_component_ids`
- `component_right_context` verify가 full `component_spans`를 먼저 보고, 없으면 `partial_component_spans`를 참고하도록 수정함
- DetectorEngine에 `realtime` 실행 옵션을 추가함
  - 기본값 `realtime=False`는 gold 평가, corpus search, audit, 예문 구축용 offline 동작임
  - `realtime=True`에서는 `regex_match_fallback` 후보와 rejected/partial/debug 보조 정보를 최종 출력에서 숨김
- 사람 검수용 CSV에 partial component 보조 정보 열을 추가함
- partial component 기반 verify 적용 후 df003 corpus search 산출물을 다시 생성함
- 최신 df003 human review Excel 산출물을 다시 생성함:
  - `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003_batch_000_human_review.xlsx`
- 정규식 다듬기 및 예문 제작용 통합 말뭉치 root와 네 입력 파일명을 `PROJECT_SPEC.md`에 명시함
- `dict.xlsx`의 `detect_rules` 23행 df003 verify rule `r_df003_v01` pattern을 확장함
  - 이전: `^\s*(?:으로|인|일|에)`
  - 이후: `^\s*(?:으로|인|일|에|극|금|되|립|었|을|응|정|했|화)`
- batch_001 검색 전 detector bundle 재생성과 df003 gold test를 완료함
- batch_001 prepared corpus 생성 완료:
  - `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_work/corpus/example_making/prepared/example_making_batch_001.jsonl`
  - `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_work/corpus/example_making/prepared/example_making_batch_001_report.json`
- 확정된 df003 detector bundle로 batch_001 검색 완료:
  - `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003_batch_001_detection.jsonl`
  - `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003_batch_001_human_review.csv`
  - `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003_batch_001_search_report.json`
- `src/detector/span_utils.py`에 HanTalk span/parser writer 유틸을 추가함
  - `parse_span_segments`
  - `format_span_segments`
  - `inject_span_markers`
  - 새 출력은 `[[10,13],[15,16]]` JSON list 형식으로 통일하고, 기존 `[(10,13),(15,16)]` 형식도 읽을 수 있게 함
- `src/export_encoder_examples.py` 구현 완료
  - labeled review `.xlsx`/`.csv`를 읽어 인코더 pair-mode 학습 예문으로 변환함
  - `text_b`는 `dict.xlsx`가 아니라 `configs/detector/detector_bundle.json`의 `canonical_form`과 `gloss`에서 생성함
  - TP는 `label=1`, FP는 `label=0` 및 `example_role=neg_target_absent`로 변환함
  - `conf_e_id`, `neg_boundary`, `neg_confusable`는 새 export 경로에서 사용하지 않음
  - Excel 출력 열도 `gold_example_role`이 아니라 새 HanTalk key인 `example_role`을 사용함
  - `span_status=span_wrong`이고 `corrected_span_segments`가 있으면 corrected span을 우선 사용함
  - `example_id`는 `df003-pos-0001`, `df003-neg-0001` 같은 소문자 짧은 형식으로 생성함
  - `pos_conti`, `pos_disconti`, `neg_target_absent`별 stable hash split을 적용함
- df003 batch_000 labeled review 파일에서 인코더 예문 산출물을 생성함:
  - `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003/df003_encoder_examples.xlsx`
  - `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003/df003_encoder_pair_examples.jsonl`
  - `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003/df003_encoder_examples_summary.json`
- `src/train_encoder_pair.py` 구현 완료
  - `*_encoder_pair_examples.jsonl`만 읽고 Excel은 학습 경로에서 읽지 않음
  - `AutoModel + masked_mean/cls pooling + Linear head + BCEWithLogitsLoss` 구조를 사용함
  - checkpoint는 `encoder/`, `tokenizer/`, `head.pt`, `runtime_encoder_config.json`, `checkpoint_meta.json` 구조로 저장함
  - W&B는 `disabled/offline/online` 옵션을 지원하고 기본값은 `disabled`임
  - truncation 통계, speed metrics, debug predictions, data summary, metrics by epoch를 저장하도록 구현함
  - train만 seed 기반 shuffle을 사용하고 dev/test는 고정 순서로 평가함
- `src/train_encoder_pair.py` 운영 안전장치 보강 완료
  - 학습 경로에서 `seed_state`, tokenization, device, model info, optimizer info가 포함된 최종 `train_config.json`을 다시 저장함
  - CLI 값 범위 검증을 추가함
  - `input_construction_version=hantalk_binary_pair_v1` 검증을 fatal error로 추가함
  - `--max-saved-prediction-rows`로 prediction/debug 파일 저장 행 수를 제한할 수 있게 함
  - `--log-every-steps`로 step 단위 train loss를 `train_step_log.jsonl`과 W&B에 기록할 수 있게 함
- batch_002 검색 전 detector bundle 재생성과 df003 gold test를 완료함
- batch_002 prepared corpus 생성 완료:
  - `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_work/corpus/example_making/prepared/example_making_batch_002.jsonl`
  - `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_work/corpus/example_making/prepared/example_making_batch_002_report.json`
  - 구성: 일상대화 5,000행, 뉴스 700행, 비출판물 2,000행, 학습자 말뭉치 2,500행
- 확정된 df003 detector bundle로 batch_002 검색 완료:
  - `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003/df003_batch_002_detection.jsonl`
  - `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003/df003_batch_002_human_review.csv`
  - `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003/df003_batch_002_search_report.json`
  - 후보 수: 142개
  - 후보 출처: 일상대화 57개, 뉴스 46개, 비출판물 29개, 학습자 말뭉치 10개
- `src/prepare_codex_review.py` 구현 완료
  - `*_human_review.csv/xlsx`를 읽어 Codex 1차 검토용 `*_codex_review.csv`, `*_codex_review.xlsx`, `*_codex_review_report.json`을 생성함
  - 자동 TP/FP suggestion은 만들지 않고, Codex가 직접 채울 `codex_review_*` 열만 추가함
  - `hit_id`, `raw_text`, `span_segments`를 필수 열로 검증함
  - span parse, span boundary, overlap/ordering, `span_extracted_text`를 기계적으로 확인함
- df003 batch_002 Codex 1차 검토용 파일 생성 완료:
  - `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003/df003_batch_002_codex_review.csv`
  - `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003/df003_batch_002_codex_review.xlsx`
  - `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003/df003_batch_002_codex_review_report.json`
  - span parse 결과: `parsed=142`, `parse_error=0`, `out_of_bounds=0`, `overlap_or_unsorted=0`
- df003 batch_000 + batch_002 labeled review 누적 집계를 완료함
  - 사용 파일:
    - `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003/df003_batch_000_human_review_labeled.csv`
    - `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003/df003_batch_002_human_review_labeled.csv`
  - batch_001 labeled 파일은 없으므로 이번 누적 집계와 export에서 제외함
  - 누적 결과: `TP=130`, `FP=157`, `unclear=0`, `blank=0`, `invalid=0`
  - `positive_100=true`, `negative_100=true`
  - summary:
    - `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003/df003_review_summary.json`
- df003 인코더 학습용 예문 export를 batch_000 + batch_002 labeled review 기준으로 갱신함
  - export 결과: `n_rows_read=287`, `n_rows_exported=287`, `n_rows_skipped=0`, `deduped_count=0`
  - label counts: `positive=130`, `negative=157`
  - role counts: `pos_conti=32`, `pos_disconti=98`, `neg_target_absent=157`
  - split counts: `train=229`, `dev=29`, `test=29`
  - 생성 파일:
    - `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003/df003_encoder_examples.xlsx`
    - `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003/df003_encoder_pair_examples.jsonl`
    - `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003/df003_encoder_examples_summary.json`

## 이번에 테스트한 것

- 기존 `정규식 골드/정규식 골드_df003.xlsx`에서 positive gold가 50개인지 확인함
- 각 gold record의 `target_spans`가 sentence의 문자 구간에서 `target_text`로 추출되는지 확인함
- `df003_gold_50.jsonl`이 JSONL 50줄로 생성되도록 검증함
- `python3 -m py_compile src/test_gold.py`로 초기 문법 검사를 수행함
- `python3 src/test_gold.py --item-id df003 --regex-version v1` 실행 결과 `gold_total=50`, `gold_matched=50`, `gold_recall=1.0`, `fn_count=0`을 확인함
- `python3 src/test_gold.py --item-id df003 --regex-version v2_bridge_candidate --fail-on-fn` 실행 결과 `gold_total=50`, `gold_matched=50`, `gold_recall=1.0`, `fn_count=0`을 확인함
- `rg`로 긴 활용형 중심의 df003 명명 표현이 남아 있지 않음을 확인함
- `regex/df003_versions.jsonl` JSONL 파싱이 정상임을 확인함
- `python3 -m py_compile src/detector/bridges.py src/detector/component_locator.py src/detector/export_bundle.py src/detector/engine.py src/detector/span_utils.py src/test_gold.py` 통과
- `python3 -m src.detector.export_bundle --dict datasets/dict/dict.xlsx --out configs/detector/detector_bundle.json` 통과
- bundle export 결과: `items=9`, `runtime_units=5`, `warnings=0`
- df003 bundle 평가(sentence): `gold_total=50`, `gold_matched=50`, `gold_recall=1.0`, `span_overlap_recall=1.0`, `span_exact_recall=1.0`, `component_span_success_count=50`, `fn_count=0`
- df003 bundle 평가(overlap): `gold_total=50`, `gold_matched=50`, `gold_recall=1.0`, `span_overlap_recall=1.0`, `span_exact_recall=1.0`, `component_span_success_count=50`, `fn_count=0`
- 직접 detect 확인: `"저는 제주도에 가 본 적이 있어요."`에서 DetectorEngine은 `span_segments=[[10, 13], [15, 16]]`, `span_text="본 적 ... 있"`, `span_source="component_spans"`, `applied_bridge_ids=["adnominal_n"]`을 출력함
- `active_unit_ids` 없이 DetectorEngine을 실행하면 `ValueError: active_unit_ids is required unless allow_all=True`가 발생함을 확인함
- `ps_neunde` polyset unit을 기본 옵션으로 실행하면 `ValueError`가 발생함을 확인함
- 기준 문서에서 `configs/grammar_items.yaml`을 장기 SSOT처럼 보이게 하던 설명을 보조 config로 정리함
- 기준 문서에서 `span_start/span_end` 중심 corpus hit schema를 `span_segments` 중심 detection JSONL/review CSV schema로 교체함
- `order_policy=fx`는 고정 순서, `order_policy=fl`은 anchor 고정 + 인접 `fl`끼리만 교환하는 정책으로 기록함
- 합성 테스트에서 인접 `fl` component끼리는 순서 교환이 허용되고, anchor가 포함된 교환은 차단됨을 확인함
- df003은 `order_policy=fx`이므로 component order가 `c1 → c2 → c3` 하나로 유지됨을 debug 출력으로 확인함
- `python3 -m py_compile src/detector/span_utils.py src/detector/component_locator.py src/detector/engine.py src/test_gold.py` 통과
- gap marker 상수화 후 df003 bundle 평가에서 `gold_recall=1.0`, `span_exact_recall=1.0`, `fn_count=0` 유지 확인
- 직접 detect 확인에서 `span_text="본 적 ... 있"` 출력이 유지됨을 확인함
- `python3 -m src.detector.export_bundle --dict datasets/dict/dict.xlsx --out configs/detector/detector_bundle.json` 통과
- bundle export 결과: `items=9`, `runtime_units=5`, `warnings=0`, `df003 c1 bridge_id=adnominal_n`, `bridges_by_id.adnominal_n` 반영 확인
- df003 bundle 평가 출력에 `span_source_counts={"component_spans": 53, "regex_match_fallback": 1}`가 추가됨을 확인함
- 직접 detect summary에서 `n_component_span_success=1`, `n_component_span_fallback=0`, `n_component_span_regex_only=0` 출력 확인
- `git diff --check` 통과
- `PROJECT_SPEC.md`와 `DECISIONS.md`에 Kiwi 기본 제외 및 예외 검토 원칙을 기록함
- 일상대화말뭉치 통합 파일 생성 결과를 확인함:
  - 2024년: 728,257행
  - 2023년: 677,262행
  - 합계: 1,405,519행, 헤더 포함 전체 1,405,520줄
  - 형식: `form;source`
- 신문말뭉치 2024년 통합 파일 생성 결과를 확인함:
  - 총 5,390,096행, 헤더 포함 전체 5,390,097줄
  - 형식: `form;source`
  - `form` 안의 HTML 태그는 제거함
- 비출판물말뭉치 통합 파일 생성 결과를 확인함:
  - SJML 파일 10,753개 처리
  - 총 238,855행, 헤더 포함 전체 238,856줄
  - 형식: `sentence;source`
  - `<text ...>` 내부 텍스트를 대상으로 하고 SGML/HTML 태그는 제거함
- 학습자말뭉치(구어 5~6급) 통합 파일 생성 결과를 확인함:
  - 총 81,906행, 헤더 포함 전체 81,907줄
  - 형식: `sentence;source`
- 50개 정규식 gold 예문 후보 제작용 신문말뭉치 2022년 통합 파일 생성 결과를 확인함:
  - JSON 파일 9개 처리
  - 총 2,366,197행, 헤더 포함 전체 2,366,198줄
  - 형식: `form;source`
  - `form` 안의 HTML 태그는 제거함
- 50개 정규식 gold 예문 후보 제작용 일상대화말뭉치 2022년 통합 파일 생성 결과를 확인함:
  - JSON 파일 2,654개 처리
  - 총 866,359행, 헤더 포함 전체 866,360줄
  - 형식: `form;source`
- `python3 -m py_compile src/prepare_example_corpus.py src/search_corpus.py` 통과
- prepared corpus batch 생성 결과:
  - 총 10,000행
  - `daily_conversation=5000`
  - `news=2000`
  - `non_published=2000`
  - `learner_spoken_5_6=1000`
  - parse error 0
- 같은 seed와 batch_index로 `/private/tmp/example_making_batch_000_check.jsonl`을 다시 생성했을 때 SHA-256이 동일함을 확인함:
  - `35e459fd5697fb370f83f5afd7fae7985df29063682b72f6dd3f9fbfa9778afd`
- df003 corpus search 결과:
  - input texts: 10,000
  - texts with hits: 291
  - candidates: 307
  - candidates by domain: `daily_conversation=64`, `news=192`, `non_published=47`, `learner_spoken_5_6=4`
  - span source counts: `component_spans=119`, `regex_match_fallback=188`
  - elapsed: 약 0.13초
- `df003_batch_000_human_review.csv`에 307개 후보 행이 생성되고, 사람이 채울 `human_label`, `span_status`, `memo`, `reviewer` 열이 포함됨을 확인함
- `/private/tmp/hantalk_sample_20_review.csv` 샘플 실행으로 review CSV가 UTF-8 BOM(`b'\xef\xbb\xbf'`)을 포함하고, `llm_temp_label`, `llm_note` header가 들어감을 확인함
- `/private/tmp/hantalk_sample_20_review_order.csv` 샘플 실행으로 `raw_text`, `regex_match_text`, `human_label` 열이 연속 배치됨을 확인함
- df003 `char_window` verify hard_fail rule 추가 후 corpus search 결과:
  - input texts: 10,000
  - texts with hits: 155
  - candidates: 161
  - candidates by domain: `daily_conversation=51`, `news=84`, `non_published=24`, `learner_spoken_5_6=2`
  - span source counts: `component_spans=62`, `regex_match_fallback=99`
  - hard_failed candidates: 146
- 당시 `df003_batch_000_human_review.xlsx`는 162행(header 포함), 35열로 생성됨을 확인함
- 단, 최신 bundle gold test에서 `gold_recall=0.92`, `fn_count=4`가 발생함을 확인함. 원인은 `r_df003_v01`의 `적\s*(?:으로|인|일|에)` hard_fail이 candidate 주변 `char_window` 안의 다른 `적으로/적인`까지 잡아 gold TP 후보를 제거하기 때문임
- df003 `component_right_context` verify hard_fail rule 수정 후 gold test 결과:
  - `gold_total=50`
  - `gold_matched=50`
  - `gold_recall=1.0`
  - `span_exact_recall=1.0`
  - `fn_count=0`
- df003 `component_right_context` verify hard_fail rule 수정 후 corpus search 결과:
  - input texts: 10,000
  - texts with hits: 281
  - candidates: 296
  - candidates by domain: `daily_conversation=64`, `news=185`, `non_published=43`, `learner_spoken_5_6=4`
  - span source counts: `component_spans=63`, `regex_match_fallback=233`
  - hard_failed candidates: 11
- 당시 `df003_batch_000_human_review.xlsx`는 297행(header 포함), 35열로 재생성됨을 확인함
- partial component 기반 `component_right_context` verify 적용 후 직접 detect 확인:
  - `"어떤 문화가 특징적인 문화가 있을까요?"`는 `partial_component_spans.c2` 기준으로 `r_df003_v01` hard fail 처리되어 최종 candidates에서 제거됨
  - 같은 문장을 `realtime=True`로 실행하면 rejected/partial 정보가 최종 output에서 숨겨짐
  - `"저는 제주도에 가 본 적이 있어요."`는 `realtime=True`에서도 `component_spans` 후보로 유지됨
- partial component 기반 verify 적용 후 df003 corpus search 결과:
  - input texts: 10,000
  - texts with hits: 173
  - candidates: 180
  - candidates by domain: `daily_conversation=51`, `news=100`, `non_published=27`, `learner_spoken_5_6=2`
  - span source counts: `component_spans=63`, `regex_match_fallback=117`
  - component span status counts: `ok=63`, `no_ordered_component_path=117`
  - hard_failed candidates: 127
- 최신 `df003_batch_000_human_review.csv` header에 partial 보조 열이 포함됨을 확인함
- 최신 `df003_batch_000_human_review.xlsx`는 181행(header 포함), 40열로 재생성됨을 확인함
- df003 verify rule pattern 확장 후 bundle export 결과 `warnings=0`을 확인함
- df003 verify rule pattern 확장 후 gold test 결과:
  - `gold_total=50`
  - `gold_matched=50`
  - `gold_recall=1.0`
  - `span_exact_recall=1.0`
  - `fn_count=0`
- 확장된 df003 verify rule로 corpus search와 `df003_batch_000_human_review.csv`를 다시 생성함
- 확장된 df003 verify rule 적용 후 corpus search 결과:
  - input texts: 10,000
  - texts with hits: 140
  - candidates: 145
  - candidates by domain: `daily_conversation=48`, `news=73`, `non_published=22`, `learner_spoken_5_6=2`
  - span source counts: `component_spans=63`, `regex_match_fallback=82`
  - hard_failed candidates: 162
  - review CSV는 40열 구조로 생성됨
- df003 batch_000 사람 검수 완료본을 공식 labeled 파일로 확정함:
  - `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003_batch_000_human_review_labeled.xlsx`
  - `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003_batch_000_human_review_labeled.csv`
- `/Users/yonghyunnam/Downloads/for_codex2`는 전달/임시 확인 폴더로만 사용하고, 자동화 기준 입력은 `HanTalk_arti/example_making` 아래 labeled 파일로 둠
- df003 batch_000 labeled 파일은 사람이 `human_label`에 전 행 `tp/fp`, `span_status`에 전 행 `ok`를 입력한 검수 완료본임
- batch_000 검수 결과는 현재 `TP 60`, `FP 85`로 보고, 더 이상 안전하게 FP를 줄이기보다 다음 batch 반복 수집으로 넘어감
- `src/summarize_review.py` 구현 완료
  - `--item-id`를 필수로 받음
  - `--artifact-root`를 주면 `{artifact_root}/{item_id}/{item_id}_review_summary.json` 경로를 자동 생성함
  - labeled `.xlsx`와 `.csv`를 모두 읽음
  - header 이름은 `strip()`하여 비교함
  - 필수 열은 `hit_id`, `human_label`, `span_status`
  - 빈 `hit_id`와 중복 `hit_id`는 error로 처리함
  - row의 `origin_e_id` 또는 `unit_id`가 `--item-id`와 모두 다르면 잘못된 labeled 파일로 보고 error 처리함
  - `origin_e_id`와 `unit_id`가 모두 없으면 item 검증을 건너뛰되 warning으로 남김
  - `human_label`을 `tp`, `fp`, `unclear`, `blank`, `invalid`로 정규화함
  - `span_status`를 `ok`, `span_wrong`, `not_applicable`, `blank`, `invalid`로 정규화함
  - `FP + span_status=ok`는 오류로 보지 않음
  - `corpus_domain`, `span_source`, `component_span_status`별 label count를 집계함
  - `positive_100`, `negative_100`, `next_action`을 계산함
  - invalid row count는 `n_invalid_rows_total`, `n_invalid_rows_listed`로 구분하여 기록함
- df003 batch_000 labeled xlsx/csv 집계 결과:
  - n_rows: 145
  - label_counts: `tp=60`, `fp=85`, `unclear=0`, `blank=0`, `invalid=0`
  - span_status_counts: `ok=145`, `invalid=0`
  - by_span_source: `component_spans(tp=60, fp=3)`, `regex_match_fallback(tp=0, fp=82)`
  - target_reached: `positive_100=false`, `negative_100=false`
  - next_action: `continue_batch_search`
  - item_id_validation: `n_missing_item_reference_rows=0`
  - warnings: `[]`
  - invalid row counts: `n_invalid_rows_total=0`, `n_invalid_rows_listed=0`
  - summary output:
    - `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003_review_summary.json`
- CSV 사본 입력도 같은 결과로 집계됨을 확인함:
  - `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003_batch_000_human_review_labeled.csv`
- 같은 batch의 xlsx와 csv를 동시에 `--input`으로 넣으면 중복 `hit_id` error가 발생함을 확인함
- `--item-id xx999`처럼 파일 내용과 다른 item ID를 넣으면 item mismatch error가 발생함을 확인함
- batch_001 실행 전 bundle export 결과:
  - `items=9`
  - `runtime_units=5`
  - `warnings=0`
- batch_001 실행 전 df003 gold test 결과:
  - `gold_total=50`
  - `gold_matched=50`
  - `gold_recall=1.0`
  - `span_exact_recall=1.0`
  - `component_span_success_count=50`
  - `component_span_fallback_count=0`
  - `fn_count=0`
- batch_001 prepared corpus 생성 결과:
  - 총 10,000행
  - `daily_conversation=5000`
  - `news=2000`
  - `non_published=2000`
  - `learner_spoken_5_6=1000`
- batch_001 df003 corpus search 결과:
  - input texts: 10,000
  - texts with hits: 178
  - candidates: 182
  - candidates by domain: `daily_conversation=59`, `news=89`, `non_published=29`, `learner_spoken_5_6=5`
  - span source counts: `component_spans=85`, `regex_match_fallback=97`
- `python3 -m py_compile src/detector/span_utils.py src/export_encoder_examples.py` 통과
- `/private/tmp` smoke export에서 `df003_batch_000_human_review_labeled.xlsx` 145행을 모두 인코더 예문으로 변환함:
  - positive: 60
  - negative: 85
  - role counts: `pos_conti=18`, `pos_disconti=42`, `neg_target_absent=85`
  - split counts: `train=117`, `dev=14`, `test=14`
  - JSONL에 `conf_e_id`가 없고 `span_segments`가 실제 list로 저장됨을 확인함
  - Excel sheet `examples`에 `conf_e_id`가 없고 `span_segments`가 `[[23,26],[28,29]]` 형식으로 저장됨을 확인함
  - 같은 seed/입력으로 JSONL을 재생성했을 때 SHA-256이 동일함을 확인함
- 실제 artifact 폴더에 df003 인코더 예문 산출물을 생성함:
  - `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003/df003_encoder_examples.xlsx`
  - `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003/df003_encoder_pair_examples.jsonl`
  - `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003/df003_encoder_examples_summary.json`
- `python3 -m py_compile src/train_encoder_pair.py` 통과
- `python3 -m src.train_encoder_pair --help` 출력 확인
- `src.train_encoder_pair` validate-only 경로에서 새 옵션(`--max-saved-prediction-rows`, `--log-every-steps`)과 최종 `train_config.json` 저장을 확인함
- 잘못된 CLI 값 검증 확인:
  - `--threshold 2` 실행 시 `[ERROR] --threshold must be between 0 and 1`로 실패함
- `python3 -m py_compile src/prepare_codex_review.py` 통과
- `src.prepare_codex_review`를 df003 batch_002 human review CSV에 실행해 Codex 검토용 CSV/XLSX/report를 생성함
- 생성된 Codex review XLSX를 다시 입력으로 읽는 경로도 `/private/tmp`에서 smoke test하여 `n_rows=142`, `span_parse_counts.parsed=142`를 확인함
- df003 batch_002 Codex review report 확인:
  - n_rows: 142
  - span_parse_counts: `parsed=142`, `parse_error=0`, `out_of_bounds=0`, `overlap_or_unsorted=0`
  - span_source_counts: `component_spans=74`, `regex_match_fallback=68`
  - component_span_status_counts: `ok=74`, `no_ordered_component_path=67`, `partial_required_components=1`
- 모델 다운로드 없이 `/private/tmp`에서 validate-only 실행을 확인함:
  - command: `python3 -m src.train_encoder_pair --examples-jsonl /Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003/df003_encoder_pair_examples.jsonl --out-dir /private/tmp/hantalk_train_encoder_pair_validate --model-name-or-path local-placeholder-model --seed 42 --shuffle-seed 42 --validate-only --skip-tokenization-stats --overwrite`
  - output files:
    - `/private/tmp/hantalk_train_encoder_pair_validate/train_config.json`
    - `/private/tmp/hantalk_train_encoder_pair_validate/data_summary.json`
    - `/private/tmp/hantalk_train_encoder_pair_validate/train_encoder_pair_report.json`
  - data summary: total 145, train 117, dev 14, test 14, positive 60, negative 85
  - train/dev/test 모두 label 0/1을 포함함
- `python3 -m py_compile src/prepare_example_corpus.py` 통과
- 새 sampling schedule 검증을 위해 `/private/tmp`에 batch_002 ratio check 산출물을 임시 생성함:
  - total: 10,200
  - `daily_conversation=5000`
  - `news=700`
  - `non_published=2000`
  - `learner_spoken_5_6=2500`
  - schedule: `batch_002_plus_rebalanced_ratio`
  - rank ranges: `daily_conversation=10000:15000`, `news=4000:4700`, `non_published=4000:6000`, `learner_spoken_5_6=2000:4500`
- `git diff --check`로 문서와 `src/prepare_example_corpus.py`의 whitespace 오류가 없음을 확인함
- batch_002부터 예문 구축용 prepared corpus 비율을 조정함:
  - `daily_conversation=5000`
  - `news=700`
  - `non_published=2000`
  - `learner_spoken_5_6=2500`
- 비율 조정 이유를 `PROJECT_SPEC.md`와 `DECISIONS.md`에 기록함
  - 뉴스 말뭉치 문장은 다른 말뭉치보다 대체로 2~3배 길고, 학습자 말뭉치 문장은 짧음
  - 따라서 문장 수를 단순히 `5:2:2:1`로 두면 실제 텍스트량과 학습자 발화 비중이 의도와 다르게 나올 수 있음
- `configs/corpus/example_making_manifest.json`에 `sampling_schedules`와 `rank_start_offsets`를 추가해 batch_000/001은 기존 비율로 재생성 가능하게 보존하고, batch_002 이후는 새 비율로 이전 사용 hash rank를 건너뛰어 생성하도록 수정함
- 작업 속도를 줄이기 위해 2024년 신문 말뭉치 통합 파일을 5개 JSON 기반 축소본으로 다시 생성함:
  - source folder: `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_work/corpus/example_making/news_paper(2024)`
  - source JSON files: `NIRW2400000001.json`, `NLRW2400000001.json`, `NPRW2400000001.json`, `NWRW2400000001.json`, `NZRW2400000001.json`
  - 확인용 산출물: `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_work/corpus/example_making/news_paper(2024)/news_paper_2024_form_source.txt`
  - manifest가 읽는 산출물: `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_work/corpus/example_making/신문말뭉치(2024).txt`
  - 형식: `form;source`
  - 행 수: header 제외 1,215,885행, header 포함 1,215,886줄
- 향후 예문 구축 검색 산출물은 item별 artifact 폴더에 저장하도록 정리함:
  - 공통 prepared corpus: `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_work/corpus/example_making/prepared/`
  - item별 산출물 root: `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/{item_id}/`
  - 예: `/Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003/df003_batch_002_human_review.csv`
- batch_000 + batch_002 labeled review 누적 summary 확인:
  - `n_rows=287`
  - `TP=130`
  - `FP=157`
  - `positive_100=true`
  - `negative_100=true`
  - `next_action=ready_for_encoder_export`
- batch_000 + batch_002 labeled review에서 인코더 pair examples export 확인:
  - `n_rows_exported=287`
  - `positive=130`
  - `negative=157`
  - `pos_conti=32`
  - `pos_disconti=98`
  - `neg_target_absent=157`
  - `train=229`, `dev=29`, `test=29`
- 모델 다운로드 없이 `/private/tmp`에서 최신 `df003_encoder_pair_examples.jsonl` validate-only를 실행함:
  - command: `python3 -m src.train_encoder_pair --examples-jsonl /Users/yonghyunnam/coding/HanTalk_group/HanTalk_arti/example_making/df003/df003_encoder_pair_examples.jsonl --out-dir /private/tmp/hantalk_df003_encoder_pair_validate_287 --model-name-or-path klue/roberta-base --seed 42 --shuffle-seed 42 --validate-only --skip-tokenization-stats --overwrite`
  - output files:
    - `/private/tmp/hantalk_df003_encoder_pair_validate_287/train_config.json`
    - `/private/tmp/hantalk_df003_encoder_pair_validate_287/data_summary.json`
    - `/private/tmp/hantalk_df003_encoder_pair_validate_287/train_encoder_pair_report.json`
  - validation result: `n_examples=287`
## 다음 작업

1. df003 예문 수집은 현재 기준으로 멈추고, `df003_encoder_pair_examples.jsonl`을 학습 입력 SSOT로 사용함
2. 실제 encoder 학습 전에 모델 후보와 실행 환경을 정함
   - 후보 예: `klue/roberta-base`, `klue/bert-base`, 경량 Korean encoder 후보, DeBERTa 계열 등
   - 목표: F1=1에 도달 가능한 모델 중 end-to-end inference latency가 가장 낮은 모델 찾기
3. 선택한 backbone으로 `src.train_encoder_pair` 정식 학습을 실행함
4. 학습 report에서 아래를 비교함
   - dev/test F1, balanced accuracy
   - truncation stats
   - `avg_inference_example_sec`
   - parameter count
   - debug predictions
5. 학습 결과가 불안정하면 batch_003부터 추가 labeled review를 수집해 예문 수를 늘림

## 주의사항

- df003은 batch_000 + batch_002만으로 positive/negative 100개 기준을 충족했으므로, 다음 명시 요청이 있으면 인코더 fine-tuning을 시작할 수 있습니다.
- 다만 모델 후보와 실행 환경을 정하기 전까지는 추가 corpus batch를 만들거나 labeled 파일을 덮어쓰지 않습니다.
- 현재 구현한 것은 인코더 학습 실행이 아니라 pair-mode 학습 예문 export입니다.
- `src/train_encoder_pair.py`는 구현되어 있지만, 현재 batch_000 기준 positive=60/negative=85이므로 정식 학습은 아직 권장하지 않습니다. smoke나 validate-only는 가능하지만 논문/실험용 학습은 positive/negative 각각 100개 이상을 확보한 뒤 실행합니다.
- Phase 1에서는 Label Studio, Prefect, DVC, MLflow를 도입하지 않습니다.
- LLM이 만든 TP/FP 판단은 임시 참고용이며 gold label이 아닙니다.
- 사람이 만든 gold와 human review 파일은 명시 요청 없이 덮어쓰지 않습니다.
- 정규식 recall=1은 사람이 만든 gold 50개 기준입니다.
- 말뭉치 FP를 줄이기 위해 정규식을 수정하더라도 gold recall=1이 깨지면 검색용 정규식으로 확정하지 않습니다.
- 브릿지는 무조건 채택하지 않고, 넓은 정규식으로 gold recall=1을 확보한 뒤 후보 버전 또는 `bridge_id` 버전을 만들어 비교합니다.
- 브릿지 후보는 gold recall=1 유지와 5,000행 말뭉치 FP 감소량을 확인한 뒤, FP 감소 효과가 있거나 span 경계가 좋아질 때만 채택합니다. df003의 `adnominal_n`은 현재 채택되어 있습니다.
- 일반 말뭉치 검색은 공통 prepared corpus batch를 사용합니다. batch_002부터 현재 batch 비율은 일상대화 5,000행, 뉴스 700행, 비출판물 2,000행, 학습자 말뭉치 2,500행입니다. batch_000/001은 이전 비율 산출물로 보존합니다.

## 미해결 문제

- df003 span 기준은 기존 df003 gold span을 변환해 사용했지만, 최종 교육적 span 정책은 사람이 확인해야 합니다.
- 공통 prepared corpus batch는 stable hash 기반으로 구현했고, batch_002부터 비율 변경에 따른 domain별 중복을 피하기 위해 `sampling_schedules`와 `rank_start_offsets`를 사용합니다. 이후 batch_index를 늘릴 때 domain별 중복 없음과 검수량 운영 방식은 계속 확인해야 합니다.
- 기본 detector 경로는 Kiwi 없이 진행합니다. 다만 문자 기반 bridge로 해결하기 어려운 항목이 나오면 Kiwi 상업 라이선스/속도/정확도 및 다른 형태소 분석기 후보를 비교해야 합니다.
- 예외적으로 형태소 분석을 쓰게 될 경우 문장 단위 형태소 분석 cache를 전체 300개 규칙에 공유할지, 난이도/목표 항목에 따라 필요한 규칙에만 공유할지는 HanTalk 본 시스템 설계 단계에서 다시 결정해야 합니다.
- `PROJECT_SPEC.md`의 `향후 detector 설계 검토 메모`는 SSOT가 아니라 비-SSOT 검토 목록입니다. 구현 전 다시 검토해야 합니다.
- df003은 component span 조립이 붙었지만, 일반 말뭉치에서는 `regex_match_fallback` 후보가 FP로 남을 수 있습니다. corpus search 단계에서 이 후보들을 확인해야 합니다.
- 현재 `detector_bundle.json`은 dict 정리 후 warnings=0으로 생성됩니다.
- 현재 최신 `detector_bundle.json`은 warnings=0으로 export되며, df003 gold recall=1.0을 회복했습니다.


## 2026-04-30 업무 시작 점검

- 읽은 기준 문서: `AGENTS.md` → `PROJECT_SPEC.md` → `DECISIONS.md` → `CURRENT_TASK.md`
- 기준 문서상 현재 Phase: Phase 1 pilot
- 기준 문서상 현재 항목: df003 `ㄴ/은 적 있/없`
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
- 내부 로더가 `rule_type=surface_regex`, `engine=re`를 자동 보충하도록 구현됨.
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

## 2026-05-01 df003 gold recall test CLI 구현

- `regex/df003_versions.jsonl`에 df003 v1 정규식을 추가함.
- `src/test_gold.py`를 추가하여 정규식 버전 JSONL과 `exported_gold/df003_gold_50.jsonl`을 읽고 gold recall과 FN report를 출력하도록 함.
- `configs/grammar_items.yaml`의 `gold_file` 경로를 `exported_gold/df003_gold_50.jsonl`로 수정함.
- 실행 명령: `python3 src/test_gold.py --item-id df003 --regex-version v1`
- 테스트 결과: `gold_total=50`, `gold_matched=50`, `gold_recall=1.000000`, `fn_count=0`
- 생성된 보고서: `logs/df003_gold_eval_v1.json`, `logs/df003_fn_report_v1.jsonl`
- 다음 작업은 v1 정규식을 일반 말뭉치에 적용해 hit 후보를 수집하고, TP/FP 검수표 구조를 만드는 것임.

## 2026-05-01 말뭉치 FP 기반 정규식 개선 루프 기록

- `PROJECT_SPEC.md`에 검색용 정규식 및 예문 구축 루프를 추가함.
- 1단계는 정규식 gold 50개 기준 recall=1 검색용 정규식을 만드는 과정으로 정리함.
- 2단계는 뉴스/일상 대화 말뭉치를 각각 5,000행 단위 batch로 검색하고, 사람이 검수한 FP 유형을 바탕으로 gold recall=1을 유지하며 정규식을 좁히는 과정으로 정리함.
- TP/FP 최종 라벨과 span은 사람이 확정하고, LLM 판단은 임시 참고용으로만 사용한다는 원칙을 재확인함.
- positive/negative 예문은 각각 100개가 모일 때까지 batch 검색과 사람 검수를 반복하기로 함.

## 2026-05-01 브릿지 및 형태소 분석 cache 원칙 기록

- 브릿지는 무조건 채택하지 않고 비교 실험 후 채택하기로 기록함.
- 먼저 넓은 정규식으로 gold recall=1을 확보하기로 함.
- 브릿지 후보를 붙인 버전을 별도로 만들고, gold recall=1 유지 여부를 확인하기로 함.
- gold recall=1을 유지한 브릿지 후보는 5,000행 말뭉치에서 FP 감소량을 확인하기로 함.
- FP 감소 효과가 있거나 span 경계가 좋아지면 채택하고, 효과가 작고 복잡도만 늘면 보류하기로 함.
- `AGENTS.md`, `PROJECT_SPEC.md`, `DECISIONS.md`, `CURRENT_TASK.md`에서 이전 브릿지 채택 표현을 비교 후 채택 원칙으로 수정함.
- 당시에는 `rg`로 관련 문구를 확인함. 코드 변경은 없었으므로 별도 실행 테스트는 하지 않았음.
- 형태소 분석은 장기적으로 문장 단위 1회 분석 후 token/span/cache를 만들고 필요한 규칙들이 공유하는 구조를 검토하기로 함.
- 모든 300개 규칙이 항상 공유하는 것이 아니라, 난이도 단계나 목표 문법항목 범위에 따라 필요한 규칙만 공유할 수 있다는 단서를 기록함.
- Kiwi는 후보 중 하나로 두고, 상업 라이선스, 속도, 정확도, 배포 조건 및 다른 형태소 분석기 가능성을 나중에 반드시 비교하기로 함.

## 2026-05-01 df003 bridge candidate 추가

- 이전 프로젝트의 `build_silver.py`/`infer_step1.py`를 확인해 관형형 브릿지의 핵심이 `ㄴ/은` 구성요소를 명시적 `은/ㄴ/ᆫ` 또는 앞 음절 종성 `ㄴ`으로 복구하는 방식임을 확인함.
- 그 원리를 순수 Python `re`에서 쓸 수 있도록 종성 `ㄴ` 음절 class를 사용한 `v2_bridge_candidate` 정규식으로 정리함.
- `regex/df003_versions.jsonl`에 `v2_bridge_candidate`를 추가함.
- 실행 명령: `python3 src/test_gold.py --item-id df003 --regex-version v2_bridge_candidate --fail-on-fn`
- 테스트 결과: `gold_total=50`, `gold_matched=50`, `gold_recall=1.000000`, `fn_count=0`
- 생성된 보고서: `logs/df003_gold_eval_v2_bridge_candidate.json`, `logs/df003_fn_report_v2_bridge_candidate.jsonl`
- 다음 단계는 v1과 v2 bridge candidate를 같은 5,000행 말뭉치 batch에 적용해 FP 감소량과 span 경계 개선 여부를 비교하는 것임.

## 2026-05-01 df003 명칭 정리

- 문법항목 명명은 필수 구성성분만 포함하는 방향으로 정리함.
- 긴 활용형 중심으로 남아 있던 df003 항목명을 `ㄴ/은 적 있/없`으로 변경함.
- 수정 파일: `AGENTS.md`, `PROJECT_SPEC.md`, `DECISIONS.md`, `CURRENT_TASK.md`, `configs/grammar_items.yaml`, `regex/df003_versions.jsonl`.
- `dict.xlsx`의 `items.canonical_form`은 이미 `ㄴ/은 적 있/없`이므로 수정하지 않음.
- `gold.xlsx`와 `exported_gold/df003_gold_50.jsonl`의 실제 예문 문장은 명칭이 아니라 원문 자료이므로 수정하지 않음.
- 검증: `python3 src/test_gold.py --item-id df003 --regex-version v1 --fail-on-fn`, `python3 src/test_gold.py --item-id df003 --regex-version v2_bridge_candidate --fail-on-fn`.

## 2026-05-01 df003 필수 구성성분 명명 재점검

- 기준 문서 순서(`AGENTS.md` → `PROJECT_SPEC.md` → `DECISIONS.md` → `CURRENT_TASK.md`)를 다시 읽고 현재 Phase 1 범위에 맞는 작업인지 확인함.
- `plan_by_user.md`에서 pilot 항목명과 예시 config의 `name`을 `ㄴ/은 적 있/없`으로 정리함.
- `configs/grammar_items.yaml`, `PROJECT_SPEC.md`, `plan_by_user.md`의 alias도 활용형 중심 표현 대신 `ㄴ 적 있`, `은 적 있`, `본 적 있`처럼 필수 구성성분 중심으로 다듬음.
- 실제 gold 예문과 포함/제외 예시는 원문 데이터 또는 표면 예시이므로 수정하지 않음.
- 이전 프로젝트의 규칙 detect 방식은 그대로 복제하지 않고, 응답속도를 줄이는 조건 아래에서 필요한 detect/span/bridge/cache 아이디어만 참고하기로 재확인함.
- 검증: 기준 문서/config/regex/plan 파일에서 긴 활용형 중심의 df003 항목명과 alias가 남아 있지 않음을 `rg`로 확인함. 남은 `가 본 적이 있다` 표현은 항목명이 아니라 포함 예시 문장임.
- 검증: `python3 -m py_compile src/test_gold.py`, `python3 src/test_gold.py --item-id df003 --regex-version v1 --fail-on-fn`, `python3 src/test_gold.py --item-id df003 --regex-version v2_bridge_candidate --fail-on-fn`.

## 2026-05-01 detector 설계 검토 메모 기록

- `PROJECT_SPEC.md`에 `향후 detector 설계 검토 메모` 섹션을 추가함.
- 해당 섹션은 SSOT가 아니라 비-SSOT 검토 목록으로 명시함. 프로젝트 초반이라 schema와 구현 방식이 바뀔 수 있으므로, 구현 전 반드시 다시 검토해야 함.
- 당시 바로 다음 구현 범위는 `src/detector/export_bundle.py`, DetectorEngine 기반 구현, `src/test_gold.py`의 DetectorEngine 기반 리팩터링으로 제한했음.
- 이후 runtime bundle, `span_segments` 중심 output schema, component bridge 공용화, df003 component span 조립은 구현 완료됨.
- 아직 보류 중인 주요 항목: `group=c` polyset 단위 detect, detect profile, `active_unit_ids`/`teaching_target_e_ids` 분리, detection JSONL/review CSV CLI, offline `audit_rules.py`, group=c verify hard_fail 정책.
- 이 항목들은 당장 확정하지 않지만, corpus search와 HanTalk 실시간 detect를 같은 DetectorEngine 계열로 이어가기 위해 다음 구현 단계에서 반드시 다시 검토함.

## 2026-05-01 detector bundle 1차 구현

- `src/detector/__init__.py`, `src/detector/export_bundle.py`, `src/detector/engine.py`, `src/detector/span_utils.py`를 추가함.
- `export_bundle.py`는 `datasets/dict/dict.xlsx`를 읽어 `configs/detector/detector_bundle.json`을 생성함.
- bundle에는 `items_by_e_id`, `components_by_e_id`, `rules_by_ruleset_id`, `polysets_by_id`, `runtime_units`, `warnings`를 포함함.
- regex compile 실패, 필수 sheet/column 누락, 중복 ID, 잘못된 group/stage/target은 fatal error로 처리함.
- Excel blank/boolean/int/string 값을 runtime JSON에 맞게 normalize하고, JSON 저장 시 `allow_nan=False`를 사용함.
- DetectorEngine은 bundle 로딩, compiled regex cache, `active_unit_ids`, detect raw_sentence, verify hard_fail raw_sentence/char_window, summary count를 지원함.
- `char_window.window_chars`는 후보 envelope 기준 좌우 각각 N자로 정의함.
- 1차 DetectorEngine candidate는 당시 `span_source=regex_match`, `component_span_enabled=false`를 명시함. 이후 component span 조립 구현으로 df003은 `span_source=component_spans`를 사용할 수 있게 됨.
- `src/test_gold.py`는 기존 `regex_versions` 평가 경로를 유지하면서 `--bundle`, `--active-unit-id`, `--bundle-match-policy` 옵션을 추가함.
- bundle 평가에서는 future-proof하게 `candidate.unit_id == item_id` 또는 `item_id in member_e_ids`를 item match로 처리함.
- `PROJECT_SPEC.md`와 `DECISIONS.md`에 `dict.xlsx` SSOT/runtime bundle, `span_segments`, 1차 regex_match span 정책을 기록함.
- 검증:
  - `python3 -m py_compile src/detector/export_bundle.py src/detector/engine.py src/detector/span_utils.py src/test_gold.py`
  - `python3 -m src.detector.export_bundle --dict datasets/dict/dict.xlsx --out configs/detector/detector_bundle.json`
  - `python3 src/test_gold.py --item-id df003 --bundle configs/detector/detector_bundle.json --active-unit-id df003 --fail-on-fn`
  - `python3 src/test_gold.py --item-id df003 --bundle configs/detector/detector_bundle.json --active-unit-id df003 --bundle-match-policy overlap --fail-on-fn`
  - `python3 src/test_gold.py --item-id df003 --regex-version v1 --fail-on-fn`
  - `python3 src/test_gold.py --item-id df003 --regex-version v2_bridge_candidate --fail-on-fn`

## 2026-05-01 detector 안전장치 보강

- `export_bundle.py`에서 `detect_rules.e_id`와 `rule_components.e_id`가 `items.e_id`에 없는 경우 fatal error로 처리하도록 함.
- `items.detect_ruleset_id`가 detect rule을 1개도 포함하지 않거나, `items.verify_ruleset_id`가 verify rule을 1개도 포함하지 않으면 fatal error로 처리하도록 함.
- 같은 `ruleset_id` 안에 detect/verify stage가 섞이면 fatal error로 처리하도록 함.
- Excel header row 중간의 빈 header와 중복 header를 fatal error로 처리하도록 함.
- DetectorEngine은 `active_unit_ids`가 없으면 기본적으로 실행하지 않고, `allow_all=True`일 때만 전체 runtime unit 실행을 허용하도록 함.
- `group=c` polyset runtime unit은 Phase 1에서 기본 실행을 막고, 명시적 실험을 위해 `allow_experimental_polyset=True`를 둠.
- `max_matches_per_rule` 기본값 50을 추가하고, match 폭주가 있으면 summary에 `n_matches_truncated`, `truncated_rules`를 남기도록 함.
- 검증:
  - `python3 -m py_compile src/detector/export_bundle.py src/detector/engine.py src/detector/span_utils.py src/test_gold.py`
  - `python3 -m src.detector.export_bundle --dict datasets/dict/dict.xlsx --out configs/detector/detector_bundle.json` → `warnings=0`
  - df003 bundle sentence/overlap 평가 모두 `gold_recall=1.0`, `fn_count=0`
  - 기존 regex v1/v2 평가 모두 `gold_recall=1.0`, `fn_count=0`
  - `active_unit_ids` 누락 실행과 `ps_neunde` 기본 실행이 의도대로 `ValueError`를 발생시키는지 확인함.

## 2026-05-01 기준 문서 일관성 정리

- `PROJECT_SPEC.md`에서 현재 기준을 `dict.xlsx`/`detector_bundle.json`/`component_spans` 중심으로 정리함.
- `configs/grammar_items.yaml`은 장기 SSOT가 아니라 초기 pilot 보조 config로 명시함.
- corpus search 산출물 schema를 `span_start`/`span_end` 중심 CSV에서 `span_segments` 중심 detection JSONL + review CSV 구조로 교체함.
- `DECISIONS.md`의 초기 `regex_match` span 결정은 superseded decision으로 표시하고, 현재는 component span 성공 시 `component_spans`, 실패 시 `regex_match_fallback`을 사용한다고 명시함.
- `CURRENT_TASK.md`의 오래된 미래형 구현 표현과 초기 DetectorEngine 표현을 현재 구현 상태에 맞게 정리함.

"""6-1 회귀 테스트 + 데모 픽스처. FakeLLM 기반이라 키/네트워크 없이 돈다.

실행: uv run --directory backend python tests/test_analyze.py
"""

from datetime import date

from app.analysis.completeness import finalize_item
from app.analysis.pipeline import _postprocess, analyze, load_context
from app.feedback.db import save_user_preference
from app.llm.fake import FakeLLM
from app.llm.solar import _extract_json
from app.schemas.analysis import AnalyzeResult, ContextBundle, Item, LLMItem, LLMOutput
from app.schemas.items import ItemType, Priority

BASE = "2026-06-05"


def _run(text: str):
    return analyze(raw_text=text, base_date=BASE, llm=FakeLLM())


def test_scenario1_multi_item():
    r = _run("내일까지 성종은 발표자료, 동근은 API 테스트 정리, 우태는 데모 영상 준비. 금요일 오전 10시 최종 리허설하자.")
    assert len(r.items) == 4
    assert [i.type for i in r.items] == ["task", "task", "task", "calendar"]
    assert all(not i.needs_confirmation for i in r.items)  # 전부 명확
    assert all(i.due_date == date(2026, 6, 6) for i in r.items[:3])
    assert all(i.date is None for i in r.items[:3])         # task 마감은 due_date
    assert r.items[3].all_day is False                     # 일정에 time 있음
    assert r.items[3].date == date(2026, 6, 12)


def test_scenario2_vague_calendar_and_risk():
    r = _run("다음 주쯤 멘토님께 보여드리고, 안 되면 캘린더 연동은 Mock으로 대체하자.")
    pending = next(i for i in r.items if i.type == "pending")
    risk = next(i for i in r.items if i.type == "risk")
    # 모호 일정(날짜 vague, calendar 필수) → 정보 부족으로 확인 필요
    assert pending.needs_confirmation is True
    assert pending.recommended_tool == "save_to_pending"
    assert pending.clarification_question is not None
    assert pending.date is None
    assert pending.confidence <= 0.7
    assert risk.needs_confirmation is False


def test_scenario3_single_calendar_for_conflict():
    r = _run("다음 주 화요일 오전 10시에 팀 회의 잡자.")
    assert len(r.items) == 1
    cal = r.items[0]
    assert cal.type == "calendar" and cal.time == "10:00"
    assert cal.needs_confirmation is False  # 6-2가 기존 일정과 충돌 검증


def test_low_certainty_branches_to_class_ambiguous():
    # 보류(pending)는 type이 아니라 플래그: 분류 애매 → needs_confirmation
    item = finalize_item(LLMItem(
        type="task", title="기획서 다시 보기", type_certainty=0.5,
        date_status="missing", required_ok=True,
    ))
    assert item.needs_confirmation is True
    assert item.type == "pending"
    assert item.recommended_tool == "save_to_pending"
    assert "유형" in item.clarification_question   # 분류가 먼저, 완성도는 안 봄


def test_no_action_items_is_empty():
    # 입력 유형 라벨 없이, 실행 항목 없으면 빈 결과
    class Empty:
        def analyze(self, **_):
            return {"items": []}

    r = analyze(raw_text="ㅎㅇ", base_date=BASE, llm=Empty())
    assert r.items == []


def test_fake_llm_output_matches_contract():
    raw = FakeLLM().analyze(
        raw_text="다음 주 화요일 오전 10시에 팀 회의 잡자.",
        base_date=BASE,
        context=ContextBundle(),
    )
    output = LLMOutput.model_validate(raw)
    assert len(output.items) == 1
    assert output.items[0].type == "calendar"


def test_solar_json_extraction_matches_contract():
    raw = _extract_json("""```json
{
  "items": [
    {
      "type": "task",
      "title": "API 테스트 정리",
      "assignee": "이동근",
      "date": "2026-06-06",
      "time": null,
      "priority": "high",
      "source_sentence": "동근은 API 테스트 정리",
      "recommended_tool": "create_task",
      "type_certainty": 0.9,
      "date_status": "concrete",
      "assignee_present": true,
      "time_present": false,
      "needs_base_event": false,
      "required_ok": true
    }
  ]
}
```""")
    output = LLMOutput.model_validate(raw)
    assert output.items[0].type == "task"
    assert output.items[0].recommended_tool == "create_task"


def test_invalid_json_retries_then_uses_second_response():
    class BrokenThenValid:
        def __init__(self):
            self.calls = 0

        def analyze(self, **_):
            self.calls += 1
            if self.calls == 1:
                raise ValueError("broken json")
            return {"items": [{
                "type": "memo",
                "title": "두 번째 응답",
                "source_sentence": "두 번째 응답",
                "recommended_tool": "create_memo",
            }]}

    llm = BrokenThenValid()
    r = analyze(raw_text="두 번째 응답", base_date=BASE, llm=llm)
    assert llm.calls == 2
    assert r.items[0].title == "두 번째 응답"
    assert r.items[0].needs_confirmation is False


def test_invalid_json_twice_falls_back_to_pending():
    class AlwaysBroken:
        def __init__(self):
            self.calls = 0

        def analyze(self, **_):
            self.calls += 1
            raise ValueError("broken json")

    llm = AlwaysBroken()
    r = analyze(raw_text="원문", base_date=BASE, llm=llm)
    assert llm.calls == 2
    assert len(r.items) == 1
    assert r.items[0].type == "pending"
    assert r.items[0].recommended_tool == "save_to_pending"
    assert r.items[0].needs_confirmation is True


def test_next_weekday_is_normalized_from_base_date():
    class WrongDate:
        def analyze(self, **_):
            return {"items": [{
                "type": "calendar",
                "title": "팀 회의",
                "date": "2026-06-16",
                "time": "10:00",
                "source_sentence": "다음 주 화요일 오전 10시에 팀 회의 잡자.",
                "recommended_tool": "create_calendar_event",
                "type_certainty": 0.95,
                "date_status": "concrete",
                "time_present": True,
                "required_ok": True,
            }]}

    r = analyze(raw_text="다음 주 화요일 오전 10시에 팀 회의 잡자.", base_date=BASE, llm=WrongDate())
    assert r.items[0].date == date(2026, 6, 9)


def test_vague_date_does_not_keep_invented_date():
    class InventedVagueDate:
        def analyze(self, **_):
            return {"items": [{
                "type": "calendar",
                "title": "멘토님께 보여주기",
                "date": "2026-06-12",
                "source_sentence": "다음 주쯤 멘토님께 보여드리고",
                "recommended_tool": "create_calendar_event",
                "type_certainty": 0.85,
                "date_status": "vague",
                "required_ok": True,
            }]}

    r = analyze(raw_text="다음 주쯤 멘토님께 보여드리고", base_date=BASE, llm=InventedVagueDate())
    assert r.items[0].date is None
    assert r.items[0].needs_confirmation is True


def test_load_context_empty_when_no_saved_preferences():
    # 저장된 선호가 없으면 빈 컨텍스트 (autouse fixture 가 feedback.db 를 tmp 로 격리).
    context = load_context()
    assert context.preferences == []


def test_load_context_reinjects_saved_preferences():
    # 저장 -> load_context 가 그 선호를 다시 끌어와 ContextBundle.preferences 에 채운다.
    save_user_preference(field="date", original_pattern="vague", preferred="pending")
    save_user_preference(field="assignee", original_pattern="성종", preferred="박성종")

    context = load_context()

    by_field = {p["field"]: p for p in context.preferences}
    assert by_field["date"]["original_pattern"] == "vague"
    assert by_field["date"]["preferred"] == "pending"
    assert by_field["assignee"]["preferred"] == "박성종"


def test_load_context_falls_back_to_empty_on_db_error(monkeypatch):
    # 선호 로드가 실패해도 분석은 막지 않는다 (빈 선호 폴백).
    def _boom():
        raise RuntimeError("db unavailable")

    monkeypatch.setattr("app.analysis.pipeline.load_user_preferences", _boom)
    context = load_context()
    assert context.preferences == []


def test_load_context_includes_existing_items_summary(tmp_db):
    # 저장소의 기존 일정/할일이 요약 문자열로 프롬프트 컨텍스트에 들어간다.
    from app.tools.local_tools import create_calendar_event, create_task

    create_calendar_event("팀 회의", date(2026, 6, 12), "10:00")
    create_task("API 테스트 정리", assignee="동근", due_date=date(2026, 6, 6))

    summary = load_context().existing_items_summary
    assert "팀 회의" in summary
    assert "API 테스트 정리" in summary
    assert "동근" in summary


def test_load_context_summary_empty_on_storage_error(monkeypatch):
    # 저장소 조회 실패 시 요약은 빈 문자열(분석 계속).
    def _boom():
        raise RuntimeError("storage unavailable")

    monkeypatch.setattr("app.analysis.pipeline.load_calendar_events", _boom)
    assert load_context().existing_items_summary == ""


def test_load_context_reads_guidelines_json(tmp_path, monkeypatch):
    # guidelines.json을 읽어 ContextBundle.guidelines에 채운다.
    p = tmp_path / "guidelines.json"
    p.write_text('[{"rule": "테스트 지침"}]', encoding="utf-8")
    monkeypatch.setattr("app.analysis.pipeline._GUIDELINES_PATH", p)
    guidelines = load_context().guidelines
    assert any(g.get("rule") == "테스트 지침" for g in guidelines)


def test_load_context_guidelines_empty_when_missing(tmp_path, monkeypatch):
    monkeypatch.setattr("app.analysis.pipeline._GUIDELINES_PATH", tmp_path / "nope.json")
    assert load_context().guidelines == []


def test_load_context_guidelines_empty_on_broken_json(tmp_path, monkeypatch):
    p = tmp_path / "guidelines.json"
    p.write_text("{ broken json", encoding="utf-8")
    monkeypatch.setattr("app.analysis.pipeline._GUIDELINES_PATH", p)
    assert load_context().guidelines == []


def test_postprocess_applies_preference_override():
    # 선호 패턴과 일치하는 필드를 코드가 강제 치환(LLM이 안 따랐을 때의 이중 안전장치).
    item = Item(id="item-0", type=ItemType.task, title="발표자료", assignee="성종")
    ctx = ContextBundle(
        preferences=[{"field": "assignee", "original_pattern": "성종", "preferred": "박성종"}]
    )
    out = _postprocess(AnalyzeResult(items=[item]), ctx)
    assert out.items[0].assignee == "박성종"


def test_postprocess_no_change_when_pattern_mismatch():
    item = Item(id="item-0", type=ItemType.task, title="발표자료", assignee="우태")
    ctx = ContextBundle(
        preferences=[{"field": "assignee", "original_pattern": "성종", "preferred": "박성종"}]
    )
    out = _postprocess(AnalyzeResult(items=[item]), ctx)
    assert out.items[0].assignee == "우태"


def test_postprocess_pass_through_without_preferences():
    item = Item(id="item-0", type=ItemType.task, title="x", assignee="성종")
    out = _postprocess(AnalyzeResult(items=[item]), ContextBundle())
    assert out.items[0].assignee == "성종"


def test_postprocess_applies_enum_preference_with_type_coercion():
    # priority(enum) 선호도 직렬화 비교 + 재검증으로 타입이 강제된다.
    item = Item(id="item-0", type=ItemType.task, title="x", priority=Priority.medium)
    ctx = ContextBundle(
        preferences=[{"field": "priority", "original_pattern": "medium", "preferred": "high"}]
    )
    out = _postprocess(AnalyzeResult(items=[item]), ctx)
    assert out.items[0].priority == Priority.high


def test_postprocess_skips_invalid_preference_without_crashing():
    # preferred 값이 필드 타입에 invalid(date 필드에 비날짜)면 보정을 건너뛰고 원본 유지.
    # ValidationError 가 analyze 전체를 실패시키지 않아야 한다(best-effort).
    item = Item(id="item-0", type=ItemType.task, title="발표자료", due_date=date(2026, 6, 6))
    ctx = ContextBundle(
        preferences=[
            {"field": "due_date", "original_pattern": "2026-06-06", "preferred": "내일까지"}
        ]
    )
    out = _postprocess(AnalyzeResult(items=[item]), ctx)
    assert out.items[0].due_date == date(2026, 6, 6)  # 원본 유지(크래시 없음)


if __name__ == "__main__":
    import inspect

    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    ran = 0
    for fn in fns:
        # load_context 선호 테스트는 pytest fixture(tmp DB 격리/monkeypatch)에 의존하므로
        # 직접 실행 시 실제 feedback.db 를 오염시키지 않도록 건너뛴다.
        if inspect.signature(fn).parameters or "load_context" in fn.__name__:
            print(f"SKIP {fn.__name__} (needs pytest fixtures)")
            continue
        fn()
        ran += 1
        print(f"PASS {fn.__name__}")
    print(f"\n{ran} passed")

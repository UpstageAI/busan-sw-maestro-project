import tempfile
import unittest
from pathlib import Path

from backend.app.config import get_settings
from backend.app.db import Repository
from backend.app.models import Article, BriefingProfileInput, BriefingRequest, FetchReport
from backend.app.news_client import NewsClient
from backend.app.service import BriefingService, ValidationError
from backend.app.summarizer import Summarizer


def build_service(tmp_dir: Path) -> BriefingService:
    repository = Repository(tmp_dir / "test.db")
    repository.init()
    return BriefingService(
        news_client=NewsClient(api_key=None, use_rss=False),
        summarizer=Summarizer(
            api_key=None,
            model=get_settings().upstage_model,
            base_url=get_settings().upstage_base_url,
        ),
        repository=repository,
    )


class StaticNewsClient:
    def __init__(self, articles: list[Article]) -> None:
        self.articles = articles

    def fetch(
        self,
        *,
        sources: list[str],
        topics: list[str],
        custom_keywords: list[str],
        date_range: str,
        limit: int,
    ) -> tuple[list[Article], list[str], bool, FetchReport]:
        return self.articles, [], False, FetchReport(
            source_count=len(sources),
            collected_count=len(self.articles),
            attempted_feed_count=1,
            failed_feed_count=0,
        )


class RecordingSelector:
    def __init__(self) -> None:
        self.candidate_count = 0
        self.limit = 0

    def summarize(
        self, articles: list[Article], topic_labels: list[str], *, limit: int | None = None
    ) -> tuple[list[Article], list[str], list[str]]:
        self.candidate_count = len(articles)
        self.limit = limit or len(articles)
        selected = [
            article.model_copy(
                update={
                    "summary": "LLM 선별 후보 요약",
                    "why_it_matters": "사용자 관심 조건과 직접 관련됩니다.",
                    "selection_reason": "키워드 풀 안에서 맥락 관련성이 높아 선택했습니다.",
                    "issue_group": "AI 투자",
                    "agent_selected": True,
                }
            )
            for article in articles[: self.limit]
        ]
        return selected, ["AI 투자 이슈"], []


class BriefingServiceTest(unittest.TestCase):
    def test_create_briefing_with_sample_data(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = build_service(Path(temp_dir))
            briefing = service.create_briefing(
                BriefingRequest(
                    sources=["yonhap", "mk", "hankyung"],
                    topics=["ai", "economy"],
                    date_range="7d",
                    limit=5,
                )
            )

        self.assertTrue(briefing.articles)
        self.assertTrue(briefing.used_sample_data)
        self.assertTrue(briefing.articles[0].summary)
        self.assertGreaterEqual(briefing.articles[0].priority_score, 0)
        self.assertTrue(briefing.articles[0].priority_label)

    def test_lists_and_loads_briefing_history(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = build_service(Path(temp_dir))
            created = service.create_briefing(
                BriefingRequest(
                    sources=["yonhap", "mk", "hankyung"],
                    topics=["ai", "economy"],
                    date_range="7d",
                    limit=5,
                )
            )
            history = service.list_history()
            loaded = service.get_briefing(history[0].id)

        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].title, created.title)
        self.assertEqual(history[0].article_count, len(created.articles))
        self.assertEqual(history[0].custom_keywords, created.custom_keywords)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.title, created.title)

    def test_requires_source_selection(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = build_service(Path(temp_dir))
            with self.assertRaises(ValidationError) as context:
                service.create_briefing(BriefingRequest(sources=[], topics=["ai"]))

        self.assertIn("언론사", str(context.exception))

    def test_custom_keywords_can_drive_briefing_without_topic(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = build_service(Path(temp_dir))
            briefing = service.create_briefing(
                BriefingRequest(
                    sources=["chosun"],
                    topics=[],
                    custom_keywords=["유통"],
                    date_range="7d",
                    limit=1,
                )
            )

        self.assertEqual(briefing.custom_keywords, ["유통"])
        self.assertIn("유통", briefing.title)
        self.assertEqual(len(briefing.articles), 1)
        self.assertIn("유통", briefing.articles[0].priority_reason or "")

    def test_exclude_keywords_remove_matching_articles(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = build_service(Path(temp_dir))
            briefing = service.create_briefing(
                BriefingRequest(
                    sources=["chosun"],
                    topics=[],
                    custom_keywords=["유통"],
                    exclude_keywords=["유통"],
                    date_range="7d",
                    limit=3,
                )
            )

        self.assertEqual(briefing.articles, [])
        self.assertEqual(briefing.exclude_keywords, ["유통"])
        self.assertEqual(briefing.stats.selected_count, 0)

    def test_saves_lists_and_deletes_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = Repository(Path(temp_dir) / "test.db")
            repository.init()
            created = repository.save_profile(
                BriefingProfileInput(
                    name="반도체 모니터링",
                    sources=["yonhap"],
                    topics=["ai"],
                    custom_keywords=["반도체"],
                    exclude_keywords=["스포츠"],
                    date_range="7d",
                    limit=5,
                )
            )
            profiles = repository.list_profiles()
            deleted = repository.delete_profile(created.id)

        self.assertEqual(len(profiles), 1)
        self.assertEqual(profiles[0].custom_keywords, ["반도체"])
        self.assertEqual(profiles[0].exclude_keywords, ["스포츠"])
        self.assertTrue(deleted)

    def test_passes_rule_candidates_to_agent_selector_before_final_selection(self) -> None:
        titles = [
            "AI 반도체 투자 확대",
            "AI 데이터센터 전력 수요 증가",
            "AI 로봇 산업 협력",
            "AI 클라우드 인프라 경쟁",
            "AI 소프트웨어 수출 전략",
            "AI 칩 설계 생태계",
            "AI 제조 자동화 확산",
            "AI 보안 플랫폼 출시",
        ]
        articles = [
            Article(
                title=title,
                source="테스트뉴스",
                url=f"https://example.com/{index}",
                published_at="2026-06-07T09:00:00+09:00",
                description="AI 반도체 데이터센터 투자 확대",
            )
            for index, title in enumerate(titles)
        ]
        selector = RecordingSelector()
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = Repository(Path(temp_dir) / "test.db")
            repository.init()
            service = BriefingService(
                news_client=StaticNewsClient(articles),
                summarizer=selector,
                repository=repository,
            )
            briefing = service.create_briefing(
                BriefingRequest(
                    sources=["yonhap"],
                    topics=["ai"],
                    custom_keywords=["반도체"],
                    date_range="7d",
                    limit=3,
                )
            )

        self.assertEqual(selector.limit, 3)
        self.assertGreater(selector.candidate_count, 3)
        self.assertEqual(briefing.stats.candidate_count, 8)
        self.assertEqual(briefing.stats.selected_count, 3)
        self.assertTrue(briefing.stats.selector_used)
        self.assertTrue(all(article.agent_selected for article in briefing.articles))
        self.assertTrue(briefing.articles[0].selection_reason)


if __name__ == "__main__":
    unittest.main()

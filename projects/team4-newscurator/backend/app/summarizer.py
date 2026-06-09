from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from backend.app.models import Article


class Summarizer:
    def __init__(self, *, api_key: str | None, model: str, base_url: str) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    def summarize(
        self, articles: list[Article], topic_labels: list[str], *, limit: int | None = None
    ) -> tuple[list[Article], list[str], list[str]]:
        if not articles:
            return [], [], []
        final_limit = min(limit or len(articles), len(articles))
        if not self.api_key:
            selected = articles[:final_limit]
            return self._fallback(selected, topic_labels), self._common_topics(selected, topic_labels), [
                "UPSTAGE_API_KEY가 없어 로컬 우선순위 후보를 선택하고 요약했습니다."
            ]

        try:
            payload = self._call_upstage(articles, topic_labels, final_limit)
            summarized = self._merge_ai_result(articles, payload, final_limit)
            common_topics = payload.get("common_topics", []) or self._common_topics(summarized, topic_labels)
            notices = [f"Upstage가 룰 기반 후보 {len(articles)}건 중 {len(summarized)}건을 최종 선별했습니다."]
            return summarized, common_topics, notices
        except Exception as exc:
            selected = articles[:final_limit]
            summarized = self._fallback(selected, topic_labels)
            common_topics = self._common_topics(articles, topic_labels)
            notices = [f"Upstage 선별/요약 API 오류로 로컬 우선순위 선별을 사용했습니다: {exc}"]
            return summarized, common_topics, notices

    def _call_upstage(self, articles: list[Article], topic_labels: list[str], limit: int) -> dict[str, Any]:
        article_payload = [
            {
                "index": index,
                "title": article.title,
                "source": article.source,
                "published_at": article.published_at,
                "description": article.description,
                "matched_keywords": article.matched_keywords,
                "rule_score": article.priority_score,
                "rule_reason": article.priority_reason,
            }
            for index, article in enumerate(articles)
        ]
        body = {
            "model": self.model,
            "temperature": 0.2,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "당신은 객관적이고 중립적인 뉴스 브리핑 에이전트입니다. "
                        "후보 기사 중 사용자의 관심 조건과 실제 관련성이 높은 기사만 선별하세요. "
                        "중복 이슈는 대표 기사 위주로 고르고, 너무 주변적인 기사는 제외하세요. "
                        "원문에 없는 사실, 정치적 의견, 투자 추천, 진위 판단을 추가하지 마세요. "
                        "반드시 설명 없이 유효한 JSON 객체만 출력하세요."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "topics": topic_labels,
                            "selection_limit": limit,
                            "instructions": {
                                "selection": "후보 기사에서 최종 브리핑 기사만 선별",
                                "selection_reason": "선택 이유는 사용자 관심 조건과의 관련성 중심으로 한국어 1문장",
                                "issue_group": "같은 이슈를 묶는 짧은 한국어 이름",
                                "article_summary": "기사별 요약은 한국어 2문장 이내",
                                "why_it_matters": "사용자가 왜 봐야 하는지 중립적으로 1문장",
                                "common_topics": "기사 전반의 공통 핵심 이슈 1~3개",
                            },
                            "articles": article_payload,
                            "output_schema": {
                                "common_topics": ["공통 핵심 이슈"],
                                "selected_articles": [
                                    {
                                        "index": 0,
                                        "selection_reason": "선별 이유",
                                        "issue_group": "이슈 그룹",
                                        "summary": "요약",
                                        "why_it_matters": "중요한 이유",
                                    }
                                ],
                            },
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
        }
        request = Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=30) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc

        content = response_payload["choices"][0]["message"]["content"]
        return self._parse_json_content(content)

    def _parse_json_content(self, content: str) -> dict[str, Any]:
        text = content.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        return json.loads(text)

    def _merge_ai_result(self, articles: list[Article], payload: dict[str, Any], limit: int) -> list[Article]:
        selected_items = payload.get("selected_articles") or payload.get("articles") or []
        merged: list[Article] = []
        selected_indexes: set[int] = set()
        for item in selected_items:
            if not isinstance(item, dict) or "index" not in item:
                continue
            try:
                index = int(item["index"])
            except (TypeError, ValueError):
                continue
            if index < 0 or index >= len(articles) or index in selected_indexes:
                continue
            selected_indexes.add(index)
            article = articles[index]
            merged.append(
                article.model_copy(
                    update={
                        "summary": item.get("summary") or article.description or article.title,
                        "why_it_matters": item.get("why_it_matters")
                        or "선택한 관심 분야와 관련된 최신 흐름을 파악하는 데 도움이 됩니다.",
                        "selection_reason": item.get("selection_reason")
                        or "룰 기반 후보군에서 사용자 관심 조건과의 관련성이 높아 선택했습니다.",
                        "issue_group": item.get("issue_group"),
                        "agent_selected": True,
                    }
                )
            )
            if len(merged) == limit:
                break

        if len(merged) < limit:
            selected_urls = {str(article.url) for article in merged}
            fallback_articles = [
                article for article in articles if str(article.url) not in selected_urls
            ][: limit - len(merged)]
            merged.extend(self._fallback(fallback_articles, []))

        return merged

    def _fallback(self, articles: list[Article], topic_labels: list[str]) -> list[Article]:
        topic_text = ", ".join(topic_labels) if topic_labels else "선택한 관심 분야"
        summarized: list[Article] = []
        for article in articles:
            description = article.description or article.title
            summary = description
            if len(summary) > 160:
                summary = summary[:157].rstrip() + "..."
            summarized.append(
                article.model_copy(
                    update={
                        "summary": summary,
                        "why_it_matters": f"{topic_text} 흐름을 빠르게 확인할 수 있는 기사입니다.",
                    }
                )
            )
        return summarized

    def _common_topics(self, articles: list[Article], topic_labels: list[str]) -> list[str]:
        if topic_labels:
            return [f"{label} 관련 주요 이슈가 이어지고 있습니다." for label in topic_labels[:3]]
        sources = sorted({article.source for article in articles})
        return [f"{', '.join(sources[:3])} 등에서 다룬 주요 이슈입니다."]

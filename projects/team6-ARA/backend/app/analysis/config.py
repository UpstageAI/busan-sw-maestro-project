"""6-1 판단 임계값/규칙 상수.

planning.md: confidence 0.7은 데이터로 계산하는 값이 아니라 MVP 초기 컷오프이며
데모 시나리오를 돌려보며 팀이 손으로 조정한다. → 여기 모아두고 튜닝한다.
"""

# 분류 확신도가 이 값 미만이면 "분류 애매"로 확인 필요
CERTAINTY_THRESHOLD = 0.7
# 완성도가 이 값 미만이면 "정보 부족"으로 확인 필요
COMPLETENESS_THRESHOLD = 0.7

# 날짜가 의미 있는(감점 대상) 유형 / 날짜가 필수인 유형
DATE_RELEVANT_TYPES = {"task", "calendar"}
DATE_REQUIRED_TYPES = {"calendar"}

# 규칙 기반 감점 (1.0에서 시작)
PENALTY_DATE_VAGUE = 0.3
PENALTY_DATE_MISSING = 0.2
PENALTY_TASK_NO_ASSIGNEE = 0.2
PENALTY_NEEDS_BASE_EVENT = 0.3

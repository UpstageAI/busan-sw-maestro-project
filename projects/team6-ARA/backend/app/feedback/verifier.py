from typing import Any


def verify_result(result: dict[str, Any]) -> bool:
    """
    저장 결과가 유효한지 확인한다.
    현재는 결과값 존재 여부만 체크. 향후 세부 검증 로직은 이 함수 안에 추가한다.
    """
    return bool(result)

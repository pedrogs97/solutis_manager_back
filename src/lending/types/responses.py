from typing import Any, Dict, List, TypedDict


class LendingDataResponse(TypedDict):
    lending: Dict[str, Any]
    document: Dict[str, Any]
    verfication: List[Dict[str, Any]]

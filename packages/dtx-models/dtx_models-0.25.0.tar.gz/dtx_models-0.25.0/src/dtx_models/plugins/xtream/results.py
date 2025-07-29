from typing import List, Optional

from pydantic import BaseModel


class TurnResult(BaseModel):
    """Result of a single conversation turn."""

    turn: int
    phase: int
    attacker: str
    target: str
    target_truncated: str
    evaluation_score: int
    evaluation_reason: str


class StrategyResult(BaseModel):
    """Result of a single strategy attempt."""

    set_number: Optional[int] = None
    strategy_number: Optional[int] = None
    conversation: List[TurnResult]
    jailbreak_achieved: bool
    jailbreak_turn: Optional[int]


class BehaviorResult(BaseModel):
    """Result of one behavior (multiple strategies)."""

    behavior_number: int
    behavior: dict
    strategies: List[StrategyResult]


class FullRunResults(BaseModel):
    """Result of the full run (multiple behaviors)."""

    configuration: dict
    behaviors: dict[int, BehaviorResult]

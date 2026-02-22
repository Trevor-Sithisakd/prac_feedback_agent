"""Data models for input normalization used by the Intake Crew."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Literal

Tone = Literal["supportive", "direct", "balanced"]
Format = Literal["bullet", "narrative", "hybrid"]

ALLOWED_TONES = {"supportive", "direct", "balanced"}
ALLOWED_FORMATS = {"bullet", "narrative", "hybrid"}


@dataclass
class Preferences:
    tone: Tone = "supportive"
    format: Format = "hybrid"


@dataclass
class PersonaProfile:
    goals: List[str] = field(default_factory=list)
    context: str = ""
    preferences: Preferences = field(default_factory=Preferences)


@dataclass
class Guidelines:
    must_include: List[str]
    style_rules: List[str]
    safety_rules: List[str]


@dataclass
class QualityTargets:
    min_action_items: int = 3
    requires_metrics: bool = True
    pass_threshold: int = 80


@dataclass
class InputPacket:
    topic: str
    user_intent: str
    persona_profile: PersonaProfile
    guidelines: Guidelines
    quality_targets: QualityTargets
    risk_flags: List[str]
    clarification_needed: bool
    intake_confidence: float

    def validate(self) -> None:
        if not self.topic.strip():
            raise ValueError("topic must not be empty")
        if not self.user_intent.strip():
            raise ValueError("user_intent must not be empty")

        prefs = self.persona_profile.preferences
        if prefs.tone not in ALLOWED_TONES:
            raise ValueError(f"tone must be one of {sorted(ALLOWED_TONES)}")
        if prefs.format not in ALLOWED_FORMATS:
            raise ValueError(f"format must be one of {sorted(ALLOWED_FORMATS)}")

        if not self.guidelines.must_include:
            raise ValueError("must_include must not be empty")
        if not 0 <= self.quality_targets.pass_threshold <= 100:
            raise ValueError("pass_threshold must be between 0 and 100")
        if self.quality_targets.min_action_items <= 0:
            raise ValueError("min_action_items must be positive")

        if not 0.0 <= self.intake_confidence <= 1.0:
            raise ValueError("intake_confidence must be between 0.0 and 1.0")

    def to_dict(self) -> dict:
        return {
            "topic": self.topic,
            "user_intent": self.user_intent,
            "persona_profile": {
                "goals": self.persona_profile.goals,
                "context": self.persona_profile.context,
                "preferences": {
                    "tone": self.persona_profile.preferences.tone,
                    "format": self.persona_profile.preferences.format,
                },
            },
            "guidelines": {
                "must_include": self.guidelines.must_include,
                "style_rules": self.guidelines.style_rules,
                "safety_rules": self.guidelines.safety_rules,
            },
            "quality_targets": {
                "min_action_items": self.quality_targets.min_action_items,
                "requires_metrics": self.quality_targets.requires_metrics,
                "pass_threshold": self.quality_targets.pass_threshold,
            },
            "risk_flags": self.risk_flags,
            "clarification_needed": self.clarification_needed,
            "intake_confidence": self.intake_confidence,
        }

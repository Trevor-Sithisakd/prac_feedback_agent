"""Input Generating Agent (Intake Crew).

Converts a raw user request into a normalized input packet for downstream crews.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from agent.input_layer.models import (
    Guidelines,
    InputPacket,
    PersonaProfile,
    Preferences,
    QualityTargets,
)
from agent.input_layer.schema import (
    BROAD_TOPICS,
    CLARIFICATION_CONFIDENCE_THRESHOLD,
    CRISIS_KEYWORDS,
    DEFAULT_MUST_INCLUDE,
    DEFAULT_SAFETY_RULES,
    DEFAULT_STYLE_RULES,
)
from agent.llm import LLMClient, build_default_llm_client


@dataclass
class IntakeRequest:
    raw_text: str
    topic: Optional[str] = None
    goals: Optional[List[str]] = None
    context: str = ""
    tone: str = "supportive"
    output_format: str = "hybrid"
    constraints: Optional[List[str]] = None


class IntakeCrew:
    """Generate validated input packets for the generation/evaluation pipeline."""

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client if llm_client is not None else build_default_llm_client()

    def process(self, request: IntakeRequest) -> InputPacket:
        llm_packet = self._llm_normalize(request)
        if llm_packet is not None:
            llm_packet.validate()
            return llm_packet
        return self._heuristic_normalize(request)

    def _llm_normalize(self, request: IntakeRequest) -> InputPacket | None:
        if self.llm_client is None:
            return None

        prompt = self._build_intake_prompt(request)
        try:
            raw = self.llm_client.complete(prompt)
            parsed = json.loads(raw)
        except Exception:
            return None

        try:
            packet = InputPacket(
                topic=parsed["topic"],
                user_intent=parsed["user_intent"],
                persona_profile=PersonaProfile(
                    goals=parsed["persona_profile"].get("goals", []),
                    context=parsed["persona_profile"].get("context", ""),
                    preferences=Preferences(
                        tone=self._sanitize_tone(parsed["persona_profile"].get("preferences", {}).get("tone", request.tone)),
                        format=self._sanitize_format(parsed["persona_profile"].get("preferences", {}).get("format", request.output_format)),
                    ),
                ),
                guidelines=Guidelines(
                    must_include=parsed["guidelines"].get("must_include", list(DEFAULT_MUST_INCLUDE)),
                    style_rules=parsed["guidelines"].get("style_rules", list(DEFAULT_STYLE_RULES)),
                    safety_rules=parsed["guidelines"].get("safety_rules", list(DEFAULT_SAFETY_RULES)),
                ),
                quality_targets=QualityTargets(
                    min_action_items=int(parsed["quality_targets"].get("min_action_items", 3)),
                    requires_metrics=bool(parsed["quality_targets"].get("requires_metrics", True)),
                    pass_threshold=int(parsed["quality_targets"].get("pass_threshold", 80)),
                ),
                risk_flags=parsed.get("risk_flags", ["none"]),
                clarification_needed=bool(parsed.get("clarification_needed", False)),
                intake_confidence=float(parsed.get("intake_confidence", 0.75)),
            )
            return packet
        except Exception:
            return None

    def _heuristic_normalize(self, request: IntakeRequest) -> InputPacket:
        topic = self._extract_topic(request)
        user_intent = self._extract_intent(request.raw_text)
        goals = request.goals or self._extract_goals(request.raw_text)

        risk_flags = self._detect_risks(request.raw_text)

        guideline_style_rules = DEFAULT_STYLE_RULES + (request.constraints or [])
        guidelines = Guidelines(
            must_include=list(DEFAULT_MUST_INCLUDE),
            style_rules=self._dedupe(guideline_style_rules),
            safety_rules=list(DEFAULT_SAFETY_RULES),
        )

        quality_targets = QualityTargets(
            min_action_items=3,
            requires_metrics=True,
            pass_threshold=80,
        )

        confidence = self._score_confidence(topic=topic, goals=goals, has_risk=bool(risk_flags))
        clarification_needed = self._clarification_needed(topic=topic, confidence=confidence)

        packet = InputPacket(
            topic=topic,
            user_intent=user_intent,
            persona_profile=PersonaProfile(
                goals=goals,
                context=request.context.strip(),
                preferences=Preferences(
                    tone=self._sanitize_tone(request.tone),
                    format=self._sanitize_format(request.output_format),
                ),
            ),
            guidelines=guidelines,
            quality_targets=quality_targets,
            risk_flags=risk_flags or ["none"],
            clarification_needed=clarification_needed,
            intake_confidence=confidence,
        )
        packet.validate()
        return packet

    def _build_intake_prompt(self, request: IntakeRequest) -> str:
        return (
            "Normalize this personal-development user request into JSON with keys: "
            "topic,user_intent,persona_profile,guidelines,quality_targets,risk_flags,"
            "clarification_needed,intake_confidence."
            f"\nRaw request: {request.raw_text}\n"
            f"Given topic: {request.topic}\nGiven goals: {request.goals}\n"
            f"Context: {request.context}\nTone: {request.tone}\nFormat: {request.output_format}\n"
            "Return only valid JSON."
        )

    def _extract_topic(self, request: IntakeRequest) -> str:
        if request.topic and request.topic.strip():
            return request.topic.strip()

        sentences = re.split(r"[.!?]\s+", request.raw_text.strip())
        for sentence in sentences:
            clean = sentence.strip()
            if clean:
                return clean[:120]

        return "General personal development"

    def _extract_intent(self, text: str) -> str:
        lowered = text.lower()
        if "feedback" in lowered:
            return "Get feedback on personal development"
        if "plan" in lowered:
            return "Create an actionable personal development plan"
        return "Improve personal development outcomes"

    def _extract_goals(self, text: str) -> List[str]:
        bullets = [part.strip(" -") for part in text.split("\n") if part.strip().startswith("-")]
        if bullets:
            return bullets[:5]

        matches = re.findall(r"\bto\s+([a-zA-Z][^,.!?]{3,60})", text)
        goals = [m.strip() for m in matches][:3]
        return goals if goals else ["Build consistent personal growth habits"]

    def _detect_risks(self, text: str) -> List[str]:
        lowered = text.lower()
        flags = []
        for kw in CRISIS_KEYWORDS:
            if kw in lowered:
                flags.append("crisis_language")
                break
        if any(word in lowered for word in ["worthless", "hopeless"]):
            flags.append("negative_self_talk")
        return self._dedupe(flags)

    def _score_confidence(self, topic: str, goals: List[str], has_risk: bool) -> float:
        score = 0.9
        if len(topic.split()) <= 2:
            score -= 0.2
        if topic.lower() in BROAD_TOPICS:
            score -= 0.25
        if not goals:
            score -= 0.2
        if has_risk:
            score -= 0.15
        return max(0.0, min(1.0, round(score, 2)))

    def _clarification_needed(self, topic: str, confidence: float) -> bool:
        topic_too_broad = topic.lower() in BROAD_TOPICS
        return topic_too_broad or confidence < CLARIFICATION_CONFIDENCE_THRESHOLD

    def _sanitize_tone(self, tone: str) -> str:
        allowed = {"supportive", "direct", "balanced"}
        return tone if tone in allowed else "supportive"

    def _sanitize_format(self, output_format: str) -> str:
        allowed = {"bullet", "narrative", "hybrid"}
        return output_format if output_format in allowed else "hybrid"

    def _dedupe(self, values: List[str]) -> List[str]:
        seen = set()
        out = []
        for value in values:
            if value not in seen:
                seen.add(value)
                out.append(value)
        return out


def build_input_packet(payload: Dict[str, Any], llm_client: LLMClient | None = None) -> dict:
    """Convenience entry point for integrations expecting dictionary IO."""
    req = IntakeRequest(
        raw_text=payload.get("raw_text", ""),
        topic=payload.get("topic"),
        goals=payload.get("goals"),
        context=payload.get("context", ""),
        tone=payload.get("tone", "supportive"),
        output_format=payload.get("output_format", "hybrid"),
        constraints=payload.get("constraints"),
    )
    packet = IntakeCrew(llm_client=llm_client).process(req)
    return packet.to_dict()

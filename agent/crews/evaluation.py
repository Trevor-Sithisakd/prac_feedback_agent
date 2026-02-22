"""Evaluation crew that scores draft quality and returns revision guidance."""

from __future__ import annotations

import json
from typing import Dict, List

from agent.llm import LLMClient, build_default_llm_client


class EvaluationCrew:
    """Evaluates generated drafts against quality criteria."""

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client if llm_client is not None else build_default_llm_client()

    def evaluate(self, draft: Dict, input_packet: Dict) -> Dict:
        llm_review = self._llm_evaluate(draft, input_packet)
        if llm_review is not None:
            return llm_review

        scores = {
            "relevance": self._score_relevance(draft, input_packet),
            "personalization": self._score_personalization(draft, input_packet),
            "actionability": self._score_actionability(draft),
            "safety": self._score_safety(draft, input_packet),
            "guideline_adherence": self._score_guideline_adherence(draft, input_packet),
        }

        overall = round(sum(scores.values()) / len(scores))
        major_issues: List[str] = []
        minor_issues: List[str] = []
        revision_instructions: List[str] = []

        if scores["actionability"] < 75:
            major_issues.append("Action plan lacks enough measurable steps")
            revision_instructions.append("Add concrete success metrics for every action")
        if scores["personalization"] < 70:
            minor_issues.append("Draft could be more personalized to user context")
            revision_instructions.append("Personalize summary and actions using persona context")
        if input_packet.get("risk_flags") and "crisis_language" in input_packet["risk_flags"]:
            major_issues.append("Safety escalation required for crisis language")
            revision_instructions.append("Add crisis-support escalation language and avoid overconfident coaching")

        passed = overall >= input_packet["quality_targets"]["pass_threshold"] and not major_issues

        return {
            "overall_score": overall,
            "pass": passed,
            "criterion_scores": scores,
            "major_issues": major_issues,
            "minor_issues": minor_issues,
            "revision_instructions": revision_instructions,
            "confidence": 0.82,
        }

    def _llm_evaluate(self, draft: Dict, input_packet: Dict) -> Dict | None:
        if self.llm_client is None:
            return None
        prompt = (
            "Evaluate draft quality and return strict JSON with keys: "
            "overall_score,pass,criterion_scores,major_issues,minor_issues,revision_instructions,confidence.\n"
            f"Draft: {json.dumps(draft)}\n"
            f"Input packet: {json.dumps(input_packet)}\n"
            "Use rubric: relevance, personalization, actionability, safety, guideline_adherence."
        )
        try:
            return json.loads(self.llm_client.complete(prompt))
        except Exception:
            return None

    def _score_relevance(self, draft: Dict, input_packet: Dict) -> int:
        topic = input_packet["topic"].lower()
        return 90 if any(word in draft["summary"].lower() for word in topic.split()[:2]) else 70

    def _score_personalization(self, draft: Dict, input_packet: Dict) -> int:
        goals = input_packet["persona_profile"].get("goals", [])
        if not goals:
            return 70
        matched = sum(1 for g in goals if any(g.lower().split()[0] in a["action"].lower() for a in draft["action_plan"]))
        return min(95, 65 + matched * 10)

    def _score_actionability(self, draft: Dict) -> int:
        actions = draft.get("action_plan", [])
        if not actions:
            return 30
        with_metrics = sum(1 for a in actions if a.get("success_metric"))
        return min(95, 60 + int(35 * (with_metrics / len(actions))))

    def _score_safety(self, draft: Dict, input_packet: Dict) -> int:
        if "crisis_language" in input_packet.get("risk_flags", []):
            return 60
        if any("diagnosis" in str(v).lower() for v in draft.values()):
            return 50
        return 90

    def _score_guideline_adherence(self, draft: Dict, input_packet: Dict) -> int:
        must_include = input_packet["guidelines"]["must_include"]
        present = sum(1 for key in must_include if key in draft and draft.get(key))
        return round((present / len(must_include)) * 100)

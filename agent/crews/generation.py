"""Generation crew for personal development feedback drafts."""

from __future__ import annotations

import json
from typing import Dict, List

from agent.llm import LLMClient, build_default_llm_client, parse_json_object


class GenerationCrew:
    """Creates and revises draft outputs from normalized input packets."""

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client if llm_client is not None else build_default_llm_client()

    def generate(self, input_packet: Dict) -> Dict:
        llm_draft = self._llm_generate(input_packet)
        if llm_draft is not None:
            return self._normalize_draft(llm_draft)
        return self._heuristic_generate(input_packet)

    def revise(self, previous_draft: Dict, revision_instructions: List[str], input_packet: Dict) -> Dict:
        llm_revision = self._llm_revise(previous_draft, revision_instructions, input_packet)
        if llm_revision is not None:
            return self._normalize_draft(llm_revision)

        revised = dict(previous_draft)
        revised["summary"] = previous_draft["summary"] + " (revised using reviewer feedback)"

        for instruction in revision_instructions:
            lowered = instruction.lower()
            if "metric" in lowered:
                for item in revised["action_plan"]:
                    if not item.get("success_metric"):
                        item["success_metric"] = "Track progress weekly using a 1-10 self-rating"
            if "personal" in lowered or "personalize" in lowered:
                context = input_packet["persona_profile"].get("context", "")
                if context and context not in revised["summary"]:
                    revised["summary"] += f" Context considered: {context}."

        return revised

    def _llm_generate(self, input_packet: Dict) -> Dict | None:
        if self.llm_client is None:
            return None
        prompt = (
            "Generate personal development feedback JSON with keys: "
            "topic,summary,strengths,growth_areas,action_plan,reflection_questions,tone_check.\n"
            f"Input packet: {json.dumps(input_packet)}\n"
            "Return only valid JSON."
        )
        try:
            return parse_json_object(self.llm_client.complete(prompt))
        except Exception:
            return None

    def _llm_revise(self, previous_draft: Dict, revision_instructions: List[str], input_packet: Dict) -> Dict | None:
        if self.llm_client is None:
            return None
        prompt = (
            "Revise the draft based on revision instructions and return valid JSON with keys: "
            "topic,summary,strengths,growth_areas,action_plan,reflection_questions,tone_check.\n"
            f"Draft: {json.dumps(previous_draft)}\n"
            f"Revision instructions: {json.dumps(revision_instructions)}\n"
            f"Input packet: {json.dumps(input_packet)}\n"
            "Return only valid JSON."
        )
        try:
            return parse_json_object(self.llm_client.complete(prompt))
        except Exception:
            return None

    def _heuristic_generate(self, input_packet: Dict) -> Dict:
        topic = input_packet["topic"]
        goals = input_packet["persona_profile"]["goals"]
        tone = input_packet["persona_profile"]["preferences"]["tone"]

        strengths = [
            "You are actively seeking structured feedback",
            "You are willing to translate feedback into action",
        ]
        growth_areas = [
            "Improve consistency through smaller repeatable habits",
            "Track outcomes with clear weekly metrics",
        ]

        action_plan = self._build_action_plan(topic, goals)
        reflection_questions = [
            "What was one small win this week and why did it work?",
            "What obstacle repeated most often and how can you reduce its impact?",
            "Which next action feels realistic enough to start today?",
        ]

        return {
            "topic": topic,
            "summary": f"Here is a {tone} personal development plan for: {topic}",
            "strengths": strengths,
            "growth_areas": growth_areas,
            "action_plan": action_plan,
            "reflection_questions": reflection_questions,
            "tone_check": tone,
        }

    def _build_action_plan(self, topic: str, goals: List[str]) -> List[Dict]:
        base_goals = goals if goals else [f"Make steady progress on {topic}"]
        plan = []
        for goal in base_goals[:3]:
            plan.append(
                {
                    "action": f"Schedule a focused block for: {goal}",
                    "rationale": "Time-blocking improves consistency and follow-through.",
                    "time_horizon": "this week",
                    "success_metric": "Complete at least 3 focused sessions this week",
                }
            )
        return plan

    def _normalize_draft(self, draft: Dict) -> Dict:
        normalized = dict(draft)
        action_plan = normalized.get("action_plan")
        if not isinstance(action_plan, list):
            action_plan = [action_plan] if action_plan else []

        normalized_plan: List[Dict] = []
        for item in action_plan:
            if isinstance(item, dict):
                normalized_plan.append(
                    {
                        "action": str(item.get("action", "")).strip() or "Complete one focused improvement step",
                        "rationale": str(item.get("rationale", "")).strip() or "Build consistency through repetition.",
                        "time_horizon": str(item.get("time_horizon", "")).strip() or "this week",
                        "success_metric": str(item.get("success_metric", "")).strip()
                        or "Track completion rate weekly",
                    }
                )
                continue

            text = str(item).strip()
            if text:
                normalized_plan.append(
                    {
                        "action": text,
                        "rationale": "Build consistency through repetition.",
                        "time_horizon": "this week",
                        "success_metric": "Track completion rate weekly",
                    }
                )

        if not normalized_plan:
            normalized_plan = self._build_action_plan(
                normalized.get("topic", "personal development"),
                [],
            )

        normalized["action_plan"] = normalized_plan
        return normalized

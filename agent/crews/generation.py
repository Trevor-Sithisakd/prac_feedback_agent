"""Generation crew for personal development feedback drafts."""

from __future__ import annotations

from typing import Dict, List


class GenerationCrew:
    """Creates and revises draft outputs from normalized input packets."""

    def generate(self, input_packet: Dict) -> Dict:
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

    def revise(self, previous_draft: Dict, revision_instructions: List[str], input_packet: Dict) -> Dict:
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

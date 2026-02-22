import json
import unittest

from agent.crews.evaluation import EvaluationCrew
from agent.crews.generation import GenerationCrew
from agent.crews.intake import IntakeCrew, IntakeRequest
from agent.llm import parse_json_object


class FakeLLM:
    def complete(self, prompt: str) -> str:
        if "Normalize this personal-development user request" in prompt:
            return json.dumps(
                {
                    "topic": "Improve confidence at work",
                    "user_intent": "Get structured personal development feedback",
                    "persona_profile": {
                        "goals": ["Speak up in two meetings weekly"],
                        "context": "Early-career engineer",
                        "preferences": {"tone": "supportive", "format": "bullet"},
                    },
                    "guidelines": {
                        "must_include": ["summary", "strengths", "growth_areas", "action_plan", "reflection_questions"],
                        "style_rules": ["specific", "actionable"],
                        "safety_rules": ["no diagnosis"],
                    },
                    "quality_targets": {"min_action_items": 3, "requires_metrics": True, "pass_threshold": 80},
                    "risk_flags": ["none"],
                    "clarification_needed": False,
                    "intake_confidence": 0.92,
                }
            )
        if "Generate personal development feedback JSON" in prompt:
            return json.dumps(
                {
                    "topic": "Improve confidence at work",
                    "summary": "LLM generated draft",
                    "strengths": ["Motivated"],
                    "growth_areas": ["Communication confidence"],
                    "action_plan": [
                        {
                            "action": "Practice concise updates before standup",
                            "rationale": "Build confidence with repetition",
                            "time_horizon": "this week",
                            "success_metric": "Deliver 3 concise updates",
                        }
                    ],
                    "reflection_questions": ["What improved this week?"],
                    "tone_check": "supportive",
                }
            )
        if "Evaluate draft quality" in prompt:
            return json.dumps(
                {
                    "overall_score": 88,
                    "pass": True,
                    "criterion_scores": {
                        "relevance": 90,
                        "personalization": 85,
                        "actionability": 87,
                        "safety": 90,
                        "guideline_adherence": 88,
                    },
                    "major_issues": [],
                    "minor_issues": [],
                    "revision_instructions": [],
                    "confidence": 0.9,
                }
            )
        raise AssertionError("Unexpected prompt")


class FakeLLMStringActionPlan(FakeLLM):
    def complete(self, prompt: str) -> str:
        if "Generate personal development feedback JSON" in prompt:
            return json.dumps(
                {
                    "topic": "Improve confidence at work",
                    "summary": "LLM generated draft",
                    "strengths": ["Motivated"],
                    "growth_areas": ["Communication confidence"],
                    "action_plan": ["Practice one concise update before standup"],
                    "reflection_questions": ["What improved this week?"],
                    "tone_check": "supportive",
                }
            )
        return super().complete(prompt)


class FakeLLMFencedJSON(FakeLLM):
    def complete(self, prompt: str) -> str:
        if "Generate personal development feedback JSON" in prompt:
            return """```json
{
  "topic": "Improve confidence at work",
  "summary": "LLM generated draft",
  "strengths": ["Motivated"],
  "growth_areas": ["Communication confidence"],
  "action_plan": [{
    "action": "Practice concise updates before standup",
    "rationale": "Build confidence with repetition",
    "time_horizon": "this week",
    "success_metric": "Deliver 3 concise updates"
  }],
  "reflection_questions": ["What improved this week?"],
  "tone_check": "supportive"
}
```"""
        return super().complete(prompt)


class LLMBaselineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.llm = FakeLLM()

    def test_intake_uses_llm_baseline(self):
        crew = IntakeCrew(llm_client=self.llm)
        packet = crew.process(IntakeRequest(raw_text="help me improve confidence at work"))
        self.assertEqual(packet.topic, "Improve confidence at work")
        self.assertEqual(packet.intake_confidence, 0.92)

    def test_generation_and_evaluation_use_llm_baseline(self):
        input_packet = IntakeCrew(llm_client=self.llm).process(
            IntakeRequest(raw_text="help me improve confidence at work")
        ).to_dict()

        draft = GenerationCrew(llm_client=self.llm).generate(input_packet)
        self.assertEqual(draft["summary"], "LLM generated draft")

        review = EvaluationCrew(llm_client=self.llm).evaluate(draft, input_packet)
        self.assertTrue(review["pass"])
        self.assertEqual(review["overall_score"], 88)

    def test_generation_normalizes_string_action_plan_items_from_llm(self):
        llm = FakeLLMStringActionPlan()
        input_packet = IntakeCrew(llm_client=llm).process(
            IntakeRequest(raw_text="help me improve confidence at work")
        ).to_dict()

        draft = GenerationCrew(llm_client=llm).generate(input_packet)

        self.assertIsInstance(draft["action_plan"], list)
        self.assertIsInstance(draft["action_plan"][0], dict)
        self.assertIn("action", draft["action_plan"][0])

    def test_parse_json_object_supports_fenced_json(self):
        data = parse_json_object("""```json
        {"ok": true, "value": 3}
        ```""")
        self.assertTrue(data["ok"])
        self.assertEqual(data["value"], 3)

    def test_generation_accepts_fenced_json_from_llm(self):
        llm = FakeLLMFencedJSON()
        input_packet = IntakeCrew(llm_client=llm).process(
            IntakeRequest(raw_text="help me improve confidence at work")
        ).to_dict()

        draft = GenerationCrew(llm_client=llm).generate(input_packet)
        self.assertEqual(draft["summary"], "LLM generated draft")


if __name__ == "__main__":
    unittest.main()

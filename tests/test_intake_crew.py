import unittest

from agent.crews.intake import IntakeCrew, IntakeRequest, build_input_packet


class IntakeCrewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.crew = IntakeCrew()

    def test_process_generates_valid_packet(self):
        req = IntakeRequest(
            raw_text="I want feedback to improve consistency with exercise and sleep.",
            goals=["Exercise 4x weekly", "Sleep 7.5 hours/night"],
            context="Busy work schedule",
            tone="balanced",
            output_format="bullet",
        )

        packet = self.crew.process(req)

        self.assertEqual(packet.topic, "I want feedback to improve consistency with exercise and sleep.")
        self.assertEqual(packet.persona_profile.preferences.tone, "balanced")
        self.assertIn("action_plan", packet.guidelines.must_include)
        self.assertEqual(packet.risk_flags, ["none"])
        self.assertFalse(packet.clarification_needed)

    def test_broad_topic_triggers_clarification(self):
        req = IntakeRequest(raw_text="", topic="improve my life")
        packet = self.crew.process(req)

        self.assertTrue(packet.clarification_needed)
        self.assertLessEqual(packet.intake_confidence, 0.65)

    def test_risk_detection(self):
        req = IntakeRequest(raw_text="I feel hopeless and want to end my life")
        packet = self.crew.process(req)

        self.assertIn("crisis_language", packet.risk_flags)
        self.assertIn("negative_self_talk", packet.risk_flags)

    def test_build_input_packet_dict_interface(self):
        output = build_input_packet(
            {
                "raw_text": "Please give me feedback and a plan to improve confidence at work.",
                "constraints": ["brief"],
                "tone": "invalid-tone",
                "output_format": "invalid-format",
            }
        )

        self.assertEqual(output["persona_profile"]["preferences"]["tone"], "supportive")
        self.assertEqual(output["persona_profile"]["preferences"]["format"], "hybrid")
        self.assertIn("brief", output["guidelines"]["style_rules"])


if __name__ == "__main__":
    unittest.main()

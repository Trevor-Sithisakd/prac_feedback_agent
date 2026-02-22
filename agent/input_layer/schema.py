"""Input packet defaults and schema helpers for the intake layer."""

DEFAULT_MUST_INCLUDE = [
    "summary",
    "strengths",
    "growth_areas",
    "action_plan",
    "reflection_questions",
]

DEFAULT_STYLE_RULES = ["non-judgmental", "specific", "actionable"]
DEFAULT_SAFETY_RULES = ["no diagnosis", "no shaming language"]

CLARIFICATION_CONFIDENCE_THRESHOLD = 0.65

CRISIS_KEYWORDS = {
    "suicide",
    "self-harm",
    "kill myself",
    "hurt myself",
    "end my life",
}

BROAD_TOPICS = {
    "improve my life",
    "self improvement",
    "be better",
    "help me improve",
}

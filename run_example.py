from agent.crews.intake import build_input_packet
from agent.orchestrator.pipeline import SelfEvaluationPipeline

payload = {
    "raw_text": "I want feedback on becoming more consistent with programming.",
    "goals": ["Be more expereinced in producing projects and production ready code and skills"],
    "context": "I am looking for a job as a machine learning engineer",
    "tone": "supportive",
    "output_format": "hybrid",
}

input_packet = build_input_packet(payload)
result = SelfEvaluationPipeline().run(input_packet)

print("Status:", result["status"])
print("Summary:", result["final_output"]["summary"])
print("Top action:", result["final_output"]["action_plan"][0]["action"])

"""Pipeline orchestration for generation -> evaluation -> iteration -> finalize."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from agent.crews.evaluation import EvaluationCrew
from agent.crews.generation import GenerationCrew
from agent.storage.repository import FileRepository


@dataclass
class PipelineConfig:
    max_iterations: int = 4


class SelfEvaluationPipeline:
    def __init__(
        self,
        generation_crew: GenerationCrew | None = None,
        evaluation_crew: EvaluationCrew | None = None,
        repository: FileRepository | None = None,
        config: PipelineConfig | None = None,
    ) -> None:
        self.generation_crew = generation_crew or GenerationCrew()
        self.evaluation_crew = evaluation_crew or EvaluationCrew()
        self.repository = repository or FileRepository()
        self.config = config or PipelineConfig()

    def run(self, input_packet: Dict) -> Dict:
        state = {
            "input_packet": input_packet,
            "iteration": 0,
            "history": [],
        }

        draft = self.generation_crew.generate(input_packet)

        while state["iteration"] < self.config.max_iterations:
            review = self.evaluation_crew.evaluate(draft, input_packet)
            state["history"].append(
                {
                    "iteration": state["iteration"],
                    "draft": draft,
                    "review": review,
                }
            )

            if review["pass"]:
                final = {
                    "status": "validated",
                    "final_output": draft,
                    "final_review": review,
                }
                state["final"] = final
                state["status"] = "validated"
                self.repository.save_run(state)
                self.repository.save_final(final)
                return final

            draft = self.generation_crew.revise(
                previous_draft=draft,
                revision_instructions=review["revision_instructions"],
                input_packet=input_packet,
            )
            state["iteration"] += 1

        best = state["history"][-1]
        fallback = {
            "status": "max_iterations_reached",
            "final_output": best["draft"],
            "final_review": best["review"],
        }
        state["final"] = fallback
        state["status"] = "max_iterations_reached"
        self.repository.save_run(state)
        self.repository.save_final(fallback)
        return fallback

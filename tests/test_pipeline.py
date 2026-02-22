import tempfile
import unittest
from pathlib import Path

from agent.crews.evaluation import EvaluationCrew
from agent.crews.intake import build_input_packet
from agent.orchestrator.pipeline import PipelineConfig, SelfEvaluationPipeline
from agent.storage.repository import FileRepository


class PipelineTests(unittest.TestCase):
    def _make_input_packet(self):
        return build_input_packet(
            {
                "raw_text": "I want feedback to improve consistency at work and sleep better.",
                "goals": ["Sleep 7.5 hours", "Plan tomorrow each evening"],
                "context": "Working parent with limited evening time",
                "tone": "supportive",
            }
        )

    def test_pipeline_validates_and_saves_outputs(self):
        with tempfile.TemporaryDirectory() as td:
            repo = FileRepository(base_dir=Path(td))
            pipe = SelfEvaluationPipeline(repository=repo)
            result = pipe.run(self._make_input_packet())

            self.assertEqual(result["status"], "validated")
            self.assertTrue((Path(td) / "final").exists())
            self.assertGreaterEqual(len(repo.list_runs()), 1)

    def test_pipeline_falls_back_after_max_iterations(self):
        class AlwaysFailEvaluation(EvaluationCrew):
            def evaluate(self, draft, input_packet):
                res = super().evaluate(draft, input_packet)
                res["pass"] = False
                res["major_issues"] = ["Forced failure"]
                res["revision_instructions"] = ["Add more detail"]
                return res

        with tempfile.TemporaryDirectory() as td:
            repo = FileRepository(base_dir=Path(td))
            pipe = SelfEvaluationPipeline(
                repository=repo,
                evaluation_crew=AlwaysFailEvaluation(),
                config=PipelineConfig(max_iterations=2),
            )
            result = pipe.run(self._make_input_packet())

            self.assertEqual(result["status"], "max_iterations_reached")


if __name__ == "__main__":
    unittest.main()

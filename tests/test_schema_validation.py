import json
import unittest
from pathlib import Path


class SchemaFilesTests(unittest.TestCase):
    def test_schema_files_are_valid_json_and_have_required_keys(self):
        draft = json.loads(Path("agent/schemas/draft_schema.json").read_text())
        review = json.loads(Path("agent/schemas/review_schema.json").read_text())

        self.assertEqual(draft["type"], "object")
        self.assertIn("required", draft)
        self.assertIn("action_plan", draft["properties"])

        self.assertEqual(review["type"], "object")
        self.assertIn("required", review)
        self.assertIn("overall_score", review["properties"])


if __name__ == "__main__":
    unittest.main()

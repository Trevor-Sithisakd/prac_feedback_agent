# Personal Development Feedback Agent

An AI-agent project focused on generating high-quality, actionable feedback for personal development topics.

## What this project is
This repository implements a multi-stage workflow where one crew generates a draft, another evaluates it, the draft is iterated with feedback, and validated output is saved.

## Implemented workflow
1. **Generate initial output** from normalized input packet.
2. **Evaluate output** with rubric-based scoring.
3. **Iterate with feedback** until pass criteria are met (or max iterations reached).
4. **Finalize and save** output and review artifacts.

## Code structure
- `agent/input_layer/`: input normalization and validation (`InputPacket` contract)
- `agent/crews/intake.py`: Input Generating Agent (Intake Crew)
- `agent/crews/generation.py`: Generation Crew
- `agent/crews/evaluation.py`: Evaluation Crew
- `agent/orchestrator/pipeline.py`: orchestration loop
- `agent/storage/repository.py`: file-based persistence
- `agent/schemas/`: JSON schema contracts for draft/review outputs
- `agent/prompts/`: prompt templates for generation/evaluation
- `tests/`: unit tests for intake, pipeline, and schema artifacts

## Run tests
```bash
python -m unittest discover -s tests -v
```

## User intervention / setup notes
### API keys (if you want real LLM integration)
Current implementation is deterministic and does **not** require API keys.

To connect real model providers later, you will need to add credentials (example names):
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GOOGLE_API_KEY`

Recommended approach:
1. Add provider clients in `agent/crews/generation.py` and `agent/crews/evaluation.py`.
2. Read keys from environment variables.
3. Keep a deterministic fallback for offline testing.

### Safety policy input
You should provide your team’s final safety/escalation policy text for crisis-language cases, then wire it into generation/evaluation prompts.

## Documentation
- Detailed architecture scaffold and rationale: [`docs/agent-scaffold.md`](docs/agent-scaffold.md)

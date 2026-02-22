# Personal Development Feedback Agent

An AI-agent project focused on generating high-quality, actionable feedback for personal development topics.

## What this project is
This repository implements a multi-stage workflow where one crew generates a draft, another evaluates it, the draft is iterated with feedback, and validated output is saved.

## Implemented workflow
1. **Generate initial output** from normalized input packet.
2. **Evaluate output** with rubric-based scoring.
3. **Iterate with feedback** until pass criteria are met (or max iterations reached).
4. **Finalize and save** output and review artifacts.

## LLM baseline behavior
- Intake, generation, and evaluation crews are now **LLM-first**.
- If `OPENAI_API_KEY` is present, crews use the configured model (`OPENAI_MODEL`, default `gpt-4o-mini`) via `agent/llm.py`.
- If no API key is present or an LLM call fails, crews fall back to deterministic local logic so tests and offline development still work.

## Code structure
- `agent/llm.py`: shared LLM client abstraction + OpenAI chat client + default builder
- `agent/input_layer/`: input normalization and validation (`InputPacket` contract)
- `agent/crews/intake.py`: Input Generating Agent (Intake Crew), LLM-first normalization
- `agent/crews/generation.py`: Generation Crew, LLM-first draft/revision
- `agent/crews/evaluation.py`: Evaluation Crew, LLM-first scoring/review
- `agent/orchestrator/pipeline.py`: orchestration loop
- `agent/storage/repository.py`: file-based persistence
- `agent/schemas/`: JSON schema contracts for draft/review outputs
- `agent/prompts/`: prompt templates for generation/evaluation
- `tests/`: unit tests for intake, pipeline, schema artifacts, and LLM baseline behavior

## Run tests
```bash
python -m unittest discover -s tests -v
```

## User intervention / setup notes
### Required to run with real LLMs
Set environment variables before running crews/pipeline with live models:
- `OPENAI_API_KEY` (required for live LLM path)
- `OPENAI_MODEL` (optional, defaults to `gpt-4o-mini`)

Example:
```bash
export OPENAI_API_KEY="<your-key>"
export OPENAI_MODEL="gpt-4o-mini"
```

### Optional team inputs still needed
- Final crisis/escalation safety policy language (to harden prompts/reviewer policy)
- Provider choice and key rotation policy for production

## Documentation
- Detailed architecture scaffold and rationale: [`docs/agent-scaffold.md`](docs/agent-scaffold.md)

# Personal Development Feedback Agent

An AI-agent project focused on generating high-quality, actionable feedback for personal development topics.

## What this project is
This repository is for an automated workflow where one agent generates a draft, another evaluates it against quality criteria, and the draft is iterated until it meets the validation threshold.

## Core workflow
1. **Generate initial output** from a topic and guidelines.
2. **Evaluate output** with a reviewer crew using a scoring rubric.
3. **Iterate with feedback** until pass criteria are met (or max iterations reached).
4. **Finalize and save** validated output with review metadata.

## Project status
Scaffolding/design stage. Implementation modules can be organized under:
- `agent/crews`
- `agent/orchestrator`
- `agent/schemas`
- `agent/storage`

## Documentation
- Detailed scaffold (architecture, schemas, pseudocode, prompts, guardrails):
  - [`docs/agent-scaffold.md`](docs/agent-scaffold.md)

## Scope and safety
This agent is specialized for **personal development feedback** and should use supportive, non-judgmental, practical language. It is not a replacement for professional mental health care.

## Implemented (Input layer)
- `agent/input_layer/models.py`: input packet data model + validation
- `agent/input_layer/schema.py`: defaults, safety keyword sets, thresholds
- `agent/crews/intake.py`: intake crew to normalize raw requests into structured `input_packet_vN`-style output
- `tests/test_intake_crew.py`: unit tests for intake behavior

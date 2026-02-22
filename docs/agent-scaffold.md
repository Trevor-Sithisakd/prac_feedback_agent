# Personal Development Self-Evaluation Agent Scaffold

This repository contains a practical scaffold for an AI agent workflow that generates content, evaluates it, iterates with feedback, and finalizes approved outputs.

## Purpose
Build an automated **self-evaluation system** specialized in **personal development feedback** (e.g., growth plans, habits, reflection summaries, strengths/areas-to-improve coaching).

---

## High-Level Workflow

1. **Generate Initial Output**  
   A *Generation Crew* creates an initial draft from a topic and quality guidelines.
2. **Evaluate Output**  
   An *Evaluation Crew* scores and critiques the draft against explicit criteria.
3. **Iterate with Feedback**  
   The *Generation Crew* revises the draft using structured feedback until pass threshold or max retries.
4. **Finalize and Save**  
   Once validated, the final output and evaluation metadata are persisted for reuse.

---

## Suggested Architecture

### 1) Input Layer
- `topic`: what the user wants help with (e.g., “improve consistency with exercise”).
- `guidelines`: required format, tone, constraints, and evaluation rubric.
- `persona_profile` (optional): goals, context, values, preferred coaching style.

### 1A) Input Generating Agent (Intake Crew)
This is the component that *builds high-quality inputs* for the rest of the pipeline. It converts messy user requests into normalized, validated fields the Generation Crew can reliably use.

Responsibilities:
- Collect raw request data (free text, optional profile data, channel metadata).
- Extract or infer `topic`, `goals`, constraints, preferred tone, and desired output depth.
- Generate a rubric-aligned `guidelines` object that the evaluator can score against.
- Run safety checks (harmful language, crisis indicators, unrealistic asks) and add escalation flags.
- Validate schema and confidence; route low-confidence cases to a clarification step.

**Intake output contract (`input_packet_vN`)**
```json
{
  "topic": "string",
  "user_intent": "string",
  "persona_profile": {
    "goals": ["..."],
    "context": "string",
    "preferences": {
      "tone": "supportive|direct|balanced",
      "format": "bullet|narrative|hybrid"
    }
  },
  "guidelines": {
    "must_include": ["summary", "strengths", "growth_areas", "action_plan", "reflection_questions"],
    "style_rules": ["non-judgmental", "specific", "actionable"],
    "safety_rules": ["no diagnosis", "no shaming language"]
  },
  "quality_targets": {
    "min_action_items": 3,
    "requires_metrics": true,
    "pass_threshold": 80
  },
  "risk_flags": ["none"],
  "clarification_needed": false,
  "intake_confidence": 0.0
}
```

**How to build it (practical checklist)**
1. Define a strict input schema (`input_packet_vN`) and validate every request.
2. Build a parser prompt that maps raw user text into schema fields.
3. Add deterministic post-processing (defaults, enums, field length limits).
4. Add safety classifier + escalation paths before generation starts.
5. Add confidence scoring; if low confidence, ask targeted clarifying questions.
6. Persist the normalized packet so every iteration uses the same baseline context.

**Clarification loop trigger examples**
- Topic is too broad (e.g., “help me improve my life”).
- Conflicting constraints (e.g., “brief response” + “deep weekly plan”).
- Missing success criteria (no measurable outcome requested).

### 2) Generation Crew (Creator)
Responsible for producing:
- A personalized development response.
- Actionable recommendations.
- Reflection prompts.
- Measurable next steps.

**Output contract (`draft_vN`)**
```json
{
  "topic": "string",
  "summary": "string",
  "strengths": ["..."],
  "growth_areas": ["..."],
  "action_plan": [
    {
      "action": "string",
      "rationale": "string",
      "time_horizon": "this week|this month|quarter",
      "success_metric": "string"
    }
  ],
  "reflection_questions": ["..."],
  "tone_check": "supportive|direct|balanced"
}
```

### 3) Evaluation Crew (Reviewer)
Evaluates quality and validity with a rubric such as:
- Relevance to topic
- Personalization depth
- Actionability
- Evidence/logic quality
- Emotional safety and supportive language
- Bias/stereotype safety
- Guideline adherence

**Evaluation contract (`review_vN`)**
```json
{
  "overall_score": 0,
  "pass": false,
  "criterion_scores": {
    "relevance": 0,
    "personalization": 0,
    "actionability": 0,
    "safety": 0,
    "guideline_adherence": 0
  },
  "major_issues": ["..."],
  "minor_issues": ["..."],
  "revision_instructions": ["Concrete edit requests..."],
  "confidence": 0.0
}
```

### 4) Orchestrator (Loop Controller)
Controls retries and state:
- Run generator.
- Run evaluator.
- If fail: attach `revision_instructions` and re-run generator.
- Stop when pass threshold is reached or `max_iterations` exceeded.

### 5) Persistence Layer
Store:
- Input context and versioned drafts
- Reviews per iteration
- Final approved response
- Audit trail (who/what changed and why)

Suggested stores:
- JSON files for prototyping
- SQLite/Postgres for production
- Object store for archival snapshots

---

## End-to-End Pseudocode

```python
def run_self_evaluation_pipeline(topic, guidelines, persona_profile=None):
    state = {
        "topic": topic,
        "guidelines": guidelines,
        "persona_profile": persona_profile,
        "iteration": 0,
        "history": []
    }

    max_iterations = 4
    pass_score = 80

    draft = generation_crew.generate(topic, guidelines, persona_profile)

    while state["iteration"] < max_iterations:
        review = evaluation_crew.evaluate(draft, guidelines, persona_profile)

        state["history"].append({
            "iteration": state["iteration"],
            "draft": draft,
            "review": review
        })

        if review["pass"] and review["overall_score"] >= pass_score:
            final = finalize_output(draft, review)
            save_result(state, final)
            return final

        draft = generation_crew.revise(
            previous_draft=draft,
            revision_instructions=review["revision_instructions"],
            guidelines=guidelines,
            persona_profile=persona_profile
        )
        state["iteration"] += 1

    fallback_final = escalate_or_finalize_best_effort(state)
    save_result(state, fallback_final)
    return fallback_final
```

---

## Prompt Scaffolding

### Generation Crew Prompt Template
Use this to produce the initial and revised draft:

```text
You are a personal development feedback specialist.

Task:
Create a response for the topic: {{topic}}

Follow these guidelines:
{{guidelines}}

User context (if provided):
{{persona_profile}}

Output requirements:
1) concise summary
2) strengths observed
3) growth areas
4) action plan with measurable success metrics
5) reflection questions

Tone:
Supportive, specific, non-judgmental, and practical.
Avoid medical/clinical claims. If uncertainty exists, acknowledge it.

Return strictly in the agreed JSON schema.
```

### Evaluation Crew Prompt Template
Use this to score and provide revision instructions:

```text
You are a strict quality reviewer for personal development coaching outputs.

Evaluate this draft against the rubric:
- relevance
- personalization
- actionability
- emotional safety
- guideline adherence

Guidelines:
{{guidelines}}
Draft:
{{draft_json}}
User context:
{{persona_profile}}

Scoring:
- 0-100 overall
- criterion-level scores

Decision:
- pass = true only if no major issue and overall >= 80

Return:
- major issues
- minor issues
- concrete revision instructions the generator can execute directly
- confidence score

Return strictly in the agreed JSON schema.
```

---

## Quality + Safety Guardrails (Personal Development)

- Do not shame, blame, or use absolute judgments.
- Prefer behavior-focused feedback over identity labels.
- Encourage realistic, incremental goals.
- Include safety fallback language for severe distress signals (route to human/professional support).
- Detect and remove biased assumptions about background, gender, culture, or ability.

---

## Minimal Folder Layout

```text
/agent
  /crews
    generation.py
    evaluation.py
  /orchestrator
    pipeline.py
  /schemas
    draft_schema.json
    review_schema.json
  /storage
    repository.py
  /prompts
    generation_prompt.txt
    evaluation_prompt.txt
/tests
  test_pipeline.py
  test_schema_validation.py
README.md
```

---

## First Implementation Milestones

1. Define schemas and validation.
2. Implement generator and evaluator stubs.
3. Add orchestrator retry loop.
4. Add persistence and audit logging.
5. Add tests for pass/fail iterations and max-iteration behavior.
6. Add sample runs for 3 personal development topics.

This gives you a clean scaffold you can implement with any LLM framework while preserving your required 4-stage structure.

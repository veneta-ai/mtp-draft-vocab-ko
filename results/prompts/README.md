# Prompts

Twenty Korean prompts, fixed from 2026-10-06 on so every row in the results table is comparable.

- `ko-general-10.jsonl` — everyday Korean writing: explanation, summary, business email, numbered list, translation into
  Korean, comparison table, dialogue, itinerary, finance explainer, proofreading.
- `ko-domain-10.jsonl` — operations wording from the domains our editions serve: telecom operations (3), retail (3),
  finance (2), manufacturing (1), power (1). Public, generic wording only; no customer text, no real figures.

Each line: `{"id", "kind", "prompt"}`. Run with temperature 0, thinking off, 200–512 output tokens, three repeats, report the
median per prompt and the median over the set. The prompts never change; a new set gets a new file name.

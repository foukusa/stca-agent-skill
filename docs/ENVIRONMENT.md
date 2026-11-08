# STCA host runtime

This technical reference is for agent hosts and maintainers. Users invoke every STCA workflow in natural language: select rules, upload data, request new rules, generate candidates or ask for verification. They do not configure Python, run commands, choose backend paths or deploy a model. STCA calculations use a CPU; generation uses the current host LLM.

The default runtime reuses an existing compatible Python 3.10+ environment and checks only the capabilities needed for the requested task. It prepares missing dependencies automatically and records the actual versions. An exact historical dependency snapshot is an explicit reproducibility option, not the normal usage requirement. The author implementation remains fixed to the reviewed source revision.

The bundled rule library and bilingual generation prompts are readable without scientific dependencies. The host uses `skills/stca/scripts/agent_runtime.py` for calculation. See the internal [host workflow](../skills/stca/references/agent_workflows.md) and [runtime reference](../skills/stca/references/platform-runtime.md).

After learning valid rules, the agent automatically returns reusable models, exact constraints and complete bilingual generation prompts. A single natural-language request can continue through host-LLM generation and frozen-rule verification.

STCA Agent Skill remains version **0.1.0**. Original repeat-unit SMILES are retained and H-cap is calculation-only.

# STCA calculation environment

This technical reference is for agent hosts and maintainers. Users invoke STCA in natural language; entering a Python path is optional. Calculations use a CPU, and generation uses the current AI assistant.

The agent starts through the bundled native launcher, so a Python executable does not have to be named `python` or `python3` on PATH. It searches a bounded set of known locations and available environment-manager records, then checks candidate interpreters. Successful environments are recorded and reused. Explicitly selected interpreters are validated without silently switching to another environment.

The runtime accepts compatible Python 3.10+ environments. Rule screening checks RDKit and MACCS behavior; learning also checks the numerical APIs. If preparation is required and permitted, dependencies are installed into a separate cache environment. Existing user environments are not modified. Discovery itself does not install software. If no usable interpreter or permitted preparation route is available, the agent reports the specific blocker.

The bundled rules and bilingual prompts are readable without scientific dependencies. The agent uses `scripts/launch_runtime.sh` on macOS/Linux or `scripts/launch_runtime.ps1` on Windows to start `scripts/agent_runtime.py`. WorkBuddy's packaged entry restores the complete rule resources before calculation. These are internal operations, not setup commands for ordinary users. See [agent workflows](../skills/stca/references/agent_workflows.md) and [runtime reference](../skills/stca/references/platform-runtime.md).

After learning valid rules, the agent returns reusable models, exact constraints, complete bilingual prompts and their screening results. A natural-language request can continue through current-LLM generation and frozen-rule verification.

Version remains **0.1.0**. Original polymer SMILES and attachment points are retained; H-cap is calculation-only. Already capped input remains as supplied.

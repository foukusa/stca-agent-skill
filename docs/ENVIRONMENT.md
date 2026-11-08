# STCA calculation environment

This technical reference is for agent hosts and maintainers. Users invoke STCA in natural language; entering a Python path is optional. Calculations use a CPU, and generation uses the current AI assistant.

The agent starts through the bundled native launcher, so a Python executable does not have to be named `python` or `python3` on PATH. It searches a bounded set of known locations and available environment-manager records, then checks candidate interpreters. Successful environments are recorded and reused. Explicitly selected interpreters are validated without silently switching to another environment.

The runtime accepts compatible Python 3.10+ environments. Rule screening checks RDKit and MACCS behavior; learning also checks the numerical APIs. If preparation is required and permitted, dependencies are installed into a separate cache environment. Existing user environments are not modified. Discovery itself does not install software. If no usable interpreter or permitted preparation route is available, the agent reports the specific blocker.

The bundled rules and bilingual prompts are readable without scientific dependencies. The agent uses `scripts/launch_runtime.sh` on macOS/Linux to start `scripts/agent_runtime.py`. WorkBuddy's packaged entry restores the complete rule resources before calculation. These are internal operations, not setup commands for ordinary users. See [agent workflows](../skills/stca/references/agent_workflows.md) and [runtime reference](../skills/stca/references/platform-runtime.md).

The package includes the unmodified author implementation and a trusted file-hash inventory. Ordinary loading verifies those files locally and does not run Git or download source. An explicitly selected external source must pass its own verification; an invalid explicit path is not silently replaced. Missing scientific Python dependencies may still require a permitted PyPI download.

WorkBuddy keeps its default runtime cache within the current task workspace. New cache and rule entries are written into unique directories, verified, and marked complete only after their required files are present; normal operation does not depend on renaming or deleting a temporary directory. A blocked write remains a permission error. The assistant reports the exact stage and affected path, preserves completed calculation files, and does not change verification code, fabricate Git metadata, or repeatedly retry blocked operations. A saved rule is reported as ready only after its completion record validates.

After learning valid rules, the agent returns reusable models, exact constraints, complete bilingual prompts and their screening results. A natural-language request can continue through current-LLM generation and frozen-rule verification.

Version remains **0.1.0**. Original polymer SMILES and attachment points are retained; H-cap is calculation-only. Already capped input remains as supplied.

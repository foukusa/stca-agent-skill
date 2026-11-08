# Install and use STCA

**Version 0.1.0** · [简体中文](INSTALL.zh-CN.md) · [Home](../README.md)

## Contents

- [Choose a package](#choose-a-package)
- [Codex](#codex)
- [DeepSeek Harness](#deepseek-harness)
- [WorkBuddy](#workbuddy)
- [ChatGPT desktop](#chatgpt-desktop)
- [Calculation environment](#calculation-environment)
- [Save and continue](#save-and-continue)
- [Natural-language examples](USAGE.md)

## Choose a package

Use a direct installation below. Store listing links will be added after the corresponding review and publication are complete.

| Platform | Download |
|---|---|
| Codex | [stca-codex-0.1.0.zip](../downloads/stca-codex-0.1.0.zip?raw=true) |
| DeepSeek Harness: local skill | [stca-deepseek-harness-0.1.0.zip](../downloads/stca-deepseek-harness-0.1.0.zip?raw=true) |
| DeepSeek Harness: plugin | [dsh-plugin-stca-0.1.0.tgz](../downloads/dsh-plugin-stca-0.1.0.tgz?raw=true) |
| WorkBuddy | [stca-workbuddy-0.1.1.zip](../downloads/stca-workbuddy-0.1.1.zip?raw=true) |
| ChatGPT desktop | [stca-openai-skill-0.1.0.zip](../downloads/stca-openai-skill-0.1.0.zip?raw=true) |

All STCA tasks accept natural language. The assistant handles calculation-environment discovery; you do not need to enter a Python path during installation.

## Codex

**Install from GitHub.** In Codex, send:

```text
Use $skill-installer to install https://github.com/foukusa/stca-agent-skill/tree/main/skills/stca
```

**Or install the ZIP.** Download and extract `stca-codex-0.1.0.zip`. Put its complete `stca` folder in your personal skill directory:

```text
~/.agents/skills/stca/SKILL.md
```

For use only in one project, put the same folder at `.agents/skills/stca` inside that project. On Windows, the personal location is `%USERPROFILE%\.agents\skills\stca`. Keep the scripts, references and assets beside `SKILL.md`; do not copy only the Markdown file.

Open `/skills` or type `$stca` to select STCA, then send:

```text
Use $stca. Start STCA.
```

This installs the local skill for Codex; no OpenAI directory submission is needed to use it. A future public plugin listing is a separate distribution route. See the [official OpenAI skill guide](https://learn.chatgpt.com/docs/build-skills).

## DeepSeek Harness

Choose **Git installation** or **downloaded skill ZIP**. Both make STCA available through `/stca`.

### Git installation

In **Plugins → Add plugin**, enter this repository address, install and enable STCA:

```text
https://github.com/foukusa/stca-agent-skill.git
```

With the DSH CLI and the `web` profile, the equivalent source installation is:

```bash
dsh plugin --profile web add github:foukusa/stca-agent-skill
```

Use your actual profile name in place of `web` when appropriate. The GitHub `/tree/main` page is a browsing address; use the repository address above in Add plugin.

### Install by npm package name

After npm publication, enter the following in **Plugins → Add plugin**:

```text
dsh-plugin-stca
```

The equivalent CLI command is:

```bash
dsh plugin --profile web add dsh-plugin-stca
```

Plugin-center link: — (to be added after listing).

<!-- DSH_PLUGIN_CENTER_URL: add the actual listing URL after publication. -->

### Downloaded skill ZIP

1. Download [stca-deepseek-harness-0.1.0.zip](../downloads/stca-deepseek-harness-0.1.0.zip?raw=true) and extract it.
2. Copy the complete `stca` folder into the DSH user skill root. With the default DSH home, the result is `~/.dsh/skills/stca/SKILL.md`. For a project-only skill, use `.dsh/skills/stca` under the project root. A custom DSH home or skill-root setting takes precedence.
3. Keep `scripts`, `references` and `assets` with `SKILL.md`. The filesystem skill provider must be enabled in the selected DSH profile.
4. Enter `/stca` or say “Start STCA”.

A local skill ZIP is installed by placing the extracted folder, not by pasting the ZIP into Add plugin.

### Downloaded plugin TGZ

If you prefer Add plugin without Git, download [dsh-plugin-stca-0.1.0.tgz](../downloads/dsh-plugin-stca-0.1.0.tgz?raw=true) and enter that file's full local path in Add plugin. For a CLI installation, run from the folder containing the download:

```bash
dsh plugin --profile web add ./dsh-plugin-stca-0.1.0.tgz
```

The TGZ is already a plugin package. It does not need to be extracted or repacked.

See the [official plugin installation guide](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/user/develop/basic/publish.md) and [filesystem skill guide](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/skill-filesystem/README.md).

## WorkBuddy

1. Open [WorkBuddy](https://www.workbuddy.cn/) and its skill management page.
2. Choose the action for adding and uploading a local skill package.
3. Select [stca-workbuddy-0.1.1.zip](../downloads/stca-workbuddy-0.1.1.zip?raw=true) directly, complete import and enable **STCA Polymer Rules and Design**. Do not extract it or wrap it in another folder before uploading.
4. Say “Start STCA”.

The package includes its referenced startup resources and logo in the upload layout. The public marketplace installation link will be added after review and publication.

See [official WorkBuddy instructions](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market).

## ChatGPT desktop

The [OpenAI skill ZIP](../downloads/stca-openai-skill-0.1.0.zip?raw=true) contains the same STCA workflow as the Codex skill ZIP. Use the skill creation/import options available in your desktop app, then select STCA. For a future public plugin listing, use the supported plugin installation surface when its listing is available. See the [official skill guide](https://learn.chatgpt.com/docs/build-skills) and [plugin guide](https://learn.chatgpt.com/docs/plugins).

## Calculation environment

At the first calculation, the assistant automatically discovers a suitable local Python environment and checks the dependencies needed by your task. It can reuse an existing RDKit environment, including a discovered Conda environment, and remembers a successful choice. If dependencies are missing, it prepares a separate environment when the platform allows it; your existing environments are not modified.

You normally do not fill in any Python path. To use a particular environment, say “Use the Python interpreter at this path” and provide it. That explicit choice is checked and retained; a failure is explained instead of silently selecting another interpreter. If automatic discovery and preparation cannot complete, the assistant reports the specific missing requirement.

Reading existing rules and prompts does not require RDKit. Structural screening and exact verification require RDKit; learning rules also needs the numerical analysis dependencies. Calculations use a CPU. Generation uses the current AI assistant and needs no separate LLM API configuration.

## Save and continue

The menu order is **1 Upload data and learn, 2 Screen with existing rules, 3 Generate with existing rules**.

- Task 1 returns STCA and WRAcc rules separately, with each tier's numeric physical cutoff, comparison, unit, screening results and recommendation. If percentages are omitted, it uses Top or Bottom 10%, 20% and 30%; you can specify other percentages, such as 15% or 25%. Results preserve the original table, polymer SMILES, unmet rule conditions and uncomputable records. The rules are saved before returning to the menu.
- Task 2 screens uploaded candidates with bundled rules or My rules. The two methods' results remain separate, and the recommended method is clearly identified.
- Task 3 first shows the rule catalog. After selecting a rule, choose **Preview and confirm** to review and adjust the complete prompt before saying “Confirm and generate,” or **Generate directly** to have the current LLM generate and verify immediately. Both modes preserve every proposal and unmet rule condition, then return to the menu.

Copy a short request from the [natural-language examples](USAGE.md). “Main menu” or “Back” preserves saved rules. To change sessions or platforms, download the rule bundle and upload it in the new session, then ask the assistant to load it.

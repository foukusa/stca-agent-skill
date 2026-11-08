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

Choose your platform below. Every package link opens a file page in this GitHub repository’s [downloads folder](https://github.com/foukusa/stca-agent-skill/tree/main/downloads). On that page, click **Download raw file** (the download button) to save the ZIP or TGZ locally. Alternatively, use **Code → Download ZIP** on the [repository home](https://github.com/foukusa/stca-agent-skill) and find the release files under `downloads`. WorkBuddy’s marketplace link will be added after publication.

| Platform | Download |
|---|---|
| Codex | [stca-codex-0.1.0.zip](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/stca-codex-0.1.0.zip) |
| DeepSeek Harness: local skill | [stca-deepseek-harness-0.1.0.zip](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/stca-deepseek-harness-0.1.0.zip) |
| DeepSeek Harness: plugin | [dsh-plugin-stca-0.1.0.tgz](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/dsh-plugin-stca-0.1.0.tgz) |
| WorkBuddy | [stca-workbuddy-0.1.1.zip](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/stca-workbuddy-0.1.1.zip) |
| ChatGPT desktop | [stca-openai-skill-0.1.0.zip](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/stca-openai-skill-0.1.0.zip) |

All STCA tasks accept natural language. The assistant handles calculation-environment discovery; you do not need to enter a Python path during installation.

## Codex

1. Open a Codex conversation.
2. For GitHub installation, send:

```text
Use $skill-installer to install https://github.com/foukusa/stca-agent-skill/tree/main/skills/stca
```

3. Alternatively, download and extract `stca-codex-0.1.0.zip`. Put its complete `stca` folder in your personal skill directory:

```text
~/.agents/skills/stca/SKILL.md
```

In Finder, choose **Go → Go to Folder…** and enter `~/.agents/skills`. Create the folder if needed, then place the complete `stca` folder there. For use only in one project, put it at `.agents/skills/stca` inside that project. Keep the scripts, references and assets beside `SKILL.md`.

4. Open `/skills` or type `$stca` to select STCA, then send:

```text
Use $stca. Start STCA.
```

See the [official skill guide](https://learn.chatgpt.com/docs/build-skills) for Codex’s skill-discovery behavior.

## DeepSeek Harness

Choose **Git installation** or **downloaded skill ZIP**. Both make STCA available through `/stca`.

### Git installation

1. Open **Plugins → Add plugin**.
2. Enter this repository address and install the plugin:


```text
https://github.com/foukusa/stca-agent-skill.git
```

3. Enable STCA in the profile you use and enter `/stca`.

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

1. Download [stca-deepseek-harness-0.1.0.zip](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/stca-deepseek-harness-0.1.0.zip) and extract it.
2. Copy the complete `stca` folder into the DSH user skill root. With the default DSH home, the result is `~/.dsh/skills/stca/SKILL.md`. For a project-only skill, use `.dsh/skills/stca` under the project root. A custom DSH home or skill-root setting takes precedence.
3. Keep `scripts`, `references` and `assets` with `SKILL.md`. The filesystem skill provider must be enabled in the selected DSH profile.
4. Enter `/stca` or say “Start STCA”.

A local skill ZIP is installed by placing the extracted folder, not by pasting the ZIP into Add plugin.

### Downloaded plugin TGZ

If you prefer Add plugin without Git, download [dsh-plugin-stca-0.1.0.tgz](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/dsh-plugin-stca-0.1.0.tgz) and enter that file's full local path in Add plugin. For a CLI installation, run from the folder containing the download:

```bash
dsh plugin --profile web add ./dsh-plugin-stca-0.1.0.tgz
```

The TGZ is already a plugin package. It does not need to be extracted or repacked.

See the [official plugin installation guide](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/user/develop/basic/publish.md) and [filesystem skill guide](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/skill-filesystem/README.md).

## WorkBuddy

1. Open [WorkBuddy](https://www.workbuddy.cn/) and its skill management page.
2. Choose the action for adding and uploading a local skill package.
3. Open [stca-workbuddy-0.1.1.zip](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/stca-workbuddy-0.1.1.zip) in the repository and click **Download raw file**. Select that downloaded ZIP in WorkBuddy, complete import and enable **STCA Polymer Rules and Design**. Keep the ZIP intact for upload.
4. Say “Start STCA”.

The package includes its referenced startup resources and logo in the upload layout. The public marketplace installation link will be added after review and publication.

See [official WorkBuddy instructions](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market).

## ChatGPT desktop

1. Open the [OpenAI skill ZIP](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/stca-openai-skill-0.1.0.zip) in this repository and click **Download raw file**.
2. If your ChatGPT desktop app provides local skill creation/import, import the ZIP there and enable STCA. Availability depends on your app and account.
3. Select STCA and describe the task. Calculations need file access and a command-execution environment; an ordinary file attachment alone does not install or execute the skill.

The OpenAI skill ZIP and Codex skill ZIP contain the same STCA workflow. If local skill import is unavailable in your ChatGPT app, use the Codex installation above. See the [official skill guide](https://learn.chatgpt.com/docs/build-skills).

## Calculation environment

Calculations support CPU execution with Python 3.10 or later; Conda is optional. At the first calculation, the assistant automatically discovers a suitable local Python environment and checks the dependencies needed by your task. It can reuse an existing RDKit environment, including a discovered Conda environment, and remembers a successful choice. If dependencies are missing, it prepares a separate environment when the platform allows it; your existing environments are not modified.

You normally do not fill in any Python path. To use a particular environment, say “Use the Python interpreter at this path” and provide it. That explicit choice is checked and retained; a failure is explained instead of silently selecting another interpreter. If automatic discovery and preparation cannot complete, the assistant reports the specific missing requirement.

Reading existing rules and prompts does not require RDKit. Structural screening and exact verification require RDKit; learning rules also needs the numerical analysis dependencies. Calculations use a CPU. Generation uses the current AI assistant and needs no separate LLM API configuration. If the computation environment fails, generated proposals remain unverified. That environment failure is not a SMILES parsing result or evidence of zero rule matches.

## Save and continue

STCA works through the LLM conversation. You can directly request learning, screening or generation; if the task is unclear, the assistant explains these options and asks what you want to do.

- **Learn from data:** receive separate STCA and WRAcc rules and screening results, each tier's physical cutoff, comparison, unit and recommendation. Defaults are Top or Bottom 10%, 20% and 30%; custom percentages are supported. The assistant saves reusable rule files and reports their actual location.
- **Screen with rules:** ask for relevant bundled rules, or refer to the files saved earlier. The assistant lists sources and targets when a choice is needed.
- **Generate with rules:** select a rule in conversation, then ask to preview and confirm the prompt or to generate directly. The current LLM produces the proposals; calculation tools verify their structures and rule conditions.

Continue the conversation with **“Screen these candidates with the rules just saved”** or **“Generate with those rules.”** To switch sessions or platforms, download the rule bundle and upload it in the new session. See the [natural-language examples](USAGE.md).

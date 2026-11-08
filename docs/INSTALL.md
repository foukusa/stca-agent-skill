# Install and use STCA

**Version 0.1.0** · [简体中文](INSTALL.zh-CN.md) · [Home](../README.md)

## Contents

- [Choose a package](#choose-a-package)
- [Codex](#codex)
- [DeepSeek Harness](#deepseek-harness)
- [WorkBuddy](#workbuddy)
- [ChatGPT desktop](#chatgpt-desktop)
- [Calculation environment](#calculation-environment)
- [WorkBuddy file permissions](#workbuddy-file-permissions)
- [Save and continue](#save-and-continue)
- [Natural-language examples](USAGE.md)

## Choose a package

Choose your platform below. Every package link opens a file page in this GitHub repository’s [downloads folder](https://github.com/foukusa/stca-agent-skill/tree/main/downloads). On that page, click **Download raw file** (the download button) to save the ZIP or TGZ locally. Alternatively, use **Code → Download ZIP** on the [repository home](https://github.com/foukusa/stca-agent-skill) and find the release files under `downloads`. WorkBuddy’s marketplace link will be added after publication.

| Platform | Download |
|---|---|
| Codex | [stca-codex-0.1.0.zip](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/stca-codex-0.1.0.zip) |
| DeepSeek Harness: local skill | [stca-deepseek-harness-0.1.0.zip](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/stca-deepseek-harness-0.1.0.zip) |
| DeepSeek Harness: GUI plugin | [dsh-plugin-stca-0.1.0.zip](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/dsh-plugin-stca-0.1.0.zip) |
| DeepSeek Harness: CLI plugin | [dsh-plugin-stca-0.1.0.tgz](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/dsh-plugin-stca-0.1.0.tgz) |
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

For the graphical interface, use the **extracted local directory from the plugin ZIP**. GitHub source and TGZ installation are also available through the CLI; the manual skill ZIP has its own route. Plugin-center link: — (to be added after listing).

<!-- DSH_PLUGIN_CENTER_URL: add the actual listing URL after publication. -->

### Install the plugin through the graphical interface

1. Open [dsh-plugin-stca-0.1.0.zip](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/dsh-plugin-stca-0.1.0.zip), click **Download raw file**, and extract it.
2. Open **Plugins → Add plugin** and enter the full local path to the extracted plugin folder, for example:

```text
/Users/your-name/Downloads/dsh-plugin-stca-0.1.0
```

3. Check that the folder directly contains `package.json`, `dsh` and `skills`. This is the plugin root to give Add plugin.
4. Install it, enable STCA in the profile you use, and enter `/stca`.

Use your actual username and extraction location. In Finder, hold Option while right-clicking the folder and copy its pathname, then paste that path into the input field.

### GitHub source and the CLI

Source repository: [foukusa/stca-agent-skill](https://github.com/foukusa/stca-agent-skill). You can also use **Code → Download ZIP**, extract the source, and give Add plugin the repository root that directly contains `package.json`. A GitHub `/tree/main` page is a browsing address, not a local plugin-directory path.

For direct GitHub installation, name the package explicitly in the DSH CLI:

```bash
dsh plugin --profile web add 'dsh-plugin-stca@github:foukusa/stca-agent-skill'
```

This argument is for the CLI. Use the local plugin-directory route in the graphical interface; do not paste `dsh-plugin-stca@github:…` into its package-name input field.

### Install by npm package name

After npm publication, enter the following in **Plugins → Add plugin**:

```text
dsh-plugin-stca
```

The CLI equivalent is:

```bash
dsh plugin --profile web add dsh-plugin-stca
```

Replace `web` with your actual profile. The plugin-center link remains blank until a public listing exists.

### Downloaded skill ZIP

1. Download [stca-deepseek-harness-0.1.0.zip](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/stca-deepseek-harness-0.1.0.zip) and extract it.
2. Copy the complete `stca` folder into the DSH user skill root. With the default DSH home, the result is `~/.dsh/skills/stca/SKILL.md`. For a project-only skill, use `.dsh/skills/stca` under the project root. A custom DSH home or skill-root setting takes precedence.
3. Keep `scripts`, `references` and `assets` beside `SKILL.md`; enable the filesystem skill provider in the selected profile.
4. Enter `/stca` or say “Start STCA”.

This ZIP contains a skill folder with `SKILL.md` for manual placement. The GUI plugin ZIP contains the plugin-root `package.json`; follow the corresponding steps for each format.

### Download a TGZ and install through the CLI

Download [dsh-plugin-stca-0.1.0.tgz](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/dsh-plugin-stca-0.1.0.tgz). It is already a plugin package, with no extraction or repacking needed. Name the package explicitly and use the file’s actual absolute path:

```bash
dsh plugin --profile web add 'dsh-plugin-stca@file:/Users/your-name/Downloads/dsh-plugin-stca-0.1.0.tgz'
```

This named file specification is for the **CLI**. In the graphical interface, use the extracted directory as described above instead of pasting the full CLI argument into its input field.

### “Unable to determine the installed package from dependency changes”

This error means the DSH plugin manager could not identify one target package from the dependency changes, before STCA was loaded. Check the plugin list first: enable an existing STCA entry instead of adding it again. To replace an installed copy, remove that plugin through its management interface before installing the replacement, keeping your data, results and saved rule bundles.

If installation has not succeeded, use the **plugin ZIP → extract → plugin-root directory** route above. If it still fails, preserve the complete installation log, DSH version, installation source and actual error. Repeating the same input or modifying Python/STCA code does not address this plugin-installation stage.

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

The unmodified author implementation is included and checked locally against the package’s trusted file inventory. Ordinary calculations do not clone a Git repository or require a Git executable. Missing Python dependencies may still need a permitted download from PyPI.

You normally do not fill in any Python path. To use a particular environment, say “Use the Python interpreter at this path” and provide it. That explicit choice is checked and retained; a failure is explained instead of silently selecting another interpreter. If automatic discovery and preparation cannot complete, the assistant reports the specific missing requirement.

Reading existing rules and prompts does not require RDKit. Structural screening and exact verification require RDKit; learning rules also needs the numerical analysis dependencies. Calculations use a CPU. Generation uses the current AI assistant and needs no separate LLM API configuration. If the computation environment fails, generated proposals remain unverified. That environment failure is not a SMILES parsing result or evidence of zero rule matches.

### WorkBuddy file permissions

Use a separate folder for this task and make it the current workspace. STCA places its default WorkBuddy runtime cache, newly saved rules and output files in the task workspace, and reports their actual locations. It checks bundled source locally; a runtime task should not repeatedly run `git clone`, create a fake `.git` directory, or modify source-verification code.

The assistant reports the first failed operation, its path and the actual error. If WorkBuddy shows a permission prompt, review that specific action and path. Use WorkBuddy’s **View blocking rule** or security audit record to identify an explicit denial; ordinary Git lock files alone do not establish which platform rule was responsible. Do not disable security globally to make a task continue.

A calculation can finish while a later save is blocked. In that case, STCA keeps the models and screening files already produced and reports the rule-library save status separately. It does not report the entire task as successfully saved. New storage entries are marked ready only after all required files and their hashes validate; incomplete entries are not reusable rules. Continue from the reported results after the specific permission issue is resolved. See [WorkBuddy permissions and sandbox](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Permission-Modes) for its permission and audit controls.

## Save and continue

STCA works through the LLM conversation. You can directly request learning, screening or generation; if the task is unclear, the assistant explains these options and asks what you want to do.

- **Learn from data:** receive separate STCA and WRAcc rules and screening results, each tier's physical cutoff, comparison, unit and recommendation. Defaults are Top or Bottom 10%, 20% and 30%; custom percentages are supported. The assistant saves reusable rule files and reports their actual location.
- **Screen with rules:** ask for relevant bundled rules, or refer to the files saved earlier. The assistant lists sources and targets when a choice is needed.
- **Generate with rules:** select a rule in conversation, then ask to preview and confirm the prompt or to generate directly. The current LLM produces the proposals; calculation tools verify their structures and rule conditions.

Continue the conversation with **“Screen these candidates with the rules just saved”** or **“Generate with those rules.”** To switch sessions or platforms, download the rule bundle and upload it in the new session. See the [natural-language examples](USAGE.md).

# Install and use STCA

**Version 0.1.0** · [简体中文](INSTALL.zh-CN.md) · [Home](../README.md)

## Contents

- [Choose a package](#choose-a-package)
- [Update an existing installation](#update-an-existing-installation)
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
| WorkBuddy | [stca-workbuddy-0.1.3.zip](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/stca-workbuddy-0.1.3.zip) |
| ChatGPT desktop | [stca-openai-skill-0.1.0.zip](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/stca-openai-skill-0.1.0.zip) |

All STCA tasks accept natural language. The assistant handles calculation-environment discovery; you do not need to enter a Python path during installation.

## Update an existing installation

The STCA core version remains **0.1.0**. Replace or reimport the updated files to receive these fixes; the version label alone does not confirm that an installed copy is current. First save your exported rule bundles and task results.

- **Codex folder installation:** replace the installed `stca` folder with the complete updated folder, keeping `SKILL.md`, `scripts`, `references` and `assets` together. Keep saved rules and results in their task directories outside the installation folder.
- **DeepSeek Harness:** check STCA’s installation source in plugin management and use the available update or replacement operation. If an old copy remains, remove only the STCA plugin, then add it again with `github:foukusa/stca-agent-skill`. Keep the DSH profile, configuration, data and saved rules.
- **WorkBuddy:** import `stca-workbuddy-0.1.3.zip` and enable the updated STCA entry.
- **ChatGPT:** where local skill import is supported, reimport the updated OpenAI skill ZIP through the existing skill-management entry.

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

The recommended route is **Plugins → Add plugin**, using the GitHub installation address below. **GitHub installation does not require npm publication.** DSH reads `package.json`, the plugin entry and complete skill from the repository root. Plugin-center link: — (to be added after listing).

<!-- DSH_PLUGIN_CENTER_URL: add the actual listing URL after publication. -->

### Install from GitHub

1. In DSH, open **Plugins → Add plugin**.
2. Enter this full repository URL and click Install:

```text
github:foukusa/stca-agent-skill
```

3. Enable STCA in your current profile, then enter `/stca` or say “Start STCA”.

Use the repository URL, not a `/tree/main` browsing page or a terminal command. This GitHub route remains available before npm publication. Only entering the bare npm name `dsh-plugin-stca` requires a published npm package.

### Optional: extract the plugin ZIP and install its directory

1. Open [dsh-plugin-stca-0.1.0.zip](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/dsh-plugin-stca-0.1.0.zip), click **Download raw file**, and extract it.
2. In **Plugins → Add plugin**, enter the complete local path to the extracted plugin folder, for example:

```text
/Users/your-name/Downloads/dsh-plugin-stca-0.1.0
```

3. The folder must directly contain `package.json`, `dsh` and `skills`. Install, enable STCA and enter `/stca`.

Alternatively, use **Code → Download ZIP** in the [source repository](https://github.com/foukusa/stca-agent-skill), extract it, and give Add plugin the repository root containing `package.json`. Use your actual username and extraction location.

### Optional: GitHub installation through the CLI

In a terminal, the DSH CLI can explicitly name the package and its GitHub source:

```bash
dsh plugin --profile web add 'dsh-plugin-stca@github:foukusa/stca-agent-skill'
```

**This command still installs from GitHub and does not require npm publication.** `plugin` is a DSH command name; `@github:...` specifies the GitHub source. Replace `web` with your actual profile. Run this in a terminal, not the graphical input field; use the repository URL in the interface.

### npm package name: after publication

Only after the npm package is published, enter this in **Plugins → Add plugin**:

```text
dsh-plugin-stca
```

The CLI equivalent is `dsh plugin --profile web add dsh-plugin-stca`. Add the plugin-center link once it exists; an unpublished npm package does not prevent GitHub installation.

### Downloaded standalone skill ZIP

1. Download [stca-deepseek-harness-0.1.0.zip](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/stca-deepseek-harness-0.1.0.zip) and extract it.
2. Copy the complete `stca` folder into the DSH user skill root. With the default DSH home, the result is `~/.dsh/skills/stca/SKILL.md`. For a project-only skill, use `.dsh/skills/stca` under the project root. Custom path settings take precedence.
3. Keep `scripts`, `references` and `assets` beside `SKILL.md`, enable the filesystem skill provider in your profile, and enter `/stca`.

This ZIP contains a skill folder for manual placement. The plugin ZIP above contains the `package.json` used by Add plugin; follow the corresponding route for each format.

### Optional: install a downloaded TGZ through the CLI

Download [dsh-plugin-stca-0.1.0.tgz](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/dsh-plugin-stca-0.1.0.tgz). It is a ready-made plugin package: no extraction, repacking or npm publication is needed. Use the actual absolute file path in a terminal:

```bash
dsh plugin --profile web add 'dsh-plugin-stca@file:/Users/your-name/Downloads/dsh-plugin-stca-0.1.0.tgz'
```

This named file argument is for the CLI. The graphical interface uses a repository URL or an extracted plugin directory.

### “Unable to determine the installed package from dependency changes”

This means the DSH plugin manager could not identify one target package from the dependency changes, before loading STCA. It does not mean npm publication is required, and it is unrelated to Python, RDKit or STCA calculations.

Check the plugin list first: enable an existing STCA entry instead of repeatedly adding it. To replace an old copy, manage only the old STCA plugin while preserving your data, results and rule bundles.

A successful pnpm log, including `Packages: +1` and `Done`, confirms package installation but does not by itself identify a unique plugin for DSH. Use `github:foukusa/stca-agent-skill` in Add plugin as shown above. If an earlier HTTPS installation produced this error, retry with that address. If STCA is already listed, enable it. If installation still fails, use the local plugin-directory fallback and retain the complete log and DSH version. Keep your data, results and saved rules.

See the [official plugin installation guide](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/user/develop/basic/publish.md) and [filesystem skill guide](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/skill-filesystem/README.md).

## WorkBuddy

1. Open [WorkBuddy](https://www.workbuddy.cn/) and its skill management page.
2. Choose the action for adding and uploading a local skill package.
3. Open [stca-workbuddy-0.1.3.zip](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/stca-workbuddy-0.1.3.zip) in the repository and click **Download raw file**. Select that downloaded ZIP in WorkBuddy, complete import and enable **STCA Polymer Rules and Design**. Keep the ZIP intact for upload.
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

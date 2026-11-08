# Install and use STCA on Mac

**Version 0.1.0** · [简体中文](INSTALL.zh-CN.md) · [Home](../README.md)

## Contents

- [Choose a package](#choose-a-package)
- [ChatGPT](#chatgpt)
- [Codex](#codex)
- [DeepSeek Harness](#deepseek-harness)
- [WorkBuddy](#workbuddy)
- [Save and continue](#save-and-continue)
- [Natural-language examples](USAGE.md)

## Choose a package

| Platform | Download |
|---|---|
| ChatGPT or Codex | [stca-openai-skill-0.1.0.zip](../downloads/stca-openai-skill-0.1.0.zip?raw=true) |
| DeepSeek Harness | [stca-deepseek-harness-0.1.0.zip](../downloads/stca-deepseek-harness-0.1.0.zip?raw=true) |
| WorkBuddy | [stca-workbuddy-0.1.0.zip](../downloads/stca-workbuddy-0.1.0.zip?raw=true) |

The same standalone OpenAI skill ZIP works for ChatGPT and Codex; use the installation method supported by each client. Every workflow accepts natural language. Calculations use a CPU; the AI assistant reuses a compatible Python 3.10+ environment and prepares required dependencies without asking you to run commands.

## ChatGPT

1. Open [ChatGPT](https://chatgpt.com/) and go to **Plugins → Skills**.
2. Choose **Create → Upload from your computer**.
3. In the Mac file dialog, select `stca-openai-skill-0.1.0.zip` and click Open.
4. Complete the page instructions, select STCA and say “Start STCA”.

Creation and uploading depend on account and workspace access. See [official ChatGPT help](https://help.openai.com/en/articles/20001066-skills-in-chatgpt/). If STCA is already installed from the public directory, select it directly.

## Codex

Ask Codex to install it:

```text
Use $skill-installer to install https://github.com/foukusa/stca-agent-skill/tree/main/skills/stca
```

Then say “Use $stca”. For local installation:

1. Double-click the same `stca-openai-skill-0.1.0.zip` in Finder.
2. Use **Go → Go to Folder** to open an existing `~/.agents/skills` directory.
3. Copy the complete `stca` folder, keeping `SKILL.md` and all supporting directories together.
4. Select STCA or say “Use $stca”. Use the automatic installation request if a local skill directory is not available.

See the [official OpenAI skill guide](https://learn.chatgpt.com/docs/build-skills).

## DeepSeek Harness

1. Use a configured [DeepSeek Harness](https://www.deepseek.com/harness/).
2. Double-click the DeepSeek ZIP in Finder to obtain the complete `stca` folder.
3. Press **Command+Shift+G** in Finder, enter the configured skill root (the default is `~/.dsh/skills`), and press Return.
4. If Finder cannot find that location, ask the AI assistant in Harness to create the default user skill directory or identify the configured root, then open that location in Finder.
5. Copy the complete `stca` folder there, producing `stca/SKILL.md` with all supporting directories together.
6. Enter `/stca` in Harness.

Keep `SKILL.md`, `scripts`, `references` and `assets` together. See the [official filesystem guide](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/skill-filesystem/README.zh.md). Complete generation prompts can also be copied into an ordinary DeepSeek chat.

## WorkBuddy

1. Open [WorkBuddy](https://www.workbuddy.cn/) and its skill management page.
2. Choose the action for adding and uploading a local skill package.
3. Select the WorkBuddy ZIP in the Mac file dialog, complete import and enable STCA.
4. Say “Start STCA”.

See [official WorkBuddy instructions](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market).

## Save and continue

The menu order is **1 Upload data and learn, 2 Screen with existing rules, 3 Generate with existing rules**.

- Task 1 compares STCA and WRAcc within your data range by default. Each tier returns primary/alternative rules, physical cutoffs and both methods’ screening results for the original table, plus separate results for any independent candidates. It preserves original SMILES, failed conditions and uncomputable records, saves the rules and returns to the menu.
- Task 2 screens uploaded candidates with a selected bundled or personal rule.
- Task 3 first shows the rule catalog, methods and primary/alternative choices. After selecting a rule, choose **Preview and confirm** to review and adjust the complete prompt before saying “Confirm and generate,” or **Generate directly** to have the current LLM generate and verify immediately. Both modes preserve every proposal and failed condition, then return to the menu. No additional LLM API setup is needed.

Bundled open-data tasks provide Top 10%, 20% and 30%; your own data can support custom tiers such as 15% or 25%.

Copy the short requests from the [natural-language examples](USAGE.md).

“Main menu” or “Back” preserves saved rules. To change sessions or platforms, download the rule bundle and upload it in the new session, then ask the AI assistant to load it.

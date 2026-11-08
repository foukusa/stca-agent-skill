# Install and use STCA

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

Choose your AI platform and follow the installation method supported by its client.

| Platform | Download |
|---|---|
| ChatGPT or Codex | [stca-openai-skill-0.1.0.zip](../downloads/stca-openai-skill-0.1.0.zip?raw=true) |
| DeepSeek Harness | [stca-deepseek-harness-0.1.0.zip](../downloads/stca-deepseek-harness-0.1.0.zip?raw=true) |
| WorkBuddy | [stca-workbuddy-0.1.0.zip](../downloads/stca-workbuddy-0.1.0.zip?raw=true) |

ChatGPT and Codex use the same standalone skill package. All workflows accept natural language. The AI assistant prepares the CPU calculation environment; you do not need to run setup commands.

## ChatGPT

1. Open [ChatGPT](https://chatgpt.com/) and go to **Plugins → Skills**.
2. Choose **Create → Upload from your computer**.
3. Select `stca-openai-skill-0.1.0.zip` and complete the page instructions.
4. Select STCA and say “Start STCA”.

Creation and uploading depend on account and workspace access. See [official ChatGPT help](https://help.openai.com/en/articles/20001066-skills-in-chatgpt/). If STCA is already installed from the public directory, select it directly.

## Codex

Ask Codex to install it:

```text
Use $skill-installer to install https://github.com/foukusa/stca-agent-skill/tree/main/skills/stca
```

Then say “Use $stca”. If you install from local files:

1. Extract `stca-openai-skill-0.1.0.zip` with your file manager.
2. Copy the complete `stca` folder into the skill directory configured in Codex. If you do not know its location, ask Codex to identify it or use the installation request above.
3. Keep `SKILL.md`, `scripts`, `references` and `assets` together.
4. Select STCA or say “Use $stca”.

See the [official OpenAI skill guide](https://learn.chatgpt.com/docs/build-skills).

## DeepSeek Harness

1. Open your configured [DeepSeek Harness](https://www.deepseek.com/harness/).
2. Extract the DeepSeek ZIP to obtain the complete `stca` folder.
3. Copy it into the configured skill root; the default user root is `~/.dsh/skills`. If the directory is unavailable or you use a custom configuration, ask the Harness assistant to identify or prepare the correct location.
4. Keep the folder structure intact, with `stca/SKILL.md` and its supporting directories.
5. Enter `/stca` in Harness.

See the [official filesystem guide](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/skill-filesystem/README.zh.md). Complete generation prompts can also be copied into an ordinary DeepSeek chat.

## WorkBuddy

1. Open [WorkBuddy](https://www.workbuddy.cn/) and its skill management page.
2. Choose the action for adding and uploading a local skill package.
3. Select `stca-workbuddy-0.1.0.zip`, complete import and enable STCA.
4. Say “Start STCA”.

See [official WorkBuddy instructions](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market).

## Save and continue

The menu order is **1 Upload data and learn, 2 Screen with existing rules, 3 Generate with existing rules**.

- Task 1 returns STCA and WRAcc rules separately, with each tier’s numeric physical cutoff, comparison, unit, screening results and recommendation. If percentages are omitted, it uses Top or Bottom 10%, 20% and 30%; you can specify other percentages, such as 15% or 25%. Results preserve the original table, SMILES, unmet rule conditions and uncomputable records. The rules are saved before returning to the menu.
- Task 2 screens uploaded candidates with bundled rules or My rules. The two methods’ results remain separate, and the recommended method is clearly identified.
- Task 3 first shows the rule catalog. After selecting a rule, choose **Preview and confirm** to review and adjust the complete prompt before saying “Confirm and generate,” or **Generate directly** to have the current LLM generate and verify immediately. Both modes preserve every proposal and unmet rule condition, then return to the menu. No additional LLM API setup is needed.

Copy a short request from the [natural-language examples](USAGE.md).

“Main menu” or “Back” preserves saved rules. To change sessions or platforms, download the rule bundle and upload it in the new session, then ask the AI assistant to load it.

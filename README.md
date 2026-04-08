[English](README.md) | [中文](README-zh.md)

# CommandChat

`commandchat` provides the `occ` CLI for chatting with OpenAI or Azure OpenAI models from your terminal.

## Features

- Interactive CLI chat with `occ chat`
- Profile-based configuration for multiple OpenAI / Azure OpenAI accounts
- Prompt template management with built-in and custom prompts
- Prompt selection per command or as a profile default
- Experimental image generation command

## Requirements

- Python 3.8+
- A terminal with `pip`
- An OpenAI-compatible API key or Azure OpenAI configuration

## Install

```bash
pip3 install commandchat
```

If you manage multiple Python versions locally:

```bash
python3 -m pip install commandchat
```

## Quick start

### 1. Configure your first profile

```bash
occ configure
```

This opens the interactive configuration flow and writes local settings under `~/.occ/`.

### 2. Start chatting

```bash
occ chat "Hello, introduce yourself briefly."
```

You can also start interactive multiline input:

```bash
occ chat
```

Inside interactive chat, you can use slash commands:

- `/` to open the shortcut command menu
- `/pmp`, `/p`, or `/prompt` to list prompts and switch the active prompt template
- `/m` or `/model` to list models and switch the active model
- `/q` to exit the chat session
- `/help` to show the help panel again

When you switch prompts with `/pmp` or models with `/m`, the CLI will ask whether you want to keep the current context or start a fresh chat session with a new session id.

Interactive chat also shows a bottom status bar with the current prompt, model, and session id.

### 3. Use prompt templates

```bash
occ prompt list
occ chat -pt translate "你好世界"
occ chat -pt improve "I wants to go to school yesterday"
```

### 4. Work with multiple profiles

```bash
occ configure profile -p work
occ configure list
occ chat -p work "Summarize today's priorities"
```

## Common commands

| Command | Description |
| --- | --- |
| `occ configure` | Open the interactive configuration menu |
| `occ configure profile -p <name>` | Create or update a profile |
| `occ configure list` | List configured profiles |
| `occ configure delete <name>` | Delete a profile |
| `occ chat "message"` | Send a one-off message |
| `occ chat` | Start an interactive chat session |
| `occ chat -p <profile> -m <model> "message"` | Use a specific profile/model |
| `occ chat -pt <prompt_key> "message"` | Chat with a predefined prompt |
| `occ chat` + `/` | Open the interactive shortcut menu |
| `occ chat` + `/pmp` / `/p` / `/prompt` | Switch prompt inside interactive chat |
| `occ chat` + `/m` / `/model` | Switch model inside interactive chat |
| `occ prompt list` | List prompt templates |
| `occ prompt show <key>` | Show prompt details |
| `occ prompt add <key> -n <name> -d <desc> -s <prompt>` | Add a custom prompt |
| `occ image -desc "..." -size m` | Generate images |

## Files created locally

- `~/.occ/config`: profile and model configuration
- `~/.occ/prompts.json`: custom prompt templates

## Packaging and PyPI

This project now uses `pyproject.toml` as the single source of truth for packaging metadata.

- `README.md` is configured as `project.readme`, so PyPI renders this file on the project page.
- `README-zh.md` is kept for the GitHub repository and Chinese-language documentation.
- To update the PyPI project page content, update `README.md`, bump the version in `pyproject.toml`, and publish a new release.

### Automatic publishing with GitHub Actions

The repository includes `.github/workflows/publish-to-pypi.yml`.

On pushes to `master` or manual runs, it will:

1. Check whether the version in `pyproject.toml` changed
2. Build the sdist and wheel from `pyproject.toml`
3. Run `twine check dist/*`
4. Publish to PyPI via Trusted Publishing (OIDC)

Because the package metadata points to `README.md`, each new PyPI release also refreshes the PyPI homepage description.

## Manual build

```bash
python3 -m pip install build twine
python3 -m build
python3 -m twine check dist/*
```

## Uninstall

```bash
pip3 uninstall commandchat
```

## Feedback

- `xxx.tao.c@gmail.com`
- `xoto@outlook.be`

## License

MIT


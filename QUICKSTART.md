# Quick Start Guide

## 🚀 Quick Start

### Using Prompts

```bash
# View all available prompts
occ prompt list

# Use built-in translate prompt
occ chat -pt translate "你好世界"

# Use built-in improve prompt
occ chat -pt improve "I wants to go to school yesterday"

# Interactive prompt management
occ prompt
```

### Managing Prompts

```bash
# Add a custom prompt (command-line)
occ prompt add my-prompt -n "My Prompt" -d "Description" -s "System prompt text"

# Add a custom prompt (interactive)
occ prompt
# Then select: Add new prompt

# Modify a prompt (interactive - easiest)
occ prompt
# Then select: Modify prompt -> Choose prompt -> Select fields to modify

# Remove a prompt
occ prompt remove my-prompt
```

### Profile Configuration

```bash
# Interactive configuration (recommended)
occ configure

# View all profiles
occ configure list

# Configure a specific profile
occ configure profile -p myprofile

# Delete a profile
occ configure delete myprofile
```

### Interactive Chat Shortcuts

```bash
# Start interactive chat
occ chat

# Then use these in the chat input box:
/      # open the shortcut command menu
/pmp   # list prompts and switch the active prompt
/p     # short alias for prompt switch
/prompt # full alias for prompt switch
/m     # list models and switch the active model
/model # full alias for model switch
/help  # show help
/q     # quit chat
```

When switching prompts with `/pmp` or models with `/m`, you can either keep the current context or start a new chat session with a fresh session id.

### Setting Profile Default Prompt

```bash
# During profile configuration, you'll be asked:
occ configure profile -p myprofile

# You'll see:
# ? Set a default prompt template for this profile? (Y/n)
# Select Yes, then choose from available prompts

# Now all chats with this profile use the default prompt automatically:
occ chat -p myprofile "your message"

# Override with -pt:
occ chat -p myprofile -pt improve "your message"
```

## 📋 Command Reference

### Prompts Commands

| Command | Description |
|---------|-------------|
| `occ prompt` | Interactive prompt management menu |
| `occ prompt list` | List all prompts |
| `occ prompt show <key>` | Show prompt details |
| `occ prompt add <key> -n <name> -d <desc> -s <prompt>` | Add custom prompt |
| `occ prompt modify [key]` | Modify custom prompt (interactive if no key) |
| `occ prompt remove [key]` | Remove custom prompt (interactive if no key) |

### Configure Commands

| Command | Description |
|---------|-------------|
| `occ configure` | Interactive configuration menu |
| `occ configure list` | List all profiles |
| `occ configure profile [-p name]` | Configure a profile |
| `occ configure delete [name]` | Delete a profile |

### Chat Commands

| Command | Description |
|---------|-------------|
| `occ chat "message"` | Chat (uses profile default prompt if set) |
| `occ chat -pt <key> "message"` | Chat with specific prompt |
| `occ chat -p <profile> "message"` | Chat with specific profile |
| `occ chat -p <profile> -pt <key> "message"` | Chat with profile and prompt |
| `occ chat` + `/` | Open the interactive shortcut menu |
| `occ chat` + `/pmp` / `/p` / `/prompt` | Switch prompt inside interactive chat |
| `occ chat` + `/m` / `/model` | Switch model inside interactive chat |

## 🎯 Common Workflows

### Workflow 1: Quick Translation
```bash
# One-time use
occ chat -pt translate "你好，今天天气真好"

# Set as default for a profile
occ configure profile -p trans
# Select translate as default prompt
# Then use:
occ chat -p trans "任何中文文本"
```

### Workflow 2: English Writing Improvement
```bash
occ chat -pt improve "I am goes to the store yesterday and buy some foods"
```

### Workflow 3: Custom Code Review Prompt
```bash
# Create the prompt
occ prompt add code-review \
  -n "Code Reviewer" \
  -d "Review code and suggest improvements" \
  -s "You are an expert code reviewer. Review the code for: 1) Bugs, 2) Performance issues, 3) Best practices, 4) Security concerns. Provide specific suggestions."

# Use it
occ chat -pt code-review "def foo(x): return x + 1"

# Or set as default for a dev profile
occ configure profile -p dev
# Select code-review as default
```

### Workflow 4: Interactive Management
```bash
# For users who prefer menus over commands
occ prompt
# Navigate with arrow keys, select with Enter

occ configure
# Navigate and configure interactively
```

## 💡 Tips

1. **Interactive mode is easier**: Use `occ prompt` or `occ configure` without arguments
2. **Command-line is faster**: Use full commands when you know what you want
3. **Profile defaults save time**: Set frequently-used prompts as profile defaults
4. **Override when needed**: Use `-pt` to temporarily override profile defaults
5. **Built-in prompts are protected**: You can't accidentally modify or delete them
6. **Custom prompts are flexible**: Create as many as you need for different tasks

## ❓ FAQ

**Q: How do I see what prompts are available?**
```bash
occ prompt list
```

**Q: How do I see detailed info about a prompt?**
```bash
occ prompt show translate
```

**Q: Can I modify the built-in prompts?**
A: No, but you can create your own custom prompts based on them.

**Q: How do I set a default prompt for my profile?**
```bash
occ configure profile -p myprofile
# Then answer "Yes" when asked about default prompt
```

**Q: How do I override my profile's default prompt?**
```bash
occ chat -p myprofile -pt different-prompt "message"
```

**Q: Where are my custom prompts stored?**
A: In `~/.occ/prompts.json`

**Q: Can I delete the default profile?**
A: No, the default profile cannot be deleted.

## 🔧 Advanced Usage

### Scripting with Prompts
```bash
#!/bin/bash
# Translate multiple files
for file in *.txt; do
  content=$(cat "$file")
  occ chat -pt translate "$content" > "${file%.txt}_en.txt"
done
```

### Chain Multiple Prompts
```bash
# First translate
translation=$(occ chat -pt translate "你好世界" | tail -1)

# Then improve the translation
occ chat -pt improve "$translation"
```

### Profile-Specific Workflows
```bash
# Create specialized profiles
occ configure profile -p translate-zh
# Set default_prompt to 'translate'

occ configure profile -p writing
# Set default_prompt to 'improve'

# Use them
occ chat -p translate-zh "中文文本"
occ chat -p writing "English text needing improvement"
```

---


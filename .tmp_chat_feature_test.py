import py_compile
import occ.command.commands.chat as chat_mod

py_compile.compile('occ/command/commands/chat.py', doraise=True)

handled, prompt_key, system_message, model = chat_mod._handle_interactive_command(
    '/not-a-command', None, 'default', 'openai', 'translate', 'o1-mini'
)
assert handled is False
assert prompt_key == 'translate'
assert system_message is None
assert model == 'o1-mini'

orig_prompt_selector = chat_mod._select_prompt_interactively
orig_model_selector = chat_mod._select_model_interactively
orig_help = chat_mod._show_interactive_help
help_calls = []

chat_mod._show_interactive_help = lambda p, m: help_calls.append((p, m))
chat_mod._select_prompt_interactively = lambda style, current: ('improve', 'SYSTEM', True)
chat_mod._select_model_interactively = lambda style, profile, api_type, current: ('gpt-4o', True)

handled, prompt_key, system_message, model = chat_mod._handle_interactive_command(
    '/pmp', None, 'default', 'openai', 'translate', 'o1-mini'
)
assert (handled, prompt_key, system_message, model) == (True, 'improve', 'SYSTEM', 'o1-mini')

handled, prompt_key, system_message, model = chat_mod._handle_interactive_command(
    '/m', None, 'default', 'openai', 'improve', 'o1-mini'
)
assert (handled, prompt_key, system_message, model) == (True, 'improve', None, 'gpt-4o')

handled, prompt_key, system_message, model = chat_mod._handle_interactive_command(
    '/help', None, 'default', 'openai', 'improve', 'gpt-4o'
)
assert handled is True
assert help_calls == [('improve', 'gpt-4o')]

chat_mod._select_prompt_interactively = orig_prompt_selector
chat_mod._select_model_interactively = orig_model_selector
chat_mod._show_interactive_help = orig_help

print('chat-command-dispatch-tests=passed')


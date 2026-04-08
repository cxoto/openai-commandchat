"""Chat command"""

import html
import sys
import time

import click
from prompt_toolkit import PromptSession, print_formatted_text, HTML
from prompt_toolkit.cursor_shapes import ModalCursorShapeConfig
from prompt_toolkit.styles import style_from_pygments_cls
from pygments.styles import get_style_by_name

import occ.utils.logger as logger
from occ.CommandChat import CommandChat, DEFAULT_CHAT_LOG_ID


OPENAI_MODEL_CHOICES = [
    'o1-mini',
    'o1',
    'o3-mini',
    'gpt-4.1',
    'gpt-4.1-mini',
    'gpt-4o',
    'gpt-4o-mini',
]


def _build_questionary_style():
    from questionary import Style

    return Style([
        ('qmark', 'fg:#673ab7 bold'),
        ('question', 'bold'),
        ('answer', 'fg:#f44336 bold'),
        ('pointer', 'fg:#673ab7 bold'),
        ('highlighted', 'fg:#673ab7 bold'),
    ])


def _resolve_prompt_state(active_profile, prompt):
    from occ.commons import config as cfg
    from occ.commons.prompts import get_prompt_system_message, list_prompts

    system_message = None
    prompt_key = None

    if prompt:
        system_message = get_prompt_system_message(prompt)
        if not system_message:
            logger.log_r(f"Prompt '{prompt}' not found. Available prompts:")
            for key, value in list_prompts().items():
                logger.log_g(f"  - {key}: {value['description']}")
            return None, None, False
        prompt_key = prompt
        logger.log_g(f"Using prompt template: {prompt_key} (from command line)")
        return prompt_key, system_message, True

    profile_default_prompt = cfg.get_profile_default_prompt(active_profile)
    if profile_default_prompt:
        system_message = get_prompt_system_message(profile_default_prompt)
        if system_message:
            prompt_key = profile_default_prompt
            logger.log_g(f"Using default prompt: {prompt_key} (from profile '{active_profile}')")

    return prompt_key, system_message, True


def _get_available_models(api_server_type, active_profile, current_model):
    from occ.commons import config as cfg

    if api_server_type == 'azure-openai':
        return cfg.get_profile_models(active_profile)

    models = []
    if current_model:
        models.append(current_model)
    for model_name in OPENAI_MODEL_CHOICES:
        if model_name not in models:
            models.append(model_name)
    return models


def _resolve_initial_model(api_server_type, active_profile, model, message, file, custom_style):
    available_models = _get_available_models(api_server_type, active_profile, model)

    if api_server_type != 'azure-openai':
        return model or 'o1-mini', True

    if not available_models:
        logger.log_r(f"No models configured for profile '{active_profile}'. Please run 'occ configure' first.")
        return None, False

    if not model or model == 'o1-mini':
        if len(available_models) > 1:
            if not message and not file and sys.stdin.isatty():
                import questionary

                model = questionary.select(
                    "Select a model:",
                    choices=available_models,
                    style=custom_style
                ).ask()

                if model is None:
                    logger.log_r("Model selection cancelled.")
                    return None, False
            else:
                model = available_models[0]
                logger.log_g(f"Using model: {model}")
        else:
            model = available_models[0]
    elif model not in available_models:
        logger.log_r(f"Model '{model}' not found in profile '{active_profile}'. Available models: {', '.join(available_models)}")
        return None, False

    return model, True


def _show_interactive_help(current_prompt_key, current_model, current_chat_id):
    prompt_label = current_prompt_key or '[none]'
    model_label = current_model or '[unknown]'
    chat_label = current_chat_id or DEFAULT_CHAT_LOG_ID
    print_formatted_text(HTML(
        "<b>Help Info: \n</b>"
        "<ansigreen>Type your message and press ESC+Enter or OPT+Enter to send.\n"
        "Use /exit or /quit or /q to leave the chat.\n"
        "Use /help to show this message again.\n"
        "Use /pmp, /p, or /prompt to list prompts and switch the active prompt for the current chat session.\n"
        "Use /m or /model to list models and switch the active model for the current chat session.\n"
        "Type / to open the shortcut command menu.\n"
        f"Current prompt: {prompt_label}\n"
        f"Current model: {model_label}\n"
        f"Current session: {chat_label}</ansigreen>\n"
    ))


def _build_bottom_toolbar(current_prompt_key, current_model, current_chat_id):
    prompt_label = html.escape(current_prompt_key or 'none')
    model_label = html.escape(current_model or 'unknown')
    chat_label = html.escape(current_chat_id or DEFAULT_CHAT_LOG_ID)
    return HTML(
        f"<b><style bg='ansiblue' fg='ansiwhite'> prompt: {prompt_label} </style></b> "
        f"<b><style bg='ansimagenta' fg='ansiwhite'> model: {model_label} </style></b> "
        f"<b><style bg='ansigreen' fg='ansiwhite'> session: {chat_label} </style></b> "
        "<style fg='ansibrightblack'> shortcuts: /  /p  /m  /q </style>"
    )


def _build_new_chat_log_id(current_chat_id):
    timestamp = time.strftime('%Y%m%d-%H%M%S', time.localtime())
    if not current_chat_id or current_chat_id == DEFAULT_CHAT_LOG_ID:
        return f"chat-{timestamp}"
    return f"{current_chat_id}-{timestamp}"


def _pick_shortcut_command(custom_style):
    import questionary

    selected = questionary.select(
        "Shortcut commands:",
        choices=[
            questionary.Choice(title='/pmp (/p, /prompt) - switch prompt template', value='/pmp'),
            questionary.Choice(title='/m (/model) - switch model', value='/m'),
            questionary.Choice(title='/help - show help', value='/help'),
            questionary.Choice(title='/q - quit chat', value='/q'),
        ],
        style=custom_style,
    ).ask()

    if selected is None:
        logger.log_g('Shortcut command cancelled.')
    return selected


def _ask_session_switch_behavior(custom_style, target_label, current_chat_id, action_name):
    import questionary

    selected_action = questionary.select(
        f"Apply {action_name} '{target_label}' to this chat session:",
        choices=[
            questionary.Choice(title='Start a new chat context (recommended)', value='reset'),
            questionary.Choice(title='Keep the current chat context', value='keep'),
            questionary.Choice(title='Cancel', value='cancel'),
        ],
        default='reset',
        style=custom_style,
    ).ask()

    if selected_action is None or selected_action == 'cancel':
        logger.log_g('Prompt switch cancelled.')
        return None

    if selected_action == 'reset':
        next_chat_id = _build_new_chat_log_id(current_chat_id)
        logger.log_g(f"Started a new chat context: {next_chat_id}")
        return next_chat_id

    return current_chat_id


def _select_prompt_interactively(custom_style, current_prompt_key, current_chat_id):
    import questionary
    from occ.commons.prompts import list_prompts

    prompts_dict = list_prompts()
    if not prompts_dict:
        logger.log_r("No prompt templates available.")
        return current_prompt_key, None, current_chat_id, False

    choices = []
    for key, value in prompts_dict.items():
        choices.append(questionary.Choice(
            title=f"{key} - {value['name']}: {value['description']}",
            value=key,
        ))
    choices.append(questionary.Choice(title='[None] - disable current prompt', value='[None]'))

    selected_prompt = questionary.select(
        "Select a prompt for the current chat session:",
        choices=choices,
        default=current_prompt_key if current_prompt_key in prompts_dict else None,
        style=custom_style
    ).ask()

    if selected_prompt is None:
        logger.log_g("Prompt switch cancelled.")
        return current_prompt_key, None, current_chat_id, False

    if selected_prompt == '[None]' and current_prompt_key is None:
        logger.log_g("Prompt is already disabled for the current chat session.")
        return current_prompt_key, None, current_chat_id, False

    if selected_prompt == current_prompt_key:
        logger.log_g(f"Prompt '{selected_prompt}' is already active.")
        return current_prompt_key, None, current_chat_id, False

    if selected_prompt == '[None]':
        next_chat_id = _ask_session_switch_behavior(custom_style, '[none]', current_chat_id, 'prompt')
        if next_chat_id is None:
            return current_prompt_key, None, current_chat_id, False
        logger.log_g("Prompt disabled for the current chat session.")
        return None, None, next_chat_id, True

    from occ.commons.prompts import get_prompt_system_message

    system_message = get_prompt_system_message(selected_prompt)
    next_chat_id = _ask_session_switch_behavior(custom_style, selected_prompt, current_chat_id, 'prompt')
    if next_chat_id is None:
        return current_prompt_key, None, current_chat_id, False
    logger.log_g(f"Switched prompt to: {selected_prompt}")
    return selected_prompt, system_message, next_chat_id, True


def _select_model_interactively(custom_style, active_profile, api_server_type, current_model, current_chat_id):
    import questionary

    available_models = _get_available_models(api_server_type, active_profile, current_model)
    if not available_models:
        logger.log_r("No models available to switch.")
        return current_model, current_chat_id, False

    if api_server_type == 'azure-openai':
        selected_model = questionary.select(
            "Select a model for the current chat session:",
            choices=available_models,
            default=current_model if current_model in available_models else None,
            style=custom_style
        ).ask()

        if selected_model is None:
            logger.log_g("Model switch cancelled.")
            return current_model, current_chat_id, False

        if selected_model == current_model:
            logger.log_g(f"Model '{selected_model}' is already active.")
            return current_model, current_chat_id, False

        next_chat_id = _ask_session_switch_behavior(custom_style, selected_model, current_chat_id, 'model')
        if next_chat_id is None:
            return current_model, current_chat_id, False

        logger.log_g(f"Switched model to: {selected_model}")
        return selected_model, next_chat_id, True

    choices = []
    for model_name in available_models:
        choices.append(questionary.Choice(title=model_name, value=model_name))
    choices.append(questionary.Choice(title='[Custom Input]', value='[Custom Input]'))

    selected_model = questionary.select(
        "Select a model for the current chat session:",
        choices=choices,
        default=current_model if current_model in available_models else None,
        style=custom_style
    ).ask()

    if selected_model is None:
        logger.log_g("Model switch cancelled.")
        return current_model, current_chat_id, False

    if selected_model == '[Custom Input]':
        selected_model = questionary.text(
            "Enter the model name:",
            default=current_model or '',
            style=custom_style
        ).ask()
        if not selected_model:
            logger.log_g("Model switch cancelled.")
            return current_model, current_chat_id, False

    if selected_model == current_model:
        logger.log_g(f"Model '{selected_model}' is already active.")
        return current_model, current_chat_id, False

    next_chat_id = _ask_session_switch_behavior(custom_style, selected_model, current_chat_id, 'model')
    if next_chat_id is None:
        return current_model, current_chat_id, False

    logger.log_g(f"Switched model to: {selected_model}")
    return selected_model, next_chat_id, True


def _handle_interactive_command(command, custom_style, active_profile, api_server_type, current_prompt_key, current_model, current_chat_id):
    normalized = command.lower()

    if normalized == '/':
        selected_command = _pick_shortcut_command(custom_style)
        if not selected_command:
            return True, current_prompt_key, None, current_model, current_chat_id
        return _handle_interactive_command(
            selected_command,
            custom_style,
            active_profile,
            api_server_type,
            current_prompt_key,
            current_model,
            current_chat_id,
        )

    if normalized in {'/help', '/h'}:
        _show_interactive_help(current_prompt_key, current_model, current_chat_id)
        return True, current_prompt_key, None, current_model, current_chat_id

    if normalized in {'/exit', '/quit', '/q'}:
        print_formatted_text(HTML("<ansired>Bye 👋</ansired>"))
        raise SystemExit(0)

    if normalized in {'/pmp', '/p', '/prompt'}:
        next_prompt_key, next_system_message, next_chat_id, changed = _select_prompt_interactively(
            custom_style,
            current_prompt_key,
            current_chat_id,
        )
        if changed:
            return True, next_prompt_key, next_system_message, current_model, next_chat_id
        return True, current_prompt_key, None, current_model, current_chat_id

    if normalized in {'/m', '/model'}:
        next_model, next_chat_id, changed = _select_model_interactively(
            custom_style,
            active_profile,
            api_server_type,
            current_model,
            current_chat_id,
        )
        if changed:
            return True, current_prompt_key, None, next_model, next_chat_id
        return True, current_prompt_key, None, current_model, current_chat_id

    return False, current_prompt_key, None, current_model, current_chat_id


@click.command()
@click.argument('message', required=False)
@click.option('-id', help='Enter chat id, something like context')
@click.option('--profile', '-p', envvar="OCC_PROFILE", help='Enable profile name')
@click.option("--model", "-m", envvar="OCC_MODEL", default="o1-mini",
              help="Specify the model to use for this chat session")
@click.option('--file', '-f', type=click.Path(exists=True), help='The prompt or message is from a file')
@click.option('--prompt', '-pt', help='Use a predefined prompt template (e.g., translate, improve). Use "occ prompt list" to see available prompts.')
def chat(message, id, profile, model, file, prompt):
    """Start a chat session with the AI"""
    try:
        from occ.commons import config as cfg
        custom_style = _build_questionary_style()

        # Use default profile if none specified
        active_profile = profile or "default"

        # Check if profile exists
        if not cfg.profile_exists(active_profile):
            logger.log_r(f"Profile '{active_profile}' does not exist. Please run 'occ configure' first.")
            return

        # Check API server type
        api_server_type = cfg.get_env(active_profile, 'api_server_type')

        model, ok = _resolve_initial_model(api_server_type, active_profile, model, message, file, custom_style)
        if not ok:
            return

        current_prompt_key, system_message, ok = _resolve_prompt_state(active_profile, prompt)
        if not ok:
            return

        current_chat_id = id or DEFAULT_CHAT_LOG_ID

        if file:
            with open(file, 'r') as f:
                message = f.read()
        elif not message and not sys.stdin.isatty():
            message = sys.stdin.read()
        elif not message:
            session = PromptSession(
                show_frame=True,
                style=style_from_pygments_cls(get_style_by_name("tango")), multiline=True, wrap_lines=True,
                cursor=ModalCursorShapeConfig(),
            )
            while True:
                try:
                    message = session.prompt(
                        "👤 You: \n",
                        bottom_toolbar=_build_bottom_toolbar(current_prompt_key, model, current_chat_id),
                    )
                    if not message:
                        continue

                    handled, next_prompt_key, next_system_message, next_model, next_chat_id = _handle_interactive_command(
                        message,
                        custom_style,
                        active_profile,
                        api_server_type,
                        current_prompt_key,
                        model,
                        current_chat_id,
                    )
                    if handled:
                        current_prompt_key = next_prompt_key
                        if next_system_message is not None or current_prompt_key is None:
                            system_message = next_system_message
                        model = next_model
                        current_chat_id = next_chat_id
                        continue

                    CommandChat(profile=active_profile, chat_log_id=current_chat_id, system_message=system_message).chat(message, model)
                    print()
                except KeyboardInterrupt:
                    print_formatted_text(HTML("<ansired>\n(Interrupted)</ansired>"))
                    raise SystemExit(0)
        CommandChat(profile=active_profile, chat_log_id=current_chat_id, system_message=system_message).chat(message, model)
    except Exception as e:
        logger.log_g(str(e))


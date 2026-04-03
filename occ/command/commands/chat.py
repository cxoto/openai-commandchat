"""Chat command"""

import sys
import click
from prompt_toolkit import PromptSession, print_formatted_text, HTML
from prompt_toolkit.cursor_shapes import ModalCursorShapeConfig
from prompt_toolkit.styles import style_from_pygments_cls
from pygments.styles.tango import TangoStyle

import occ.utils.logger as logger
from occ.CommandChat import CommandChat


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
        import questionary
        from occ.commons import config as cfg
        from questionary import Style
        
        custom_style = Style([
            ('qmark', 'fg:#673ab7 bold'),
            ('question', 'bold'),
            ('answer', 'fg:#f44336 bold'),
            ('pointer', 'fg:#673ab7 bold'),
            ('highlighted', 'fg:#673ab7 bold'),
        ])
        
        # Use default profile if none specified
        active_profile = profile or "default"
        
        # Check if profile exists
        if not cfg.profile_exists(active_profile):
            logger.log_r(f"Profile '{active_profile}' does not exist. Please run 'occ configure' first.")
            return
        
        # Check API server type
        api_server_type = cfg.get_env(active_profile, 'api_server_type')
        
        # For azure-openai, check for multiple models
        if api_server_type == 'azure-openai':
            available_models = cfg.get_profile_models(active_profile)
            
            if not available_models:
                logger.log_r(f"No models configured for profile '{active_profile}'. Please run 'occ configure' first.")
                return
            
            # If user didn't specify model and there are multiple models, let them choose
            if not model or model == "o1-mini":  # o1-mini is the default, treat as not specified
                if len(available_models) > 1:
                    # Interactive mode - let user select model
                    if not message and not file and sys.stdin.isatty():
                        model = questionary.select(
                            "Select a model:",
                            choices=available_models,
                            style=custom_style
                        ).ask()
                        
                        if model is None:
                            logger.log_r("Model selection cancelled.")
                            return
                    else:
                        # Non-interactive mode - use first available model
                        model = available_models[0]
                        logger.log_g(f"Using model: {model}")
                else:
                    # Only one model, use it
                    model = available_models[0]
            else:
                # User specified a model, verify it exists
                if model not in available_models:
                    logger.log_r(f"Model '{model}' not found in profile '{active_profile}'. Available models: {', '.join(available_models)}")
                    return
        
        # Handle prompt template - command line -pt has highest priority
        system_message = None
        prompt_source = None  # Track where the prompt came from
        
        if prompt:
            # Command line -pt parameter has highest priority
            from occ.commons.prompts import get_prompt_system_message, list_prompts
            system_message = get_prompt_system_message(prompt)
            if not system_message:
                logger.log_r(f"Prompt '{prompt}' not found. Available prompts:")
                for key, value in list_prompts().items():
                    logger.log_g(f"  - {key}: {value['description']}")
                return
            prompt_source = "command line"
            logger.log_g(f"Using prompt template: {prompt} (from {prompt_source})")
        else:
            # Check for profile default prompt
            profile_default_prompt = cfg.get_profile_default_prompt(active_profile)
            if profile_default_prompt:
                from occ.commons.prompts import get_prompt_system_message
                system_message = get_prompt_system_message(profile_default_prompt)
                if system_message:
                    prompt_source = f"profile '{active_profile}'"
                    logger.log_g(f"Using default prompt: {profile_default_prompt} (from {prompt_source})")
        
        if file:
            with open(file, 'r') as f:
                message = f.read()
        elif not message and not sys.stdin.isatty():
            message = sys.stdin.read()
        elif not message:
            session = PromptSession(
                show_frame=True,
                style=style_from_pygments_cls(TangoStyle), multiline=True, wrap_lines=True,
                cursor=ModalCursorShapeConfig(),
            )
            while True:
                try:
                    message = session.prompt("👤 You: \n")
                    if not message:
                        continue
                    if message.lower() in {"/help", "/Help"}:
                        print_formatted_text(HTML(
                            "<b>Help Info: \n</b><ansigreen>Type your message and press ESC+Enter or OPT+Enter to send.\n"
                            "Use /exit or /quit or /q to leave the chat.\n"
                            "Use /help to show this message again.\n"
                            "Use -pt <prompt_key> when starting chat to use a prompt template.\n"
                            "Run 'occ prompt list' to see available prompt templates.</ansigreen>\n"))
                        continue
                    if message.lower() in {"/exit", "/quit", "/q"}:
                        print_formatted_text(HTML("<ansired>Bye 👋</ansired>"))
                        exit(0)
                    CommandChat(profile=active_profile, chat_log_id=id, system_message=system_message).chat(message, model)
                    print()
                except KeyboardInterrupt:
                    print_formatted_text(HTML("<ansired>\n(Interrupted)</ansired>"))
                    exit(0)
        CommandChat(profile=active_profile, chat_log_id=id, system_message=system_message).chat(message, model)
    except Exception as e:
        logger.log_g(str(e))


from __future__ import absolute_import

import importlib.metadata
import sys

import click
from prompt_toolkit import PromptSession, print_formatted_text, HTML
from prompt_toolkit.cursor_shapes import ModalCursorShapeConfig
from prompt_toolkit.styles import style_from_pygments_cls
from pygments.lexers.markup import MarkdownLexer
from pygments.styles.tango import TangoStyle

import occ.utils.logger as logger
from occ.CommandChat import CommandChat


VERSION = importlib.metadata.version("commandchat")


@click.group()
@click.version_option(version=VERSION, prog_name='openai-commandchat')
def commandchat_operator():
    pass


@click.command()
@click.option('--profile', '-p', help='Specify profile name to configure')
def configure(profile):
    """Configure OpenAI or Azure OpenAI profiles"""
    if profile is not None:
        # If profile is specified, configure it directly
        from occ.configuration.profile_config import configure_profile
        configure_profile(profile)
    else:
        # No profile specified, show interactive selection
        from occ.configuration.profile_config import select_profile_interactively
        select_profile_interactively()


@click.command()
@click.argument('message', required=False)
@click.option('-id', help=' enter chat id, something like context')
@click.option('--profile', '-p', envvar="OCC_PROFILE", help='Enable profile name')
@click.option("--model", "-m", envvar="OCC_MODEL", default="o1-mini",
              help="Specify the model to use for this chat session")
@click.option('--file', '-f', type=click.Path(exists=True), help='the prompt or message is from a file')
def chat(message, id, profile, model, file):
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
                            "Use /help to show this message again.</ansigreen>\n"))
                        continue
                    if message.lower() in {"/exit", "/quit", "/q"}:
                        print_formatted_text(HTML("<ansired>Bye 👋</ansired>"))
                        exit(0)
                    CommandChat(profile=active_profile, chat_log_id=id).chat(message, model)
                    print()
                except KeyboardInterrupt:
                    print_formatted_text(HTML("<ansired>\n(Interrupted)</ansired>"))
                    exit(0)
        CommandChat(profile=active_profile, chat_log_id=id).chat(message, model)
    except Exception as e:
        logger.log_g(str(e))


size_map = {
    "s": "256x256",
    "S": "256x256",
    "m": "512x512",
    "M": "512x512",
    "l": "1024x1024",
    "L": "1024x1024"
}


@click.command()
@click.option('-desc', help=' Enter the description of the images you want')
@click.option('-size',
              help=' Enter the size(S/s,M/m,L/l): \n   small - 256x256 \n   middle  - 512x512 \n   large - 1024x1024')
@click.option('-num', count=True, help=' Enter the number to generate the specified number of images')
@click.option('-profile', help='Enable profile name')
def image(desc, size, num, profile):
    number = num if num > 0 else 1
    size = size_map.get(size)
    size_value = size if size is not None else "512x512"
    CommandChat(profile=profile).image_create(desc, size_value, number if number < 5 else 4)


commandchat_operator.add_command(configure)
commandchat_operator.add_command(chat)
commandchat_operator.add_command(image)


def main():
    commandchat_operator()


if __name__ == '__main__':
    main()

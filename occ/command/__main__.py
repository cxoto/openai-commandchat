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


@click.group()
def configure():
    """Configure OpenAI or Azure OpenAI profiles and prompts"""
    pass


@click.command(name='profile')
@click.option('--profile', '-p', help='Specify profile name to configure')
def configure_profile_cmd(profile):
    """Configure a profile"""
    if profile is not None:
        # If profile is specified, configure it directly
        from occ.configuration.profile_config import configure_profile
        configure_profile(profile)
    else:
        # No profile specified, show interactive selection
        from occ.configuration.profile_config import select_profile_interactively
        select_profile_interactively()


@click.command(name='delete-profile')
@click.argument('profile')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
def delete_profile_cmd(profile, yes):
    """Delete a profile"""
    import questionary
    from occ.commons import config as cfg
    
    if not cfg.profile_exists(profile):
        logger.log_r(f"Profile '{profile}' does not exist")
        return
    
    if profile == 'default':
        logger.log_r("Cannot delete the 'default' profile")
        return
    
    # Confirm deletion
    if not yes:
        confirm = questionary.confirm(
            f"Are you sure you want to delete profile '{profile}'? This will also remove all associated models.",
            default=False
        ).ask()
        
        if not confirm:
            logger.log_g("Deletion cancelled")
            return
    
    cfg.remove_profile(profile)
    logger.log_g(f"Profile '{profile}' deleted successfully")


@click.command(name='list-profiles')
def list_profiles_cmd():
    """List all configured profiles"""
    from occ.commons import config as cfg
    from rich.table import Table
    from rich.console import Console
    
    profiles = cfg.get_profiles()
    if not profiles:
        logger.log_r("No profiles found. Run 'occ configure profile' to create one.")
        return
    
    console = Console()
    table = Table(title="Configured Profiles", show_header=True, header_style="bold magenta")
    table.add_column("Profile", style="cyan", width=20)
    table.add_column("API Type", style="green", width=15)
    table.add_column("Default Prompt", style="yellow", width=20)
    table.add_column("Models", style="blue")
    
    for profile in profiles:
        api_type = cfg.get_env(profile, 'api_server_type') or 'N/A'
        default_prompt = cfg.get_profile_default_prompt(profile) or 'None'
        models = cfg.get_profile_models(profile)
        models_str = ', '.join(models) if models else 'N/A'
        table.add_row(profile, api_type, default_prompt, models_str)
    
    console.print(table)


# Add subcommands to configure group
configure.add_command(configure_profile_cmd)
configure.add_command(delete_profile_cmd)
configure.add_command(list_profiles_cmd)


@click.command()
@click.argument('message', required=False)
@click.option('-id', help=' enter chat id, something like context')
@click.option('--profile', '-p', envvar="OCC_PROFILE", help='Enable profile name')
@click.option("--model", "-m", envvar="OCC_MODEL", default="o1-mini",
              help="Specify the model to use for this chat session")
@click.option('--file', '-f', type=click.Path(exists=True), help='the prompt or message is from a file')
@click.option('--prompt', '-pt', help='Use a predefined prompt template (e.g., translate, improve). Use "occ prompts" to see available prompts.')
def chat(message, id, profile, model, file, prompt):
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
                            "Run 'occ prompts' to see available prompt templates.</ansigreen>\n"))
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


@click.group()
def prompts():
    """Manage prompt templates"""
    pass


@click.command(name='list')
def list_prompts_cmd():
    """List all available prompt templates"""
    from occ.commons.prompts import list_prompts
    from rich.table import Table
    from rich.console import Console
    
    console = Console()
    table = Table(title="Available Prompt Templates", show_header=True, header_style="bold magenta")
    table.add_column("Key", style="cyan", width=15)
    table.add_column("Name", style="green", width=25)
    table.add_column("Description", style="yellow", width=35)
    table.add_column("Type", style="blue", width=10)
    
    for key, value in list_prompts().items():
        prompt_type = "Built-in" if value.get("builtin", False) else "Custom"
        table.add_row(key, value["name"], value["description"], prompt_type)
    
    console.print(table)
    console.print("\n[bold green]Usage:[/bold green] occ chat -pt <key> \"your message\"")
    console.print("[bold green]Example:[/bold green] occ chat -pt translate \"你好世界\"")


@click.command(name='add')
@click.argument('key')
@click.option('--name', '-n', required=True, help='Display name for the prompt')
@click.option('--description', '-d', required=True, help='Brief description of the prompt')
@click.option('--system-prompt', '-s', required=True, help='The system prompt content')
def add_prompt_cmd(key, name, description, system_prompt):
    """Add a new custom prompt template"""
    from occ.commons.prompts import add_prompt
    
    success, message = add_prompt(key, name, description, system_prompt)
    if success:
        logger.log_g(message)
    else:
        logger.log_r(message)


@click.command(name='modify')
@click.argument('key')
@click.option('--name', '-n', help='New display name')
@click.option('--description', '-d', help='New description')
@click.option('--system-prompt', '-s', help='New system prompt content')
def modify_prompt_cmd(key, name, description, system_prompt):
    """Modify an existing custom prompt template"""
    from occ.commons.prompts import modify_prompt
    
    if not any([name, description, system_prompt]):
        logger.log_r("At least one of --name, --description, or --system-prompt must be provided")
        return
    
    success, message = modify_prompt(key, name, description, system_prompt)
    if success:
        logger.log_g(message)
    else:
        logger.log_r(message)


@click.command(name='remove')
@click.argument('key')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
def remove_prompt_cmd(key, yes):
    """Remove a custom prompt template"""
    from occ.commons.prompts import remove_prompt, get_prompt
    import questionary
    
    # Check if prompt exists
    prompt = get_prompt(key)
    if not prompt:
        logger.log_r(f"Prompt '{key}' not found")
        return
    
    if prompt.get("builtin", False):
        logger.log_r(f"Cannot remove built-in prompt '{key}'")
        return
    
    # Confirm removal
    if not yes:
        confirm = questionary.confirm(
            f"Are you sure you want to remove prompt '{key}'?",
            default=False
        ).ask()
        
        if not confirm:
            logger.log_g("Removal cancelled")
            return
    
    success, message = remove_prompt(key)
    if success:
        logger.log_g(message)
    else:
        logger.log_r(message)


@click.command(name='show')
@click.argument('key')
def show_prompt_cmd(key):
    """Show detailed information about a prompt template"""
    from occ.commons.prompts import get_prompt
    from rich.console import Console
    from rich.panel import Panel
    
    prompt = get_prompt(key)
    if not prompt:
        logger.log_r(f"Prompt '{key}' not found")
        return
    
    console = Console()
    prompt_type = "Built-in" if prompt.get("builtin", False) else "Custom"
    
    console.print(f"\n[bold cyan]Key:[/bold cyan] {key}")
    console.print(f"[bold cyan]Name:[/bold cyan] {prompt['name']}")
    console.print(f"[bold cyan]Type:[/bold cyan] {prompt_type}")
    console.print(f"[bold cyan]Description:[/bold cyan] {prompt['description']}")
    console.print(f"\n[bold cyan]System Prompt:[/bold cyan]")
    console.print(Panel(prompt['system_prompt'], border_style="green"))


# Add subcommands to prompts group
prompts.add_command(list_prompts_cmd)
prompts.add_command(add_prompt_cmd)
prompts.add_command(modify_prompt_cmd)
prompts.add_command(remove_prompt_cmd)
prompts.add_command(show_prompt_cmd)


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
commandchat_operator.add_command(prompts)
commandchat_operator.add_command(image)


def main():
    commandchat_operator()


if __name__ == '__main__':
    main()

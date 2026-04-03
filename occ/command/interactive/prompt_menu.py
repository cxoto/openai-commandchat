"""Interactive menu for prompt management"""

import questionary
from questionary import Style
import occ.utils.logger as logger


# Custom style for questionary
CUSTOM_STYLE = Style([
    ('qmark', 'fg:#673ab7 bold'),
    ('question', 'bold'),
    ('answer', 'fg:#f44336 bold'),
    ('pointer', 'fg:#673ab7 bold'),
    ('highlighted', 'fg:#673ab7 bold'),
])


def interactive_prompt_menu():
    """Interactive menu for managing prompts"""
    while True:
        action = questionary.select(
            "Prompt Management - What would you like to do?",
            choices=[
                'List all prompts',
                'Show prompt details',
                'Add new prompt',
                'Modify prompt',
                'Remove prompt',
                'Exit'
            ],
            style=CUSTOM_STYLE
        ).ask()
        
        if action is None or action == 'Exit':
            break
        elif action == 'List all prompts':
            from occ.command.commands.prompt import list_cmd
            list_cmd.callback()
        elif action == 'Show prompt details':
            interactive_show_prompt()
        elif action == 'Add new prompt':
            interactive_add_prompt()
        elif action == 'Modify prompt':
            interactive_modify_prompt()
        elif action == 'Remove prompt':
            interactive_remove_prompt()


def interactive_show_prompt():
    """Interactive prompt selection for showing details"""
    from occ.commons.prompts import list_prompts
    from occ.command.commands.prompt import show_cmd
    
    prompts_dict = list_prompts()
    if not prompts_dict:
        logger.log_r("No prompts available")
        return
    
    prompt_key = questionary.select(
        "Select a prompt to view:",
        choices=list(prompts_dict.keys()),
        style=CUSTOM_STYLE
    ).ask()
    
    if prompt_key:
        show_cmd.callback(prompt_key)


def interactive_add_prompt():
    """Interactive prompt addition"""
    from occ.command.commands.prompt import add_cmd
    
    key = questionary.text("Enter prompt key (e.g., my-prompt):", style=CUSTOM_STYLE).ask()
    if not key:
        return
    
    name = questionary.text("Enter prompt name:", style=CUSTOM_STYLE).ask()
    if not name:
        return
    
    description = questionary.text("Enter prompt description:", style=CUSTOM_STYLE).ask()
    if not description:
        return
    
    system_prompt = questionary.text(
        "Enter system prompt content:",
        multiline=True,
        style=CUSTOM_STYLE
    ).ask()
    if not system_prompt:
        return
    
    add_cmd.callback(key, name, description, system_prompt)


def interactive_modify_prompt():
    """Interactive prompt modification"""
    from occ.commons.prompts import list_prompts, get_prompt
    from occ.command.commands.prompt import modify_cmd
    
    user_prompts = {k: v for k, v in list_prompts().items() if not v.get('builtin', False)}
    
    if not user_prompts:
        logger.log_r("No custom prompts to modify. Built-in prompts cannot be modified.")
        return
    
    prompt_key = questionary.select(
        "Select a prompt to modify:",
        choices=list(user_prompts.keys()),
        style=CUSTOM_STYLE
    ).ask()
    
    if not prompt_key:
        return
    
    current_prompt = get_prompt(prompt_key)
    
    # Ask what to modify
    fields = questionary.checkbox(
        "What would you like to modify?",
        choices=['Name', 'Description', 'System Prompt'],
        style=CUSTOM_STYLE
    ).ask()
    
    if not fields:
        return
    
    name = None
    description = None
    system_prompt = None
    
    if 'Name' in fields:
        name = questionary.text(
            "Enter new name:",
            default=current_prompt['name'],
            style=CUSTOM_STYLE
        ).ask()
    
    if 'Description' in fields:
        description = questionary.text(
            "Enter new description:",
            default=current_prompt['description'],
            style=CUSTOM_STYLE
        ).ask()
    
    if 'System Prompt' in fields:
        system_prompt = questionary.text(
            "Enter new system prompt:",
            default=current_prompt['system_prompt'],
            multiline=True,
            style=CUSTOM_STYLE
        ).ask()
    
    modify_cmd.callback(prompt_key, name, description, system_prompt)


def interactive_remove_prompt():
    """Interactive prompt removal"""
    from occ.commons.prompts import list_prompts
    from occ.command.commands.prompt import remove_cmd
    
    user_prompts = {k: v for k, v in list_prompts().items() if not v.get('builtin', False)}
    
    if not user_prompts:
        logger.log_r("No custom prompts to remove. Built-in prompts cannot be removed.")
        return
    
    prompt_key = questionary.select(
        "Select a prompt to remove:",
        choices=list(user_prompts.keys()),
        style=CUSTOM_STYLE
    ).ask()
    
    if prompt_key:
        remove_cmd.callback(prompt_key, False)


import questionary
from questionary import Style

import occ.commons.config as config
import occ.utils.logger as logger

# Custom style for questionary
custom_style = Style([
    ('qmark', 'fg:#673ab7 bold'),
    ('question', 'bold'),
    ('answer', 'fg:#f44336 bold'),
    ('pointer', 'fg:#673ab7 bold'),
    ('highlighted', 'fg:#673ab7 bold'),
    ('selected', 'fg:#cc5454'),
    ('separator', 'fg:#cc5454'),
    ('instruction', ''),
    ('text', ''),
])

API_SERVER_TYPES = ['openai', 'azure-openai']


def select_profile_interactively():
    """Show a list of profiles and let user select one"""
    profiles = config.get_profiles()
    if not profiles:
        logger.log_r("No profiles found. Creating default profile...")
        configure_profile('default')
        return
    
    choices = profiles + ['[Create New Profile]']
    selected = questionary.select(
        "Select a profile to configure:",
        choices=choices,
        style=custom_style
    ).ask()
    
    if selected is None:
        logger.log_r("Configuration cancelled.")
        return
    
    if selected == '[Create New Profile]':
        profile_name = questionary.text(
            "Enter new profile name:",
            style=custom_style
        ).ask()
        if profile_name:
            configure_profile(profile_name)
    else:
        configure_profile(selected)


def configure_profile(profile_name):
    """Configure a profile (create new or update existing)"""
    is_existing = config.profile_exists(profile_name)
    
    if is_existing:
        logger.log_g(f"\nConfiguring existing profile: {profile_name}")
    else:
        logger.log_g(f"\nCreating new profile: {profile_name}")
        config.add_profile(profile_name)
    
    # Common configuration
    configure_common_settings(profile_name, is_existing)
    
    # API server type specific configuration
    api_server_type = config.get_env(profile_name, 'api_server_type') if is_existing else None
    api_server_type = questionary.select(
        "Select API server type:",
        choices=API_SERVER_TYPES,
        default=api_server_type if api_server_type in API_SERVER_TYPES else API_SERVER_TYPES[0],
        style=custom_style
    ).ask()
    
    if api_server_type is None:
        logger.log_r("Configuration cancelled.")
        return
    
    config.set_env(profile_name, 'api_server_type', api_server_type)
    
    if api_server_type == 'openai':
        configure_openai(profile_name, is_existing)
    elif api_server_type == 'azure-openai':
        configure_azure_openai(profile_name, is_existing)
    
    logger.log_g(f"\n✓ Profile '{profile_name}' configured successfully!")


def configure_common_settings(profile_name, is_existing):
    """Configure common settings for all API types"""
    default_limit = '4'
    if is_existing:
        existing_limit = config.get_env(profile_name, 'limit_history')
        if existing_limit:
            default_limit = existing_limit
    
    limit_history = questionary.text(
        "Limit history (number of messages to keep):",
        default=default_limit,
        style=custom_style
    ).ask()
    
    if limit_history:
        config.set_env(profile_name, 'limit_history', limit_history)


def configure_openai(profile_name, is_existing):
    """Configure OpenAI specific settings"""
    default_key = ''
    default_url = 'https://api.openai.com/v1'
    
    if is_existing:
        existing_key = config.get_env(profile_name, 'api_key')
        existing_url = config.get_env(profile_name, 'api_base_url')
        if existing_key:
            default_key = existing_key
        if existing_url:
            default_url = existing_url
    
    api_key = questionary.password(
        "OpenAI API Key:",
        default=default_key,
        style=custom_style
    ).ask()
    
    api_base_url = questionary.text(
        "API Base URL:",
        default=default_url,
        style=custom_style
    ).ask()
    
    if api_key:
        config.set_env(profile_name, 'api_key', api_key)
    if api_base_url:
        config.set_env(profile_name, 'api_base_url', api_base_url)


def configure_azure_openai(profile_name, is_existing):
    """Configure Azure OpenAI with multiple models"""
    logger.log_g("\nConfiguring Azure OpenAI models...")
    
    # Get existing models
    existing_models = config.get_profile_models(profile_name)
    
    while True:
        if existing_models:
            logger.log_g(f"\nExisting models: {', '.join(existing_models)}")
            action = questionary.select(
                "What would you like to do?",
                choices=[
                    'Add new model',
                    'Edit existing model',
                    'Remove model',
                    'Finish configuration'
                ],
                style=custom_style
            ).ask()
            
            if action is None or action == 'Finish configuration':
                break
            elif action == 'Add new model':
                add_azure_model(profile_name)
                existing_models = config.get_profile_models(profile_name)
            elif action == 'Edit existing model':
                model_to_edit = questionary.select(
                    "Select model to edit:",
                    choices=existing_models,
                    style=custom_style
                ).ask()
                if model_to_edit:
                    edit_azure_model(profile_name, model_to_edit)
            elif action == 'Remove model':
                model_to_remove = questionary.select(
                    "Select model to remove:",
                    choices=existing_models,
                    style=custom_style
                ).ask()
                if model_to_remove:
                    remove_azure_model(profile_name, model_to_remove)
                    existing_models = config.get_profile_models(profile_name)
        else:
            logger.log_g("\nNo models configured yet.")
            should_add = questionary.confirm(
                "Add a model?",
                default=True,
                style=custom_style
            ).ask()
            
            if should_add:
                add_azure_model(profile_name)
                existing_models = config.get_profile_models(profile_name)
            else:
                break


def add_azure_model(profile_name):
    """Add a new Azure OpenAI model"""
    model_name = questionary.text(
        "Model name (e.g., gpt-4, gpt-35-turbo):",
        style=custom_style
    ).ask()
    
    if not model_name:
        return
    
    edit_azure_model(profile_name, model_name)


def edit_azure_model(profile_name, model_name):
    """Edit Azure OpenAI model configuration"""
    # Get existing config if available
    existing_config = config.get_model_config(profile_name, model_name)
    
    api_key = questionary.password(
        f"API Key for {model_name}:",
        default=existing_config.get('api_key', '') if existing_config else '',
        style=custom_style
    ).ask()
    
    api_base_url = questionary.text(
        f"Azure endpoint URL for {model_name}:",
        default=existing_config.get('api_base_url', '') if existing_config else '',
        style=custom_style
    ).ask()
    
    api_version = questionary.text(
        f"API version for {model_name}:",
        default=existing_config.get('api_version', '2024-02-15-preview') if existing_config else '2024-02-15-preview',
        style=custom_style
    ).ask()
    
    if api_key and api_base_url and api_version:
        config.set_model_config(profile_name, model_name, api_key, api_base_url, api_version)
        logger.log_g(f"✓ Model '{model_name}' configured successfully!")
    else:
        logger.log_r("Configuration incomplete. Model not saved.")


def remove_azure_model(profile_name, model_name):
    """Remove an Azure OpenAI model configuration"""
    confirm = questionary.confirm(
        f"Are you sure you want to remove model '{model_name}'?",
        default=False,
        style=custom_style
    ).ask()
    
    if confirm:
        section = f"{profile_name}.{model_name}"
        config.config.remove_section(section)
        config.write_config()
        logger.log_g(f"✓ Model '{model_name}' removed.")


# Legacy functions for backward compatibility
def add_default_profile():
    """Legacy function - redirects to new configure_profile"""
    configure_profile('default')


def add_profile(profile_name):
    """Legacy function - redirects to new configure_profile"""
    configure_profile(profile_name)

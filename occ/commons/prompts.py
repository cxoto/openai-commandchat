"""
Built-in and custom prompt template management
"""

import os
import json
import logging

# Built-in default prompts (read-only)
DEFAULT_PROMPTS = {
    "translate": {
        "name": "Translation Assistant",
        "description": "Translate Chinese to English",
        "system_prompt": "You are a professional translation assistant. Please translate the Chinese text provided by the user into idiomatic English. Only output the translation result without additional explanations.",
        "builtin": True
    },
    "improve": {
        "name": "English Writing Assistant",
        "description": "Improve English sentences and identify issues",
        "system_prompt": "You are a professional English writing assistant. Please help users improve their English sentences to make them more natural for native speakers. Format your output as follows:\n\n**Improved Sentence:**\n[The improved English sentence]\n\n**Issues in Original:**\n[List grammar, word choice, and expression issues]",
        "builtin": True
    }
}


def get_home_path():
    homedir = os.environ.get('HOME', None)
    if os.name == 'nt':
        homedir = os.path.expanduser('~')
    return homedir


def get_prompts_file():
    """Get the path to user prompts configuration file"""
    homedir = get_home_path()
    prompts_dir = os.path.join(homedir, ".occ")
    os.makedirs(prompts_dir, exist_ok=True)
    return os.path.join(prompts_dir, "prompts.json")


def load_user_prompts():
    """Load user-defined prompts from file"""
    prompts_file = get_prompts_file()
    if not os.path.exists(prompts_file):
        return {}
    
    try:
        with open(prompts_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading user prompts: {e}")
        return {}


def save_user_prompts(prompts):
    """Save user-defined prompts to file"""
    prompts_file = get_prompts_file()
    try:
        with open(prompts_file, 'w', encoding='utf-8') as f:
            json.dump(prompts, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logging.error(f"Error saving user prompts: {e}")
        return False


def get_prompt(prompt_key):
    """Get a specific prompt template (checks user prompts first, then built-in)"""
    user_prompts = load_user_prompts()
    if prompt_key in user_prompts:
        return user_prompts[prompt_key]
    return DEFAULT_PROMPTS.get(prompt_key)


def list_prompts():
    """List all available prompts (built-in + user-defined)"""
    all_prompts = DEFAULT_PROMPTS.copy()
    user_prompts = load_user_prompts()
    all_prompts.update(user_prompts)
    return all_prompts


def get_prompt_system_message(prompt_key):
    """Get the system message for a prompt"""
    prompt = get_prompt(prompt_key)
    if prompt:
        return prompt["system_prompt"]
    return None


def add_prompt(key, name, description, system_prompt):
    """Add a new user-defined prompt"""
    if key in DEFAULT_PROMPTS:
        return False, f"Cannot override built-in prompt '{key}'"
    
    user_prompts = load_user_prompts()
    user_prompts[key] = {
        "name": name,
        "description": description,
        "system_prompt": system_prompt,
        "builtin": False
    }
    
    if save_user_prompts(user_prompts):
        return True, f"Prompt '{key}' added successfully"
    return False, "Failed to save prompt"


def modify_prompt(key, name=None, description=None, system_prompt=None):
    """Modify an existing user-defined prompt"""
    if key in DEFAULT_PROMPTS:
        return False, f"Cannot modify built-in prompt '{key}'"
    
    user_prompts = load_user_prompts()
    if key not in user_prompts:
        return False, f"Prompt '{key}' not found"
    
    # Update only provided fields
    if name is not None:
        user_prompts[key]["name"] = name
    if description is not None:
        user_prompts[key]["description"] = description
    if system_prompt is not None:
        user_prompts[key]["system_prompt"] = system_prompt
    
    if save_user_prompts(user_prompts):
        return True, f"Prompt '{key}' modified successfully"
    return False, "Failed to save prompt"


def remove_prompt(key):
    """Remove a user-defined prompt"""
    if key in DEFAULT_PROMPTS:
        return False, f"Cannot remove built-in prompt '{key}'"
    
    user_prompts = load_user_prompts()
    if key not in user_prompts:
        return False, f"Prompt '{key}' not found"
    
    del user_prompts[key]
    
    if save_user_prompts(user_prompts):
        return True, f"Prompt '{key}' removed successfully"
    return False, "Failed to save prompts"



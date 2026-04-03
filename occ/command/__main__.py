"""
OpenAI CommandChat - Command Line Interface

Main entry point for the occ CLI tool.
"""

from __future__ import absolute_import

import importlib.metadata
import click

# Import command modules
from occ.command.commands.prompt import prompt
from occ.command.commands.profile import configure
from occ.command.commands.chat import chat
from occ.command.commands.image import image


VERSION = importlib.metadata.version("commandchat")


@click.group()
@click.version_option(version=VERSION, prog_name='openai-commandchat')
def cli():
    """OpenAI CommandChat - AI-powered command-line chat tool"""
    pass


# Register commands
cli.add_command(configure)
cli.add_command(chat)
cli.add_command(prompt)
cli.add_command(image)


def main():
    """Main entry point"""
    cli()


if __name__ == '__main__':
    main()


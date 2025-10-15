from __future__ import absolute_import

import click
import importlib.metadata

import occ.utils.logger as logger
from occ.configuration.profile_config import add_profile, add_default_profile
from occ.CommandChat import CommandChat
from occ.utils.CommonUtil import waiting_stop

VERSION = importlib.metadata.version("commandchat")


@click.group()
@click.version_option(version=VERSION, prog_name='openai-commandchat')
def commandchat_operator():
    pass


@click.command()
@click.option('--profile', '-p', help='Enable profile name')
def configure(profile):
    if profile is not None:
        add_profile(profile)
    else:
        add_default_profile()


@click.command()
@click.argument('message')
@click.option('-id', help=' enter chat id, something like context')
@click.option('--profile', '-p', help='Enable profile name')
@click.option("--model", "-m", envvar="OCC_MODEL", default="o1-mini", help="Specify the model to use for this chat session")
def chat(message, id, profile, model):
    try:
        CommandChat(profile=profile, chat_log_id=id).chat(message, model)
    except Exception as e:
        logger.log_g(str(e))
        waiting_stop()


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

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
from occ.configuration.profile_config import add_profile, add_default_profile
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
@click.argument('message', required=False)
@click.option('-id', help=' enter chat id, something like context')
@click.option('--profile', '-p', envvar="OCC_PROFILE", help='Enable profile name')
@click.option("--model", "-m", envvar="OCC_MODEL", default="o1-mini",
              help="Specify the model to use for this chat session")
@click.option('--file', '-f', type=click.Path(exists=True), help='the prompt or message is from a file')
def chat(message, id, profile, model, file):
    try:
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
                    CommandChat(profile=profile, chat_log_id=id).chat(message, model)
                    print()
                except KeyboardInterrupt:
                    print_formatted_text(HTML("<ansired>\n(Interrupted)</ansired>"))
                    exit(0)
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

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import AsyncGenerator

from openai import AzureOpenAI
from openai import OpenAI
from openai.types.chat.chat_completion_chunk import Choice
from prompt_toolkit import print_formatted_text, HTML, Application
from prompt_toolkit.clipboard.pyperclip import PyperclipClipboard
from prompt_toolkit.layout import Layout, HSplit
from prompt_toolkit.widgets import TextArea
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown

from occ.commons.config import get_env

DEFAULT_CHAT_LOG_ID = "chat-1"
DEFAULT_PROFILE = "default"
USER_COLOR = "ansiyellow"
ASSISTANT_COLOR = "ansicyan"
TYPING_DELAY = 0.01  # 打字速度（秒/字符）
SEPARATOR = "─" * 30


def get_home_path():
    homedir = os.environ.get('HOME', None)
    if os.name == 'nt':
        homedir = os.path.expanduser('~')
    return homedir


clip = PyperclipClipboard()
console = Console()

def print_formatted(content: str, live: Live):
    md = Markdown(content)
    live.update(md)
    sys.stdout.flush()


class CommandChat:
    partial_text = []
    role = None

    def __init__(self, profile=None, chat_log_id=None):
        now = time.strftime("%Y%m%d", time.localtime())
        self.api_key = get_env(profile or DEFAULT_PROFILE, "api_key")
        self.api_base = get_env(profile or DEFAULT_PROFILE, "api_base_url")
        os.environ.setdefault("OPENAI_API_KEY", self.api_key)
        os.environ.setdefault("OPENAI_BASE_URL", self.api_base)
        self.limit_history = int(get_env(profile or DEFAULT_PROFILE, "limit_history") or 4)
        self.chat_log_id = chat_log_id or DEFAULT_CHAT_LOG_ID
        self.folder_path = os.path.join(get_home_path(), ".occ", profile or DEFAULT_PROFILE)
        self.image_folder_path = os.path.join(self.folder_path, "images")
        self.file_name = os.path.join(self.folder_path, f"{self.chat_log_id}.log")
        os.makedirs(self.folder_path, exist_ok=True)
        os.makedirs(self.image_folder_path, exist_ok=True)
        self.model = None
        if not os.path.exists(self.file_name):
            open(self.file_name, 'w').close()
        self.history_path = Path(self.folder_path, self.chat_log_id) / f"md_history_{now}.md"
        self.messages = [json.loads(line) for line in (line.strip() for line in open(self.file_name)) if line.strip()]
        if "azure" == get_env(profile or DEFAULT_PROFILE, "api_server_type"):
            self.client = AzureOpenAI(api_key=self.api_key,
                                      api_version=get_env(profile or DEFAULT_PROFILE, "api_version"),
                                      azure_endpoint=self.api_base)
        else:
            self.client = OpenAI()

    def image_create(self, description, size, num):
        raise NotImplementedError

    def chat(self, message, model):
        print_formatted_text(HTML(f"<{ASSISTANT_COLOR}>🤖 Assistant: </{ASSISTANT_COLOR}>"))
        if model == "gpt-35-turbo-instruct":
            self.completions(message, model)
        else:
            self.chat_completions(message, model)

    def completions(self, message, model):
        stream = self.client.completions.create(
            model=model,
            prompt=message,
            max_tokens=4090 - len(message),
            temperature=0.1,
            stream=True
        )
        completion_text = ''
        with Live(console=console, refresh_per_second=8) as live:
            for completion in stream:
                for choice in completion.choices:
                    completion_text += choice.text
                    print_formatted(completion_text, live)
        clip.set_text(completion_text)
        print("\n")

    def chat_completions(self, message, model):
        message = {"role": "user", "content": message}
        self.messages.append(message)
        self.model = model
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            final_text = loop.run_until_complete(self.print_streaming(self.async_stream))
        except KeyboardInterrupt:
            final_text = None
        finally:
            loop.close()

        if final_text is None:
            console.print("\n[bold red]Stream was interrupted or user exited (no final output).[/bold red]")
            sys.exit(0)
        md = Markdown(final_text)
        self.append_to_history(final_text)
        console.print(md)
        clip.set_text(final_text)
        self.record_chat_logs(message, {"role": self.role, "content": final_text.replace("\n\n", "")})

    async def async_stream(self) -> AsyncGenerator[Choice, None]:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            temperature=1,
            top_p=1,
            frequency_penalty=0.0,
            stream=True
        )
        for chunk in response:
            if chunk.choices is None or len(chunk.choices) == 0:
                continue
            choice = chunk.choices[0]
            await asyncio.sleep(0.01)
            yield choice

    async def print_streaming(self, async_stream):
        self.partial_text = []
        text_area = TextArea(
            text="",
            wrap_lines=True,
            read_only=True,
        )
        app = Application(layout=Layout(HSplit([text_area])), full_screen=False)

        async def producer():
            try:
                async for chunk in async_stream():
                    delta = chunk.delta
                    if chunk.finish_reason == "stop": break
                    if self.role is None and delta.role:
                        self.role = delta.role
                    if delta.content:
                        self.partial_text.append(delta.content)
                        joined = "".join(self.partial_text)
                        text_area.text = joined
                        text_area.buffer.cursor_position = len(text_area.buffer.text)
                        app.invalidate()
                text_area.text = ""
                app.invalidate()
                app.exit()
            except asyncio.CancelledError:
                app.exit(result=None)
            except Exception as e:
                self.partial_text.append(f"\n\n[ERROR] {e}")
                app.exit(result="".join(self.partial_text))

        app.create_background_task(producer())
        await app.run_async()
        return "".join(self.partial_text)

    def record_chat_logs(self, content, completion_text):
        with open(self.file_name, 'r+') as f:
            lines = f.readlines()
            if len(lines) >= self.limit_history:
                limit_history_ = (len(lines) + 2 - self.limit_history)
                with open(os.path.join(self.folder_path, self.chat_log_id + '_history.log'), 'a+') as hf:
                    hf.writelines("\n")
                    hf.writelines(lines[:limit_history_])
                lines = lines[limit_history_:]
            if len(lines) == 0:
                lines.append('{}\n{}'.format(json.dumps(content, ensure_ascii=False),
                                             json.dumps(completion_text, ensure_ascii=False)))
            else:
                lines.append('\n{}\n{}'.format(json.dumps(content, ensure_ascii=False),
                                               json.dumps(completion_text, ensure_ascii=False)))
            f.seek(0)
            f.truncate()
            f.writelines(lines)

    def append_to_history(self, md_text: str):
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        # 追加分隔符 + markdown 内容
        with self.history_path.open("a", encoding="utf-8") as f:
            f.write("\n\n---\n\n")
            f.write(md_text)

    def read_history(self) -> str:
        if not self.history_path.exists():
            return ""
        return self.history_path.read_text(encoding="utf-8")


if __name__ == '__main__':
    command_chat = CommandChat()
    command_chat.chat("帮我写一个python的冒泡排序算法", "o1-mini")

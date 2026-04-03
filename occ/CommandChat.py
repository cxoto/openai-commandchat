import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import AsyncGenerator, Optional
from dataclasses import dataclass

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


@dataclass
class StreamChunk:
    """Unified streaming chunk for both chat.completions and responses API"""
    content: Optional[str] = None
    role: Optional[str] = None
    finish_reason: Optional[str] = None
    event_type: Optional[str] = None


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

    def __init__(self, profile=None, chat_log_id=None, model=None, system_message=None):
        now = time.strftime("%Y%m%d", time.localtime())
        self.profile = profile or DEFAULT_PROFILE
        self.api_server_type = get_env(self.profile, "api_server_type")
        
        if not self.api_server_type:
            raise ValueError(f"Profile '{self.profile}' is not configured. Please run 'occ configure -p {self.profile}' first.")
        
        self.limit_history = int(get_env(self.profile, "limit_history") or 4)
        self.chat_log_id = chat_log_id or DEFAULT_CHAT_LOG_ID
        self.folder_path = os.path.join(get_home_path(), ".occ", self.profile)
        self.image_folder_path = os.path.join(self.folder_path, "images")
        self.file_name = os.path.join(self.folder_path, f"{self.chat_log_id}.log")
        os.makedirs(self.folder_path, exist_ok=True)
        os.makedirs(self.image_folder_path, exist_ok=True)
        self.model = model
        self.current_model_config = None
        
        if not os.path.exists(self.file_name):
            open(self.file_name, 'w').close()
        self.history_path = Path(self.folder_path, self.chat_log_id) / f"md_history_{now}.md"
        # Load messages and filter out invalid ones (with null role)
        self.messages = []
        for line in open(self.file_name):
            line = line.strip()
            if line:
                try:
                    msg = json.loads(line)
                    # Ensure role is valid
                    if msg.get('role') in ['system', 'assistant', 'user', 'function', 'tool', 'developer']:
                        self.messages.append(msg)
                except json.JSONDecodeError:
                    continue
        
        # Add system message if provided
        if system_message:
            # Check if there's already a system message at the beginning
            has_system = len(self.messages) > 0 and self.messages[0].get('role') == 'system'
            if has_system:
                # Replace existing system message
                self.messages[0] = {"role": "system", "content": system_message}
            else:
                # Insert system message at the beginning
                self.messages.insert(0, {"role": "system", "content": system_message})
        
        # Initialize client based on API server type
        if self.api_server_type == "azure-openai":
            # For Azure OpenAI, we'll initialize client per model in chat method
            self.client = None
        elif self.api_server_type == "openai":
            self.api_key = get_env(self.profile, "api_key")
            self.api_base = get_env(self.profile, "api_base_url")
            
            if not self.api_key:
                raise ValueError(f"API key not configured for profile '{self.profile}'. Please run 'occ configure -p {self.profile}' first.")
            
            os.environ.setdefault("OPENAI_API_KEY", self.api_key)
            os.environ.setdefault("OPENAI_BASE_URL", self.api_base)
            self.client = OpenAI()
        else:
            # Fallback for legacy "azure" type
            self.api_key = get_env(self.profile, "api_key")
            self.api_base = get_env(self.profile, "api_base_url")
            
            if not self.api_key:
                raise ValueError(f"API key not configured for profile '{self.profile}'. Please run 'occ configure -p {self.profile}' first.")
            
            os.environ.setdefault("OPENAI_API_KEY", self.api_key)
            os.environ.setdefault("OPENAI_BASE_URL", self.api_base)
            if "azure" == self.api_server_type:
                self.client = AzureOpenAI(api_key=self.api_key,
                                          api_version=get_env(self.profile, "api_version"),
                                          azure_endpoint=self.api_base)
            else:
                self.client = OpenAI()
    
    def _get_azure_client(self, model):
        """Get Azure OpenAI client for a specific model"""
        from occ.commons.config import get_model_config
        
        model_config = get_model_config(self.profile, model)
        if not model_config:
            raise ValueError(f"Model '{model}' not found in profile '{self.profile}'")
        
        self.current_model_config = model_config
        return AzureOpenAI(
            api_key=model_config['api_key'],
            api_version=model_config['api_version'],
            azure_endpoint=model_config['api_base_url']
        )
    
    def _is_completions_model(self, model):
        """Check if model uses completions API instead of chat completions API"""
        # Azure OpenAI behavior is different from standard OpenAI
        # For Azure, most models (including codex) use chat completions API
        if self.api_server_type in ["azure-openai", "azure"]:
            # Only specific instruct models use completions API in Azure
            azure_completions_models = [
                'gpt-35-turbo-instruct',
                'text-davinci-003',
                'text-davinci-002',
            ]
            return model in azure_completions_models
        
        # For standard OpenAI
        completions_models = [
            'gpt-35-turbo-instruct',
            'text-davinci-003',
            'text-davinci-002',
            'text-curie-001',
            'text-babbage-001',
            'text-ada-001',
        ]
        
        # Check exact match
        if model in completions_models:
            return True
        
        # Check if model contains 'instruct' or 'davinci' (but not codex for standard OpenAI)
        # Note: Codex models behavior varies, so we only check by keyword for OpenAI
        model_lower = model.lower()
        if any(keyword in model_lower for keyword in ['instruct', 'davinci']):
            return True
        
        return False

    def image_create(self, description, size, num):
        raise NotImplementedError

    def chat(self, message, model):
        # Initialize Azure client if needed
        if self.api_server_type == "azure-openai":
            self.client = self._get_azure_client(model)
        
        print_formatted_text(HTML(f"<{ASSISTANT_COLOR}>🤖 Assistant: </{ASSISTANT_COLOR}>"))
        
        # Check if model requires completions API instead of chat completions
        # Models like gpt-35-turbo-instruct, text-davinci-003, codex variants use completions API
        if self._is_completions_model(model):
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
        # Reset role for this chat session
        self.role = None
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
        # Ensure role is always set (default to 'assistant' if not returned by model)
        response_role = self.role if self.role else "assistant"
        self.record_chat_logs(message, {"role": response_role, "content": final_text.replace("\n\n", "")})

    async def async_stream(self) -> AsyncGenerator[StreamChunk, None]:
        """
        Unified streaming generator that returns StreamChunk objects.
        Handles both responses API (o1, codex) and chat.completions API (gpt-4, etc.)
        """
        # Detect which API to use
        model_lower = self.model.lower()
        use_responses_api = (
            self.model.startswith('o1-') or 
            self.model.startswith('o1') or
            'codex' in model_lower
        )
        
        if use_responses_api:
            # Use responses API for o1 and codex models
            response = self.client.responses.create(
                model=self.model,
                input=self.messages,
                stream=True
            )
            
            # Handle responses API streaming with event types
            for event in response:
                if hasattr(event, "type"):
                    match event.type:
                        case "response.output_text.delta":
                            # Incremental text output
                            yield StreamChunk(
                                content=event.delta,
                                event_type=event.type
                            )
                            await asyncio.sleep(0.01)
                        
                        case "response.output_text.done":
                            # Text output completed
                            yield StreamChunk(
                                finish_reason="stop",
                                event_type=event.type
                            )
                        
                        case "response.output_item.done":
                            # Item completed - only extract role if status is completed
                            if hasattr(event, "item"):
                                if hasattr(event.item, "status") and event.item.status == 'completed':
                                    # Only get role when status is completed
                                    if hasattr(event.item, "role"):
                                        yield StreamChunk(
                                            role=event.item.role,
                                            finish_reason="completed",
                                            event_type=event.type
                                        )
                                    else:
                                        yield StreamChunk(
                                            finish_reason="completed",
                                            event_type=event.type
                                        )
                        
                        case _:
                            # Other event types, just pass through
                            pass
        else:
            # Use chat.completions API for regular models
            params = {
                'model': self.model,
                'messages': self.messages,
                'temperature': 1,
                'top_p': 1,
                'frequency_penalty': 0.0,
                'stream': True
            }
            
            response = self.client.chat.completions.create(**params)
            
            for chunk in response:
                if chunk.choices is None or len(chunk.choices) == 0:
                    continue
                    
                choice = chunk.choices[0]
                delta = choice.delta
                
                # Convert to unified StreamChunk format
                yield StreamChunk(
                    content=delta.content if hasattr(delta, 'content') else None,
                    role=delta.role if hasattr(delta, 'role') else None,
                    finish_reason=choice.finish_reason
                )
                await asyncio.sleep(0.01)

    async def print_streaming(self, async_stream):
        self.partial_text = []
        text_area = TextArea(
            text="",
            wrap_lines=True,
            read_only=True,
        )
        app = Application(layout=Layout(HSplit([text_area])), full_screen=False)

        async def producer():
            """
            Process streaming chunks from either API in a unified way.
            Handles StreamChunk objects regardless of source API.
            """
            try:
                async for chunk in async_stream():
                    # Handle finish conditions
                    if chunk.finish_reason in ("stop", "completed"):
                        # Extract role before finishing (for responses API)
                        if chunk.role and self.role is None:
                            self.role = chunk.role
                        break
                    
                    # Extract role if provided (usually first chunk for chat.completions)
                    if chunk.role and self.role is None:
                        self.role = chunk.role
                    
                    # Append content if available
                    if chunk.content:
                        self.partial_text.append(chunk.content)
                        joined = "".join(self.partial_text)
                        text_area.text = joined
                        text_area.buffer.cursor_position = len(text_area.buffer.text)
                        app.invalidate()
                
                # Clear text area and exit
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

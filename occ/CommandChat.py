import json
import openai
from openai import OpenAI
from openai import AzureOpenAI
import os

from occ.commons.config import get_env
from occ.utils.CommonUtil import save_and_copy_image, waiting_start, waiting_stop

DEFAULT_CHAT_LOG_ID = "chat-1"
DEFAULT_PROFILE = "default"


def get_home_path():
    homedir = os.environ.get('HOME', None)
    if os.name == 'nt':
        homedir = os.path.expanduser('~')
    return homedir


class CommandChat:

    def __init__(self, profile=None, chat_log_id=None):
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
        if not os.path.exists(self.file_name):
            open(self.file_name, 'w').close()
        self.messages = [json.loads(line) for line in (line.strip() for line in open(self.file_name)) if line.strip()]
        if "azure" == get_env(profile or DEFAULT_PROFILE, "api_server_type"):
            self.client = AzureOpenAI(api_key=self.api_key,
                                      api_version=get_env(profile or DEFAULT_PROFILE, "api_version"),
                                      azure_endpoint=self.api_base)
        else:
            self.client = OpenAI()

    def image_create(self, description, size, num):
        try:
            response = self.client.Image.create(
                prompt=description,
                n=num,
                size=size
            )
            for index in range(num):
                image_url = response['data'][index]['url']
                save_and_copy_image(image_url, self.image_folder_path)
        except openai.error.OpenAIError as e:
            print(e.http_status)
            print(e.error)

    def image_create_variation(self, img_file, size):
        openai.api_key = self.api_key
        openai.api_base = self.api_base
        try:
            response = openai.Image.create_variation(
                open(img_file, "rb"),
                n=1,
                size=size
            )
            save_and_copy_image(response['data'][0]['url'], self.image_folder_path)
        except openai.error.OpenAIError as e:
            print(e.http_status)
            print(e.error)

    def completions(self, message, model):
        waiting_start()
        stream = self.client.completions.create(
            model=model,
            prompt=message,
            max_tokens=4090 - len(message),
            temperature=0.1,
            stream=True
        )
        waiting_stop()
        for completion in stream:
            for choice in completion.choices:
                print(choice.text, end="")

        print("\n")

    def chat(self, message, model):
        if model == "gpt-35-turbo-instruct":
            self.completions(message, model)
        else:
            self.chat_completions(message, model)

    def chat_completions(self, message, model):
        openai.api_key = self.api_key
        openai.api_base = self.api_base
        message = {"role": "user", "content": message}
        self.messages.append(message)
        waiting_start()
        response = self.client.chat.completions.create(
            model=model,
            messages=self.messages,
            temperature=1,
            top_p=1,
            frequency_penalty=0.0,
            stream=True
        )
        waiting_stop()
        completion_text = ''
        role = None
        for chunk in response:
            if chunk.choices is None or len(chunk.choices) == 0:
                continue
            choice = chunk.choices[0]
            delta = choice.delta

            if choice.finish_reason == "stop":
                break

            if role is None and delta.role:
                role = delta.role

            if delta.content:
                completion_text += delta.content
                print(delta.content, end="")
        print("\n")
        self.record_chat_logs(message, {"role": role, "content": completion_text.replace("\n\n", "")})

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


if __name__ == '__main__':
    command_chat = CommandChat()
    command_chat.chat("帮我写一个python的冒泡排序算法", "gpt-35-turbo-instruct")

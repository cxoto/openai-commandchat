
import json
from commons.config import get_env
import openai
import os

from utils.CommonUtil import save_and_copy_image, waiting_start, waiting_stop


def get_home_path():
    homedir = os.environ.get('HOME', None)
    if os.name == 'nt':
        homedir = os.path.expanduser('~')
    return homedir

class CommandChat:

    DEFAULT_PROFILE = "default"
    DEFAULT_CHAT_LOG_ID = "chat-1"

    def __init__(self, profile=None, chat_log_id=None):
        self.api_key = get_env(profile or self.DEFAULT_PROFILE, "api_key")
        self.limit_history = int(get_env(profile or self.DEFAULT_PROFILE, "limit_history") or 4)
        self.chat_log_id = chat_log_id or self.DEFAULT_CHAT_LOG_ID
        self.folder_path = os.path.join(get_home_path(), ".occ", profile or self.DEFAULT_PROFILE)
        self.image_folder_path = os.path.join(self.folder_path, "images")
        self.file_name = os.path.join(self.folder_path, f"{self.chat_log_id}.log")
        os.makedirs(self.folder_path, exist_ok=True)
        os.makedirs(self.image_folder_path, exist_ok=True)
        if not os.path.exists(self.file_name):
            open(self.file_name, 'w').close()
        self.messages = [json.loads(line) for line in (line.strip() for line in open(self.file_name)) if line.strip()]
    
    def image_create(self, description, size, num):
        openai.api_key = self.api_key
        try:
            response = openai.Image.create(
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

    def chat(self, message):
        openai.api_key = self.api_key
        message = {"role": "user", "content": message}
        self.messages.append(message)
        waiting_start()
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=self.messages,
            temperature=0.2,
            max_tokens=2048,
            top_p=1,
            frequency_penalty=0.0,
            presence_penalty=0.6,
            stream=True
        )
        waiting_stop()   
        completion_text = ''
        content = ''
        role = None
        for event in response:
            if event['choices'][0]["finish_reason"] == "stop":
                break
            if role is None:
                try:
                    role = event['choices'][0]["delta"]["role"]
                except Exception:
                    content = event['choices'][0]["delta"]["content"]
            else:
                content = event['choices'][0]["delta"]["content"]
            completion_text += content
            print(content, end="")
        print("\n")
        self.record_chat_logs(message, {"role": role, "content": completion_text.replace("\n\n", "")})

    def record_chat_logs(self, content, completion_text):
        with open(self.file_name, 'r+') as f:
            lines = f.readlines()
            if len(lines) >= self.limit_history:
                with open(os.path.join(self.folder_path, self.chat_log_id + '_history.log'), 'a+') as hf:
                    hf.writelines(lines[:(self.limit_history)])
                lines = lines[(self.limit_history):]
            lines.append('\n{}\n{}'.format(json.dumps(content, ensure_ascii=False), json.dumps(completion_text, ensure_ascii=False)))
            f.seek(0)
            f.truncate()
            f.writelines(lines)


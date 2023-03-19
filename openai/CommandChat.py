
import json
from commons.config import get_env
import openai
import os


class CommandChat:

    def __init__(self, profile=None, chat_log_id=None):
        profile = profile if profile != None else "default"
        self.api_key = get_env(profile, "api_key")
        self.chat_log_id = chat_log_id if chat_log_id != None else "chat-1"
        self.file_name = self.chat_log_id + '.log'
        self.messages = []
        if not os.path.exists(self.file_name):
            with open(self.file_name, 'w') as f:
                pass
        with open(self.file_name, 'r') as f:
            lines = filter(lambda x: x.strip(), f)
            self.messages = [json.loads(line) for line in map(str.strip, lines)]
    
    def run(self, message):
        openai.api_key = self.api_key
        message = {"role": "user", "content": message}
        self.messages.append(message)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=self.messages,
            temperature=0.1,
            max_tokens=2048,
            top_p=1,
            frequency_penalty=0.0,
            presence_penalty=0.6,
            stream=True
        )

        collected_events = []
        completion_text = ''
        content = ''
        role = ''
        for event in response:
            collected_events.append(event)
            if event['choices'][0]["finish_reason"] == "stop":
                break
            try:
                role = event['choices'][0]["delta"]["role"]
            except Exception:
                content = event['choices'][0]["delta"]["content"]
            completion_text += content
            print(content.replace("\n", ""), end="")
        self.record_chat_logs(
            message, {"role": role, "content": completion_text.replace("\n\n", "")})

    def read_last_lines(self, lines):
        with open(self.chat_log_id, 'r') as f:
            last_lines = f.readlines()[-lines:]
        return ''.join(last_lines)

    def record_chat_logs(self, content, completion_text):
        file_name = self.file_name

        with open(file_name, 'r+') as f:
            lines = f.readlines()
            if len(lines) >= 6:
                with open(self.chat_log_id+'_history.log', 'a+') as hf:
                    hf.write(lines[0])
                lines = lines[1:]
            lines.append('\n{}\n{}'.format(json.dumps(content, ensure_ascii=False),  json.dumps(completion_text, ensure_ascii=False)))
            f.seek(0)
            f.truncate()
            f.writelines(lines)


if __name__ == '__main__':
    CommandChat(profile=None, chat_log_id=None).run("我的上一个问题是啥")

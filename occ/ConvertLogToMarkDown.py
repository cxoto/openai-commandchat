import json
import os

from occ.CommandChat import get_home_path, DEFAULT_CHAT_LOG_ID, DEFAULT_PROFILE


class Converter:
    def __init__(self, profile=None, chat_log_id=None):
        self.chat_log_id = chat_log_id or DEFAULT_CHAT_LOG_ID
        self.folder_path = os.path.join(get_home_path(), ".occ", profile or DEFAULT_PROFILE)
        self.file_name = os.path.join(self.folder_path, self.chat_log_id + '_history.log')

    def convert(self):
        # 读取log文件
        with open(self.file_name, 'r') as file:
            log_data = file.readlines()

        # 创建MD文档
        with open('output.md', 'w') as file:
            for line in log_data:
                # 解析JSON数据
                data = json.loads(line)
                role = data['role']
                content = data['content']

                # 根据role写入不同的内容到MD文档
                if role == 'user':
                    file.write('# ' + content + '\n')
                elif role == 'assistant':
                    file.write(content + '\n')


if __name__ == '__main__':
    Converter().convert()

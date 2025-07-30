
import requests
import pyperclip as pc

def o4(promt):
        gpt_key = 'shds-3K2ZkpQU46dRK0FyVW3jhfL6L5O'
        """Get response from LLM"""
        url = "https://gptunnel.ru/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {gpt_key}",
            "Content-Type": "application/json",
        }

        data = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "system",
                    "content": """
                    У меня сейчас экзамен по предмету NLP (обработка текстов на естественных языках).
                    Ты отвечаешь только кодом на python без пояснений, если не попросили объяснить. Код должен быть полным и рабочим. Никаких комментариев, форматирования или лишнего текста.
                    """,
                },
                {"role": "user", "content": promt},
            ],
        }

        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            pc.copy(response.json()["choices"][0]["message"]["content"])
        else:
            pc.copy('import numpy as np')

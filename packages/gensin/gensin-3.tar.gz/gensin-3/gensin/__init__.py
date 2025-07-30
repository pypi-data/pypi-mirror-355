
import requests
import pyperclip as pc

def o3(promt):
        gpt_key = 'shds-3K2ZkpQU46dRK0FyVW3jhfL6L5O'
        """Get response from LLM"""
        url = "https://gptunnel.ru/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {gpt_key}",
            "Content-Type": "application/json",
        }

        data = {
            "model": "o3",
            "messages": [
                {
                    "role": "system",
                    "content": """
                        У меня сейчас экзамен. 
                        Пиши только код целиком без пояснений и коментариев.
                        НИЧЕГО КРОМЕ КОДА НЕ КИДАЙ!!! 
                        '```python' - вот такое не вставляй (нужен только сам код)
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

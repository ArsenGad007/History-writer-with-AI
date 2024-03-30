import requests
from config import MAX_TOKENS_IN_TASK, MAX_TOKENS_IN_ANSWER, TEMPERATURE, IAM_TOKEN, FOLDER_ID
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename="log_file.txt",
    filemode="a",
)


def create_new_token():
    """Создание нового токена"""
    metadata_url = "http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token"
    headers = {"Metadata-Flavor": "Google"}
    response = requests.get(metadata_url, headers=headers)
    return response.json()


def count_tokens(text: str, folder_id: str, iam_token: str):
    """
    Функция считает количество токенов в тексте
    :param iam_token:
    :param folder_id:
    :param text:
    :return: Число токенов в тексте
    """
    headers = {
        'Authorization': f'Bearer {iam_token}',
        'Content-Type': 'application/json'
    }
    data = {
        "modelUri": f"gpt://{folder_id}/yandexgpt-lite",
        "text": text
    }
    response = requests.post("https://llm.api.cloud.yandex.net/foundationModels/v1/tokenize", headers=headers,
                             json=data)
    tokenizer = response.json()["tokens"]
    return len(tokenizer)


def answer_gpt(UserMessage: str, UserId: int, UserName: str, db: object.__class__):
    """
    Функция отправляет запрос к нейросети и получает ответ от неё
    :param UserMessage:
    :param UserId:
    :param UserName:
    :param db:
    :return: Ответ от нейросети
    """

    if count_tokens(UserMessage, FOLDER_ID, IAM_TOKEN) > MAX_TOKENS_IN_TASK:
        logging.error(f"{UserName}: Промт слишком длинный")
        return "Задача слишком длинная :(. Переформулируйте запрос"

    elif UserMessage.lower() == "end":
        db.update_data(UserId, 'user_content', f"{UserMessage} Закончи историю", 'Users')
    elif UserMessage.lower() == "продолжить" or UserMessage.lower() == "continue":
        db.update_data(UserId, 'user_content', f"{UserMessage} Продолжи историю", 'Users')
    else:
        # Записываем данные в таблицу
        db.update_data(UserId, 'task', UserMessage, 'Users')
        db.update_data(UserId, 'answers', " ", 'Users')
        db.update_data(UserId, 'user_content', f"Напиши начало истории в жанре "
                                               f"{db.select_data(UserId, 'genre', 'Users')}, в роли главного "
                                               f"героя: {db.select_data(UserId, 'character', 'Users')}. Также "
                                               f"пользователь просит учесть эту дополнительную информацию: "
                                               f"{db.select_data(UserId, 'info', 'Users')}. Не давай никакие "
                                               f"подсказки пользователю от себя.", 'Users')

    try:
        logging.info(f"{UserName}: Генерация промта")
        # Отправляем Post запрос
        iam_token = IAM_TOKEN
        folder_id = FOLDER_ID  # Folder_id для доступа к YandexGPT

        headers = {
            'Authorization': f'Bearer {iam_token}',
            'Content-Type': 'application/json'
        }
        data = {
            "modelUri": f"gpt://{folder_id}/yandexgpt-lite",  # модель для генерации текста
            "completionOptions": {
                "stream": False,  # потоковая передача частично сгенерированного текста выключена
                "temperature": TEMPERATURE,
                # чем выше значение этого параметра, тем более креативными будут ответы модели (0-1)
                "maxTokens": MAX_TOKENS_IN_ANSWER
                # максимальное число сгенерированных токенов, очень важный параметр для экономии токенов
            },
            "messages": [
                {
                    "role": "system",
                    "text": "Ты бот сценарист. Напиши сценарий."
                },
                {
                    "role": "assistant",
                    "text": db.select_data(UserId, 'answers', 'Users')
                },
                {
                    "role": "user",
                    "text": db.select_data(UserId, 'user_content', 'Users')
                }
            ]
        }
        # Выполняем запрос к YandexGPT
        response = requests.post("https://llm.api.cloud.yandex.net/foundationModels/v1/completion", headers=headers,
                                 json=data)
    except:
        logging.error(f"{UserName}: Сервер не отвечает")
        return "Сервер не отвечает"

    try:
        # Извлечение ответа GPT
        db.update_data(UserId, 'gpt_response', response.json()["result"]["alternatives"][0]["message"]["text"], 'Users')
    except:
        logging.error(f"{UserName}: Не удалось получить ответ от нейросети")
        return "Не удалось получить ответ от нейросети"

    # Сохраняем ответы GPT и записываем данные в таблицу
    db.update_data(UserId, 'answers', f"{db.select_data(UserId, 'answers', 'Users')} "
                                      f"{db.select_data(UserId, 'gpt_response', 'Users')}", 'Users')

    logging.info(f"{UserName}: Генерация промта завершена")

    # Печать ответа GPT
    return db.select_data(UserId, 'gpt_response', 'Users')

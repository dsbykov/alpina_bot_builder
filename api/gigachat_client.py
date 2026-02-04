import os
import logging

from gigachat import GigaChatAsyncClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

client = GigaChatAsyncClient(credentials=os.getenv("GIGACHAT_AUTH_KEY"),
                             verify_ssl_certs=False)
logger.debug(f"Создан клиент GigaChat")


async def get_gigachat_response_async(prompt: str) -> str:
    try:
        response = await client.achat(prompt)
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"!Ошибка GigaChat: {str(e)}")
        return "Кажется проблема интеграции с GigaChat. \
            Повторите попытку озже."

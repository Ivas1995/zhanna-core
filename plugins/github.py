import httpx
import asyncio
import logging
import os
from config import BASE_DIR, GITHUB_TOKEN, ENCRYPTION_KEY
from security import decrypt_data
from database import save_interaction
from utils.notify_user import notify_user

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(BASE_DIR, "sakura.log"), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def github_action(action, user_id, repo_name=None, content=None, path=None):
    """Дії з GitHub: список репозиторіїв, створення, оновлення коду."""
    headers = {
        "Authorization": f"Bearer {decrypt_data(GITHUB_TOKEN, ENCRYPTION_KEY)}",
        "Accept": "application/vnd.github+json"
    }
    try:
        async with httpx.AsyncClient() as client:
            if action == "list":
                response = await client.get("https://api.github.com/user/repos", headers=headers, timeout=10)
                if response.status_code == 200:
                    repos = [repo["name"] for repo in response.json()]
                    result = f"Репозиторії: {', '.join(repos)}"
                    await notify_user(user_id, result)
                    await save_interaction(user_id, "github_list", result)
                    return result
                return "Помилка отримання репозиторіїв"
            elif action == "create":
                if not repo_name:
                    return "Вкажіть назву репозиторію!"
                data = {"name": repo_name, "private": False}
                response = await client.post("https://api.github.com/user/repos", headers=headers, json=data, timeout=10)
                if response.status_code == 201:
                    result = f"Репозиторій {repo_name} створено"
                    await notify_user(user_id, result)
                    await save_interaction(user_id, "github_create", result)
                    return result
                return "Помилка створення репозиторію"
            elif action == "update":
                if not repo_name or not content or not path:
                    return "Вкажіть репозиторій, шлях і вміст!"
                # Отримання SHA поточного файлу (якщо існує)
                sha_url = f"https://api.github.com/repos/{user_id}/{repo_name}/contents/{path}"
                sha_response = await client.get(sha_url, headers=headers, timeout=10)
                sha = sha_response.json().get("sha") if sha_response.status_code == 200 else None
                data = {
                    "message": f"Update {path} by Sakura AI",
                    "content": base64.b64encode(content.encode()).decode(),
                    "sha": sha
                }
                response = await client.put(sha_url, headers=headers, json=data, timeout=10)
                if response.status_code in (200, 201):
                    result = f"Файл {path} оновлено в {repo_name}"
                    await notify_user(user_id, result)
                    await save_interaction(user_id, "github_update", result)
                    return result
                return "Помилка оновлення файлу"
    except Exception as e:
        logger.error(f"GitHub action error: {str(e)}")
        from plugins.self_improvement import handle_error
        await handle_error(str(e))
        return f"Помилка: {str(e)}"
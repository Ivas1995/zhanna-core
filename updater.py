import requests
from config import XAI_API_KEY
from database import save_interaction
from security import decrypt_data

def update_knowledge():
    try:
        headers = {"Authorization": f"Bearer {decrypt_data(XAI_API_KEY)}"}
        response = requests.post(
            "https://api.x.ai/v1/",
            json={"prompt": "Update knowledge on cryptocurrency trading strategies for Binance Futures", "max_tokens": 300},
            headers=headers
        )
        new_data = response.json().get("response", "Error")
        save_interaction("system", "Update trading knowledge", new_data)
        return "Knowledge updated!"
    except Exception as e:
        return f"Error updating knowledge: {str(e)}"

if __name__ == "__main__":
    print(update_knowledge())
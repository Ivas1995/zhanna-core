from gpt4all import GPT4All
try:
    model = GPT4All("mistral-7b-openorca.Q4_0.gguf")
    print("Модель завантажено успішно!")
except Exception as e:
    print(f"Помилка: {str(e)}")
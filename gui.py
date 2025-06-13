import tkinter as tk
from tkinter import scrolledtext, ttk
import threading
import asyncio
import os
import plotly
import json
from config import BASE_DIR
from audio_manager import recognize_speech, speak
from main import process_command
from utils.network import is_online
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(BASE_DIR, "sakura.log"), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SakuraGUI:
    def __init__(self, model):
        self.model = model
        self.root = tk.Tk()
        self.root.title("SAKURA: JARVIS AI")
        self.root.geometry("1000x600")
        self.root.configure(bg="#0a0f1a")

        self.style = ttk.Style()
        self.style.configure("Custom.TButton", padding=10, font=("Helvetica", 12, "bold"), background="#00ff00", foreground="#ffffff")
        self.style.configure("Custom.TLabel", background="#0a0f1a", foreground="#00ccff", font=("Arial", 14, "bold"))

        self.online_status = ttk.Label(self.root, text="Offline", style="Custom.TLabel", foreground="red")
        self.online_status.pack(pady=5)

        self.main_frame = ttk.Frame(self.root, style="Custom.TFrame")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.chat_area = scrolledtext.ScrolledText(
            self.main_frame, wrap=tk.WORD, height=15, bg="#1c2526", fg="#00ccff", font=("Helvetica", 12),
            insertbackground="#00ff00", cursor="arrow"
        )
        self.chat_area.grid(row=0, column=0, columnspan=2, sticky="nsew", pady=5)
        self.chat_area.config(state="disabled")

        self.market_frame = ttk.LabelFrame(self.main_frame, text="Market Data", padding=10, style="Custom.TLabel")
        self.market_frame.grid(row=0, column=2, sticky="nsew", padx=5)
        self.market_label = ttk.Label(self.market_frame, text="No Data", style="Custom.TLabel", wraplength=200)
        self.market_label.pack(pady=5)

        self.input_frame = ttk.Frame(self.main_frame, style="Custom.TFrame")
        self.input_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=5)

        self.input_entry = ttk.Entry(self.input_frame, font=("Helvetica", 12), background="#1c2526", foreground="#00ccff")
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.input_entry.bind("<Return>", self.send_command)

        self.send_button = ttk.Button(self.input_frame, text="Send", style="Custom.TButton", command=self.send_command)
        self.send_button.pack(side=tk.LEFT, padx=5)

        self.voice_button = ttk.Button(self.input_frame, text="Voice", style="Custom.TButton", command=self.start_voice)
        self.voice_button.pack(side=tk.LEFT, padx=5)

        self.scan_button = ttk.Button(self.input_frame, text="Scan", style="Custom.TButton", command=self.scan_system)
        self.scan_button.pack(side=tk.LEFT, padx=5)

        self.trades_button = ttk.Button(self.input_frame, text="Trades", style="Custom.TButton", command=self.analyze_trades)
        self.trades_button.pack(side=tk.LEFT, padx=5)

        self.music_button = ttk.Button(self.input_frame, text="Music", style="Custom.TButton", command=self.play_music)
        self.music_button.pack(side=tk.LEFT, padx=5)

        self.main_frame.columnconfigure(0, weight=3)
        self.main_frame.rowconfigure(0, weight=1)

        self.loop = asyncio.get_event_loop()
        self.loop.create_task(self.update_online_status())
        self.loop.create_task(self.update_market_data())
        self.add_jarvis_effect()
        threading.Thread(target=self.run_asyncio_loop, daemon=True).start()

    def run_asyncio_loop(self):
        """Запуск асинхронного циклу."""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def add_jarvis_effect(self):
        """Голографічний ефект JARVIS."""
        self.root.after(500, self.pulse_effect)

    def pulse_effect(self):
        """Пульсуючий ефект для кнопок."""
        colors = ["#00ff00", "#00cc00"]
        current_color = self.send_button.cget("background")
        next_color = colors[0] if current_color == colors[1] else colors[1]
        for btn in [self.send_button, self.voice_button, self.scan_button, self.trades_button, self.music_button]:
            btn.configure(background=next_color)
        self.root.after(500, self.pulse_effect)

    async def update_online_status(self):
        """Оновлення статусу мережі."""
        if await is_online():
            self.online_status.config(text="Online", foreground="#00ff00")
        else:
            self.online_status.config(text="Offline", foreground="#ff0000")
        self.root.after(10000, lambda: self.loop.create_task(self.update_online_status()))

    async def update_market_data(self):
        """Оновлення ринкових даних з графіком."""
        from crypto_trader import analyze_market
        try:
            data = await analyze_market(None, "gui_user", testnet=True)
            self.market_label.config(text=data[:200] + "...")
            # Генерація графіку через Plotly
            fig = plotly.graph_objs.Figure()
            fig.add_trace(plotly.graph_objs.Scatter(x=[datetime.now()], y=[float(data.split("Ціна: ")[1].split(" ")[0])], mode='lines', name='Price'))
            with open(os.path.join(BASE_DIR, "static", "market_plot.html"), "w") as f:
                f.write(fig.to_html())
        except Exception as e:
            self.market_label.config(text="Data Error")
            logger.error(f"Market data error: {str(e)}")
        self.root.after(60000, lambda: self.loop.create_task(self.update_market_data()))

    def send_command(self, event=None):
        """Відправка текстової команди."""
        command = self.input_entry.get()
        if command:
            self.add_message(f"User: {command}")
            self.input_entry.delete(0, tk.END)
            threading.Thread(target=self.process_command_async, args=(command,), daemon=True).start()

    def start_voice(self):
        """Запуск голосового вводу."""
        threading.Thread(target=self.process_voice_async, daemon=True).start()

    def scan_system(self):
        """Сканування системи."""
        threading.Thread(target=self.process_scan_async, daemon=True).start()

    def analyze_trades(self):
        """Аналіз угод."""
        threading.Thread(target=self.process_trades_async, daemon=True).start()

    def play_music(self):
        """Відтворення музики."""
        threading.Thread(target=self.process_music_async, daemon=True).start()

    def add_message(self, message):
        """Додавання повідомлення в чат."""
        self.chat_area.config(state="normal")
        self.chat_area.insert(tk.END, message + "\n")
        self.chat_area.config(state="disabled")
        self.chat_area.see(tk.END)

    def process_command_async(self, command):
        """Обробка текстової команди."""
        async def process():
            response = await process_command(command, "gui_user", self.model)
            self.add_message(f"Sakura: {response}")
            await speak(response)
        self.loop.create_task(process())

    async def process_voice_async(self):
        """Обробка голосової команди."""
        text = await recognize_speech()
        if text:
            self.add_message(f"User (Voice): {text}")
            response = await process_command(text, "gui_user", self.model)
            self.add_message(f"Sakura: {response}")
            await speak(response)

    async def process_scan_async(self):
        """Сканування системи."""
        from home_control import scan_system
        response = await scan_system("gui_user")
        self.add_message(f"Sakura: {response}")

    async def process_trades_async(self):
        """Аналіз угод."""
        from crypto_trader import analyze_user_trades
        response = await analyze_user_trades("gui_user")
        self.add_message(f"Sakura: {response}")

    async def process_music_async(self):
        """Відтворення музики."""
        from plugins.youtube import play_youtube
        response = await play_youtube(self.input_entry.get() or "relaxing music", "gui_user")
        self.add_message(f"Sakura: {response}")

def start_gui(model=None):
    """Запуск GUI."""
    if not model:
        from gpt4all import GPT4All
        model = GPT4All(MODEL_NAME, model_path=os.path.join(BASE_DIR, "models"), device="cpu", allow_download=False)
    return SakuraGUI(model)
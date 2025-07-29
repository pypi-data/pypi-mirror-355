import asyncio
import os
import socket
import threading
import logging
from telegram import Bot
from tgrad.config import load_config

logger = logging.getLogger("tgrad")
logging.basicConfig(level=logging.INFO)

async def send(bot, chat_id, title, msg):
    await bot.send_message(chat_id=chat_id, text=f"*{title}*\n{msg}", parse_mode='Markdown')

def handle_client(conn, bot, chat_id, loop):
    try:
        with conn:
            data = conn.recv(2048).decode()
            if data:
                title, msg = data.split("\n", 1) if "\n" in data else ("Message", data)
                fut = asyncio.run_coroutine_threadsafe(send(bot, chat_id, title, msg), loop)
                fut.result()  # Wait for it to complete (optional)
    except Exception as e:
        logger.error(f"Client error: {e}")

def main():
    cfg = load_config()
    sock_path = cfg["socket"]
    if os.path.exists(sock_path):
        os.remove(sock_path)

    bot = Bot(token=cfg["token"])
    chat_id = cfg["chat_id"]

    loop = asyncio.new_event_loop()
    threading.Thread(target=loop.run_forever, daemon=True).start()

    logger.info(f"tgrad server listening on {sock_path}")
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server_sock:
        server_sock.bind(sock_path)
        server_sock.listen()

        while True:
            conn, _ = server_sock.accept()
            threading.Thread(target=handle_client, args=(conn, bot, chat_id, loop), daemon=True).start()

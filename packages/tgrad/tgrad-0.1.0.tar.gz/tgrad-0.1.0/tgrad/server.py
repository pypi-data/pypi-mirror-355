import os
import socket
import threading
import logging
from telegram import Bot
from tgrad.config import load_config
import asyncio

logger = logging.getLogger("tgrad")
logging.basicConfig(level=logging.INFO)


async def send(bot, chat_id, title, msg):
    await bot.send_message(
        chat_id=chat_id, text=f"*{title}*\n{msg}", parse_mode="Markdown"
    )


def handle_client(conn, bot, chat_id):
    try:
        with conn:
            data = conn.recv(2048).decode()
            if data:
                lines = data.split("\n", 1)
                title, msg = lines if len(lines) == 2 else ("Message", lines[0])
                asyncio.run(send(bot, chat_id, title, msg))
    except Exception as e:
        logger.error(f"Client error: {e}")


def main():
    cfg = load_config()
    if cfg is None:
        print("Configuration not found. Please run tgrad-config first.")
        return
    sock_path = cfg.get("socket")
    if os.path.exists(sock_path):
        os.remove(sock_path)

    bot = Bot(token=cfg["token"])
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server_sock:
        server_sock.bind(sock_path)
        server_sock.listen()
        logger.info(f"✅ tgrad server listening on {sock_path}")

        while True:
            conn, _ = server_sock.accept()
            threading.Thread(
                target=handle_client, args=(conn, bot, cfg["chat_id"]), daemon=True
            ).start()

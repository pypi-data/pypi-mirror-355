import json
import os
import argparse

CONFIG_PATH = os.path.expanduser("~/.tgrad/config.json")
DEFAULT_SOCKET = os.path.expanduser("~/.tgrad/tgrad.sock")


def load_config():
    if not os.path.exists(CONFIG_PATH):
        return None
    with open(CONFIG_PATH) as f:
        return json.load(f)


def save_config(token, chat_id, socket_path):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump({"token": token, "chat_id": chat_id, "socket": socket_path}, f)


def get_socket_path():
    try:
        return load_config().get("socket", DEFAULT_SOCKET)
    except Exception:
        return DEFAULT_SOCKET


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--token", required=True)
    parser.add_argument("-c", "--chat", required=True)
    parser.add_argument("-s", "--socket", default=DEFAULT_SOCKET)
    args = parser.parse_args()

    save_config(args.token, args.chat, args.socket)
    print("Configuration saved.")

# tgrad 

![Release](https://github.com/tareqmahmood/tgrad/actions/workflows/release.yml/badge.svg) [![PyPI - Version](https://img.shields.io/pypi/v/tgrad)](https://pypi.org/project/tgrad/)

`tgrad` is a minimal, efficient Telegram notification daemon for Linux systems. It allows local programs and scripts to send messages to a Telegram bot via a Unix domain socket. Designed for simplicity and automation, it includes both a command-line interface and a Python API for seamless integration into your workflows. 

Whether you're monitoring system health, tracking long-running jobs, or debugging servers, `tgrad` gives you a simple, secure way to receive instant alerts on your phone — without running your own server, building a mobile app, or paying for third-party services.

> [!NOTE]  
> This is mostly for personal use and with the intention to extend as personal needs evolve. Works for me. Hope it helps you too.

## ⚡ Quick Start

```bash
pip install tgrad
tgrad-config -t <BOT_TOKEN> -c <CHAT_ID>
tgrad-server &
tgrad-client -t "Test" -m "It works!"
```

## ✨ Features

- 🧵 Runs as a background daemon
- 🧾 Message delivery to Telegram via local socket
- ⚙️ Easy CLI tools to configure, run, and send messages
- 🐍 Python API (`tgrad.send()`) for direct integration

## 💪 Use-cases

- ✅ Notify when a long-running script finishes
- 🧠 Alert when memory usage exceeds 90%
- 💾 Warn when disk space drops below 10%
- ⏰ Send alerts from `cron` jobs or custom `ebpf` monitors

## 📦 Installation

```bash
pip install tgrad
```

From latest in Github
```bash
git clone https://github.com/tareqmahmood/tgrad.git
cd tgrad
pip install .
```

## 🔐 Bot Setup

<details>
   <summary>Details on setting up a Telegram bot</summary>
   
   Before using `tgrad`, you need to create a Telegram bot and get the **bot token** and **chat ID**.
   
   ### Step 1: Create a Telegram Bot
   
   1. Open Telegram and search for [`@BotFather`](https://t.me/BotFather).
   
   2. Start the chat and send:
   
      ```
      /newbot
      ```
   
   3. Follow the prompts:
   
      * Set a display name (e.g., `MyNotifierBot`)
      * Choose a unique username ending in `bot` (e.g., `my_notifier_bot`)
   
   4. BotFather will respond with a message containing your bot token:
   
      ```
      Use this token to access the HTTP API:
      123456789:ABCdefGhIJKlmNoPQRstUvWXyZ12345678
      ```
   
      🔑 Save this as your **BOT\_TOKEN**.
   
   ### Step 2: Get Your Chat ID
   
   1. Start a chat with your bot (click the link BotFather gives you).
   
   2. Send a message like `hello` or `/start`.
   
   3. Open this in your browser:
   
      ```
      https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
      ```
   
      Example:
   
      ```
      https://api.telegram.org/bot123456789:ABCdefGhIJKlmNoPQRstUvWXyZ12345678/getUpdates
      ```
   
   4. Look for a JSON field like this in the response:
   
      ```json
      "chat": {
        "id": 987654321,
        "first_name": "Your Name",
        ...
      }
      ```
   
      📩 Use the `id` value as your **CHAT\_ID**.
   
   > For groups: Add the bot to the group, send a message, and check `getUpdates` again. The `chat.id` will be a negative number like `-1001234567890`.
   
   
   Once you have your `BOT_TOKEN` and `CHAT_ID`, configure `tgrad`:
   
   
   ```bash
   tgrad-config -t <BOT_TOKEN> -c <CHAT_ID> [-s ~/.tgrad/tgrad.sock]
   ```
   
   This saves your bot token, chat ID, and socket path to `~/.tgrad/config.json`.
</details>

## 🚀 Usage

### Start the Daemon Server

```bash
tgrad-server
```

It will listen for messages on the configured Unix socket.

### Send a Message via CLI

```bash
tgrad-client -t "Title" -m "Hello from CLI"
```

### Send a Message from Python

```python
import tgrad
tgrad.send("Alert", "Something happened!")
```

## 🛣️ Roadmap

- [x] Send messages from a Linux server to a Telegram bot
- [ ] Bi-directional Telegram interaction (e.g., respond to /status)
- [ ] Accept user-defined Python scripts for trigger actions
- [ ] Event templating and message formatting

## 📄 License

MIT License.

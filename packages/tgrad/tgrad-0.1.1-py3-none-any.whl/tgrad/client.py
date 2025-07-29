import argparse
import socket
from tgrad.config import get_socket_path


def send(title, message):
    data = f"{title}\n{message}".encode()
    sock = get_socket_path()
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.connect(sock)
        s.sendall(data)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--title", required=True)
    parser.add_argument("-m", "--message", required=True)
    args = parser.parse_args()
    send(args.title, args.message)

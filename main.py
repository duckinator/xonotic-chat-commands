#!/usr/bin/env python3

import socket
import toml
import xrcon

class XonoticChatCommands:
    def __init__(self, config_file=None):
        config_file = 'server.toml'
        config = toml.load(config_file)
        self.server_addr = config['server_addr']
        self.server_port = config['server_port']
        self.rcon_password = config['rcon_password']
        self.listen_port = config['listen_port']

    def listen(self):
        # Create a UDP socket.
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Listen on '127.0.0.1:{self.listen_port}'
        self.socket.bind(('127.0.0.1', self.listen_port))

    def main_loop(self):
        while True:
            data, addr = self.socket.recvfrom(1024)  # buffer size is 1024 bytes
            print(f"[MESSAGE/{addr}] {data}")

if __name__ == '__main__':
    XonoticChatCommands().main_loop()

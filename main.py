#!/usr/bin/env python3

from message_buffer import MessageBuffer
import socket
import threading
import toml
from xrcon.client import XRcon

class XonoticChatCommands:
    PREFIX = b"\xff\xff\xff\xffn"

    def __init__(self, server_config_file=None, commands_config_file=None):
        server_config_file = server_config_file or 'server.toml'
        commands_config_file = commands_config_file or 'commands.toml'
        server_config = toml.load(server_config_file)
        commands_config = toml.load(commands_config_file)

        self.commands = commands_config['commands']

        server_addr = server_config['server']['address']
        server_port = server_config['server']['port']
        rcon_password = server_config['server']['rcon_password']

        self.listen_port = server_config['server']['listen_port']
        self.socket = None

        self.rcon = XRcon(server_addr, server_port, rcon_password)
        self.buffer = MessageBuffer()

    def listen(self):
        # Create a UDP socket.
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Listen on '127.0.0.1:{self.listen_port}'
        self.socket.bind(('127.0.0.1', self.listen_port))

    def _main_loop_recv(self):
        if not self.socket:
            self.listen()
        self.rcon.connect()

        while True:
            data, addr = self.socket.recvfrom(1024)  # buffer size is 1024 bytes

            if addr[0] != '127.0.0.1':
                print(f"[ERROR] Got message from unexpected IP: {addr!r}")
                continue

            self.buffer.write(data)

    def main_loop(self):
        self.recv_thread = threading.Thread(target=self._main_loop_recv)
        self.recv_thread.start()
        while True:
            self.handle(self.buffer.readline())

    def handle(self, data):
        if data[0:1] == "\x01":
            self.on_chat(data)
        elif ' ' in data and data.split(' ', 1)[1] == 'connected':
            self.on_player_connect(data)
        #else:
        #    print(f"[UNKNOWN MESSAGE TYPE] {data!r}")


    def on_chat(self, data):
        if ': ' not in data:
            print(f"[MESSAGE] {data}")
            return
        sender, message = data.split(': ', 1)

        if message[0] != '!':
            #print(f"[MESSAGE] {sender}: {message!r}")
            return

        if ' ' in message:
            cmd, args = message.split(' ', 1)
        else:
            cmd = message
            args = ''
        cmd = cmd[1:]

        print(f"[{sender!r}]: {message!r}")
        if cmd in self.commands:
            rcon_command = self.commands[cmd]
        else:
            rcon_command = f"vcall {cmd}"

        rcon_command = rcon_command.format(args=args)
        print(">>", rcon_command)
        response = self.rcon.execute(rcon_command).decode()
        print("=>", repr(response))
        if response:
            # HACK: Bullshit kludge for `!maps`.
            # TODO: Make this less kludgy.
            if response.startswith('^9[::^7SVQC^9::^5INFO^9]'):
                response = '\n'.join(response.split('\n')[1:])

            self.rcon.execute("say " + response)

    def on_player_connect(self, data):
        if data.split(' ', 1)[1] != 'connected':
            return

        if '[BOT]' in data:
            return

        sender = data.split(' ', 1)[0]

        if sender[0] == '^':
            return

        self.rcon.execute(f"say Hello {sender}! This server has commands usable by saying !<command> in chat. See !help for details.")

if __name__ == '__main__':
    XonoticChatCommands().main_loop()

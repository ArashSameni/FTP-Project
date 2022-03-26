import socket
import threading
import os
import pathlib

HOST = "127.0.0.1"
PORT = 65432
MESSAGE_SIZE = 1024
FILES_DIR = str(pathlib.Path(__file__).parent.resolve()) + '/files'
COLORS = {
    "BLACK": "\u001b[30;1m",
    "RED": "\u001b[31;1m",
    "GREEN": "\u001b[32;1m",
    "YELLOW": "\u001b[33;1m",
    "BLUE": "\u001b[34;1m",
    "MAGENTA": "\u001b[35;1m",
    "CYAN": "\u001b[36;1m",
    "WHITE": "\u001b[37;1m",
    "RESET": "\u001b[0m",
}

active_connections = 0
print_lock = threading.Lock()
def print_colorful(short_desc, text, color):
    SPACE_NEEDED = 21
    spaces = ' ' * (SPACE_NEEDED - len(short_desc))

    print_lock.acquire()
    print(COLORS[color] + short_desc + spaces + text + COLORS['RESET'])
    print_lock.release()

class Command():
    LIST = 'ls'
    GET = 'get'
    PUT = 'put'
    PWD = 'pwd'
    MKDIR = 'mkdir'
    RMDIR = 'rmdir'
    CD = 'cd'
    DELETE = 'delete'
    RENAME = 'rename'

    def __init__(self, cmd):
        self.type, self.args = Command.split_command(cmd)

    def split_command(cmd):
        first_space = cmd.find(' ')
        if first_space < 0:
            return cmd, ''
        return cmd[:first_space], cmd[first_space + 1:]


class ClientThread(threading.Thread):
    ENC_TYPE = 'utf-8'

    def __init__(self, conn, addr, *args):
        self.conn = conn
        self.addr = addr
        self.current_directory = ''
        threading.Thread.__init__(self, args=args)

    def run(self):
        print_colorful('[NEW CONNECTION]', f'{self.addr[0]} connected at port {self.addr[1]}', 'YELLOW')

        while True:
            message = self.conn.recv(MESSAGE_SIZE).decode(
                ClientThread.ENC_TYPE)
            if not message:
                break
            print_colorful(f'[{self.addr[0]}:{self.addr[1]}]', f'"{message}"', 'CYAN')

            cmd = Command(message)
            if cmd.type == Command.LIST:
                self.list()
            elif cmd.type == Command.GET:
                self.get()
            elif cmd.type == Command.PUT:
                self.put()
            elif cmd.type == Command.PWD:
                self.pwd()
            elif cmd.type == Command.MKDIR:
                self.mkdir(cmd.args)
            elif cmd.type == Command.RMDIR:
                self.rmdir(cmd.args)
            elif cmd.type == Command.CD:
                self.cd(cmd.args)
            elif cmd.type == Command.DELETE:
                self.delete(cmd.args)
            elif cmd.type == Command.RENAME:
                self.rename()

        self.close_connection()

    def close_connection(self):
        global active_connections
        active_connections -= 1

        print_colorful('[CONNECTION LOST]', f'{self.addr[0]}:{self.addr[1]} disconnected', 'RED')
        print_colorful('[ACTIVE CONNECTIONS]', str(active_connections), 'GREEN')

        self.conn.close()

    def list(self):
        print("list")

    def get(self):
        print("get")

    def put(self):
        print("put")

    def pwd(self):
        self.send(
            f'257 "/{self.current_directory}" is the current directory')

    def mkdir(self, dir_name):
        try:
            os.mkdir(self.absolute_path(dir_name))
            self.send(
                f'257 /{os.path.join(self.current_directory, dir_name)} created')
        except:
            self.send('550 Failed to make directory.')

    def rmdir(self, dir_name):
        try:
            to_remove = self.absolute_path(dir_name)
            if not to_remove.startswith(FILES_DIR):
                raise Exception()

            os.rmdir(to_remove)
            self.send(
                f'250 Remove directory operation successful.')
        except:
            self.send('550 Remove directory operation failed.')

    def cd(self, dir_path):
        new_path = self.absolute_path(dir_path)
        if not os.path.isdir(new_path) or not new_path.startswith(FILES_DIR):
            self.send('550 Failed to change directory.')
            return

        self.current_directory = os.path.normpath(
            os.path.join(self.current_directory, dir_path))
        if self.current_directory == '.':
            self.current_directory = ''

        self.send('250 Directory successfully changed.')

    def delete(self, file_name):
        try:
            to_remove = self.absolute_path(file_name)
            if not to_remove.startswith(FILES_DIR):
                raise Exception()

            os.remove(to_remove)
            self.send(
                f'250 Delete operation successful.')
        except:
            self.send('550 Delete operation failed.')

    def rename(self):
        print("rename")

    def absolute_path(self, joining_path):
        return os.path.normpath(os.path.join(FILES_DIR, self.current_directory, joining_path))

    def send(self, message):
        self.conn.sendall(message.encode(ClientThread.ENC_TYPE))


def handle_incoming_requests(socket):
    global active_connections

    while True:
        conn, addr = socket.accept()
        ClientThread(conn, addr).start()

        active_connections += 1
        print_colorful('[ACTIVE CONNECTIONS]', str(active_connections), 'GREEN')


def main():
    print_colorful('[STARTING SERVER]', 'Starting server...', 'YELLOW')
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print_colorful('[SERVER STARTED]', f'Server is listening on {HOST}:{PORT}', 'GREEN')

    handle_incoming_requests(server_socket)


if __name__ == '__main__':
    main()

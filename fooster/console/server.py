import functools
import inspect
import shlex
import socket
import socketserver
import threading

import paramiko

from . import commands
from . import defaults
from . import exception


__all__ = ['ConsoleHandler', 'ConsoleServer']


class ConsoleSSH(paramiko.ServerInterface):
    def __init__(self, *args, **kwargs):
        self.shell_requested = threading.Event()
        self.username = None

        super().__init__(*args, **kwargs)

    def check_auth_none(self, username):
        self.username = username
        return paramiko.AUTH_SUCCESSFUL

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED

        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_channel_shell_request(self, channel):
        self.shell_requested.set()
        return True

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True

    def get_allowed_auths(self, username):
        return 'none'


class ConsoleHandler(socketserver.StreamRequestHandler):
    def __init__(self, *args, settings=None, commands=None, **kwargs):
        if settings is None:
            settings = defaults.settings
        if commands is None:
            commands = defaults.commands

        self.settings = settings
        self.commands = commands

        super().__init__(*args, **kwargs)

    def setup(self):
        try:
            self.transport = paramiko.Transport(self.request)
            self.transport.add_server_key(self.settings['host_key'] if isinstance(self.settings['host_key'], paramiko.PKey) else paramiko.RSAKey.from_private_key_file(self.settings['host_key']))

            self.ssh = ConsoleSSH()

            self.transport.start_server(server=self.ssh)

            self.channel = self.transport.accept()

            self.ssh.shell_requested.wait(10)
            if not self.ssh.shell_requested.is_set():
                raise RuntimeError('No shell requested')
        except Exception:
            try:
                self.transport.close()
            except Exception:
                pass

            raise

    def handle(self):
        try:
            self.channel.send(self.settings['banner'].format(hostname=socket.gethostname(), commands=self.settings['banner_sep'].join(self.commands.keys())))

            cmdline = None
            history = []

            while True:
                self.channel.send(self.settings['prompt'])

                chistory = [list(line) for line in history]

                idx = 0
                hidx = len(chistory)

                chistory.append([])
                while True:
                    char = self.channel.recv(1).decode()
                    if char == '\x03':
                        raise exception.ConsoleQuit()
                    elif char == '\x04':
                        if len(chistory[hidx]) == 0:
                            raise exception.ConsoleQuit()
                    elif char == '\x09':
                        pass
                    elif char == '\x0d' or char == '\x1a':
                        self.channel.send('\r')
                        break
                    elif char == '\x7e':
                        if idx < len(chistory[hidx]):
                            del chistory[hidx][idx]
                            self.channel.send('\x1b[K')
                            self.channel.send(''.join(chistory[hidx][idx:]))
                            self.channel.send('\x1b[D' * (len(chistory[hidx]) - idx))
                    elif char == '\x7f':
                        if len(chistory[hidx]) > 0:
                            idx = idx - 1
                            del chistory[hidx][idx]
                            self.channel.send('\x1b[D')
                            self.channel.send('\x1b[K')
                            self.channel.send(''.join(chistory[hidx][idx:]))
                            self.channel.send('\x1b[D' * (len(chistory[hidx]) - idx))
                    elif char == '\x01':
                        self.channel.send('\x1b[D' * idx)
                        idx = 0
                    elif char == '\x05':
                        self.channel.send('\x1b[C' * (len(chistory[hidx]) - idx))
                        idx = len(chistory[hidx])
                    elif char == '\x0c':
                        self.channel.send('\x1b[2J\x1b[H')
                        self.channel.send('> ')
                        self.channel.send(''.join(chistory[hidx]))
                        self.channel.send('\x1b[D' * (len(chistory[hidx]) - idx))
                    elif char == '\x1b':
                        char = self.channel.recv(1).decode()
                        if char == '[':
                            char = self.channel.recv(1).decode()
                            num = 1
                            if char.isdigit():
                                num = int(char)
                                char = self.channel.recv(1).decode()
                                while char.isdigit():
                                    num = num * 10 + int(char)
                                    char = self.channel.recv(1).decode()

                            if char == 'A':
                                while num > 0:
                                    if hidx > 0:
                                        hidx = hidx - 1
                                        self.channel.send('\x1b[D' * idx)
                                        self.channel.send('\x1b[K')
                                        self.channel.send(''.join(chistory[hidx]))
                                        idx = len(chistory[hidx])
                                    num -= 1
                            elif char == 'B':
                                while num > 0:
                                    if hidx < len(chistory) - 1:
                                        hidx = hidx + 1
                                        self.channel.send('\x1b[D' * idx)
                                        self.channel.send('\x1b[K')
                                        self.channel.send(''.join(chistory[hidx]))
                                        idx = len(chistory[hidx])
                                    num -= 1
                            elif char == 'C':
                                while num > 0:
                                    if idx < len(chistory[hidx]):
                                        idx = idx + 1
                                        self.channel.send('\x1b[C')
                                    num -= 1
                            elif char == 'D':
                                while num > 0:
                                    if idx > 0:
                                        idx = idx - 1
                                        self.channel.send('\x1b[D')
                                    num -= 1
                            else:
                                while not char.isalpha():
                                    char = self.channel.recv(1).decode()
                        elif char == 'f':
                            while idx < len(chistory[hidx]):
                                if chistory[hidx][idx] == ' ':
                                    idx = idx + 1
                                    self.channel.send('\x1b[C')
                                    break

                                idx = idx + 1
                                self.channel.send('\x1b[C')
                        elif char == 'b':
                            if idx > 1:
                                idx = idx - 2
                                self.channel.send('\x1b[D' * 2)

                            while idx > 0:
                                if idx < len(chistory[hidx]) and chistory[hidx][idx] == ' ':
                                    idx = idx + 1
                                    self.channel.send('\x1b[C')
                                    break

                                idx = idx - 1
                                self.channel.send('\x1b[D')
                    else:
                        chistory[hidx].insert(idx, char)
                        idx = idx + 1
                        self.channel.send(char)
                        if idx < len(chistory[hidx]):
                            self.channel.send('\x1b[K')
                            self.channel.send(''.join(chistory[hidx][idx:]))
                            self.channel.send('\x1b[D' * (len(chistory[hidx]) - idx))
                self.channel.send('\n')

                cmdline = ''.join(chistory[hidx]).strip()

                if cmdline:
                    history.append(cmdline)
                else:
                    continue

                if len(history) > self.settings['max_history']:
                    history = history[-self.settings['max_history']:]

                try:
                    args = shlex.split(cmdline)

                    if not args:
                        continue

                    cmd = self.commands.get(args[0])

                    if cmd is None:
                        self.channel.send(self.settings['unrecognized'].format(cmd=args[0]))
                        continue

                    cmd_spec = inspect.getfullargspec(cmd)

                    kwargs = {}

                    if 'channel' in cmd_spec.kwonlyargs:
                        kwargs['channel'] = self.channel
                    if 'handler' in cmd_spec.kwonlyargs:
                        kwargs['handler'] = self
                    if 'name' in cmd_spec.kwonlyargs:
                        kwargs['name'] = args[0]

                    ret = cmd(*args[1:], **kwargs)

                    if 'channel' not in kwargs:
                        if ret is not None:
                            self.channel.send(str(ret))
                            self.channel.send('\r\n')
                except ValueError as e:
                    self.channel.send(self.settings['bad_syntax'].format(err=e))
                except TypeError:
                    self.channel.send(self.settings['bad_args'])
                    commands.help(args[0], name=args[0], handler=self)
                except exception.ConsoleExit:
                    pass
        except exception.ConsoleQuit:
            pass
        except UnicodeDecodeError:
            pass
        except KeyboardInterrupt:
            pass

    def finish(self):
        try:
            self.channel.close()
        except Exception:
            pass


class ConsoleServer(socketserver.ForkingTCPServer):
    allow_reuse_address = True

    def __init__(self, settings, commands, *args, handler=ConsoleHandler, **kwargs):
        super().__init__(settings['bind_addr'], functools.partial(handler, settings=settings, commands=commands), *args, **kwargs)

import argparse

from . import exception


__all__ = ['ConsoleArgumentParser']


class ConsoleArgumentParser(argparse.ArgumentParser):
    def __init__(self, name, channel, *args, **kwargs):
        super().__init__(*args, prog=name, **kwargs)
        self.channel = channel

    def _print_message(self, message, _=None):
        if message:
            self.channel.send(message.replace('\r\n', '\n').replace('\n', '\r\n'))

    def exit(self, _=0, message=None):
        if message:
            self._print_message(message, None)
        raise exception.ConsoleExit()

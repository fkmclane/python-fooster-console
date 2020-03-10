from .args import ConsoleArgumentParser
from .exception import ConsoleQuit, ConsoleExit
from .server import ConsoleHandler, ConsoleServer

from . import defaults
from . import commands

__all__ = ['name', 'version', 'ConsoleArgumentParser', 'ConsoleQuit', 'ConsoleExit', 'ConsoleHandler', 'ConsoleServer', 'defaults', 'commands']

name = 'fooster-console'
version = '0.0a0'

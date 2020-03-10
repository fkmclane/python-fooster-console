from . import commands as available


__all__ = ['settings', 'commands']


settings = {
    'max_history': 64,
    'host_key': 'host.key',
    'bind_addr': ('', 2222),

    'banner': 'Welcome to {hostname}!\r\nAvailable Commands:\r\n  {commands}\r\n',
    'banner_sep': '  ',
    'prompt': '> ',

    'usage': 'usage: ',
    'unrecognized': 'Command unrecognized: {cmd}\r\n',
    'bad_syntax': 'Invalid command syntax: {err}\r\n',
    'bad_args': 'Invalid command arguments\r\n',
}

commands = {
    'quit': available.quit,
    'help': available.help,
    'ping': available.ping,
}

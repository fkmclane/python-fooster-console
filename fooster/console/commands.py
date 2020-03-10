import inspect

from . import exception


__all__ = ['quit', 'ping', 'help']


def quit():
    raise exception.ConsoleQuit()


def ping():
    return


def help(cmd=None, *, name, handler):
    if cmd is None:
        cmd = name

    cmd_func = handler.commands.get(cmd)

    if cmd_func is None:
        handler.channel.send(handler.settings['unrecognized'].format(cmd=cmd))
        return

    cmd_spec = inspect.getfullargspec(cmd_func)

    if cmd_spec.varargs is not None:
        kwargs = {}

        if 'channel' in cmd_spec.kwonlyargs:
            kwargs['channel'] = handler.channel
        if 'handler' in cmd_spec.kwonlyargs:
            kwargs['handler'] = handler
        if 'name' in cmd_spec.kwonlyargs:
            kwargs['name'] = cmd

        cmd_func('-h', **kwargs)
    else:
        handler.channel.send(handler.settings['usage'])
        help_args = [cmd]
        help_args.extend(['<{}>'.format(arg) if idx < (len(cmd_spec.args) - (len(cmd_spec.defaults) if cmd_spec.defaults is not None else 0)) else '[{}]'.format(arg) for idx, arg in enumerate(cmd_spec.args)])
        handler.channel.send(' '.join(help_args))
        handler.channel.send('\r\n')

        if cmd_func.__doc__:
            handler.channel.send('\r\n')

            lines = cmd_func.__doc__.expandtabs().splitlines()

            indent = None
            for line in lines[1:]:
                stripped = line.lstrip()
                if stripped:
                    if indent is not None:
                        indent = min(indent, len(line) - len(stripped))
                    else:
                        indent = len(line) - len(stripped)

            doc = [lines[0].strip()]
            if indent:
                for line in lines[1:]:
                    doc.append(line[indent:].rstrip())

            while doc and not doc[-1]:
                doc.pop()
            while doc and not doc[0]:
                doc.pop(0)

            handler.channel.send('\r\n'.join(doc))

            handler.channel.send('\r\n')

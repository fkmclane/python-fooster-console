import fooster.console


def main():
    def docstring(a, b, c='c'):
        """
        This function concatenates input strings.

        Params:
          a: str
          b: str
          c: str = 'c'

        Returns:
          concatenated: str
        """

        return a + b + c

    def argparser(*args, name, channel):
        parser = fooster.console.ConsoleArgumentParser(name, channel)
        parser.add_argument('-t', '--test', action='store_true', dest='test', default=False, help='some test')
        parser.add_argument('-l', '--list', action='append', dest='list', default=[], help='some list')
        parser.add_argument('value', nargs='?', default='no', help='some value')
        margs = parser.parse_args(args)
        channel.send(str(margs))
        channel.send('\r\n')
        channel.send('Channel char: ')
        char = channel.recv(1)
        channel.send(char)
        channel.send('\r\n')

    example_commands = fooster.console.defaults.commands.copy()
    example_commands.update({
        'params': lambda x, y, z=5: int(x) + int(y) + int(z),
        'docstring': docstring,
        'argparser': argparser,
    })

    server = fooster.console.ConsoleServer(fooster.console.defaults.settings, example_commands)

    print('{} version {} running demo server'.format(fooster.console.name, fooster.console.version))

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()

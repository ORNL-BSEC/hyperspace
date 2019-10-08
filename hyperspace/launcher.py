#!/usr/bin/env python
import sys
import argparse

from hyperspace.api.config import Config
from hyperspace.internal.parser import Parser


def main():
    parser = argparse.ArgumentParser(description='Hyperspace launcher')
    parser.add_argument('config', metavar='FILENAME', help='Configuration file for the run')
    parser.add_argument('command', metavar='COMMAND', help='A command to run')
    parser.add_argument('varargs', nargs='*', default=[], metavar='VARARGS', help='Extra options to the command')
    parser.add_argument('-r', '--run_number', type=int, default=0, help="A run number")
    parser.add_argument('-s', '--seed', type=int, default=None, help="Random seed for the project")
    parser.add_argument('-t', '--tag', type=str, default=None, help="String tag for a given run")
    parser.add_argument(
        '-p', '--param', type=str, metavar='NAME=VALUE', action='append', default=[],
        help="Configuration parameters"
    )

    args = parser.parse_args()

    optimization_config = Config.from_file(
        args.config, args.run_number, seed=args.seed,
        parameters={k: v for (k, v) in (Parser.parse_equality(eq) for eq in args.param)}, 
        tag=args.tag
    )

    if optimization_config.project_dir not in sys.path:
        sys.path.append(optimization_config.project_dir)

    optimization_config.banner(args.command)
    optimization_config.run_command(args.command, args.varargs)
    optimization_config.quit_banner()


if __name__ == '__main__':
    main()

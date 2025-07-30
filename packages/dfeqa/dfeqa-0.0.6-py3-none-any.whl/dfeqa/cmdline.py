from __future__ import annotations

import argparse
import inspect
import sys
from importlib import import_module
from pkgutil import iter_modules
from types import ModuleType
from typing import TYPE_CHECKING

from dfeqa.commands import DfeqaCommand
from dfeqa.exceptions import UsageError

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    # typing.ParamSpec requires Python 3.10
    from typing_extensions import ParamSpec

    _P = ParamSpec("_P")


def _iter_command_classes(module_name: str) -> Iterable[type[DfeqaCommand]]:
    for module in _walk_modules(module_name):
        for obj in vars(module).values():
            if (
                inspect.isclass(obj)
                and issubclass(obj, DfeqaCommand)
                and obj.__module__ == module.__name__
                and obj != DfeqaCommand
            ):
                yield obj


def _get_commands() -> dict[str, DfeqaCommand]:
    return {
        cmd.__module__.split(".")[-1]: cmd()
        for cmd in _iter_command_classes("dfeqa.commands")
        }


def _pop_command_name(argv: list[str]) -> str | None:
    for i in range(1, len(argv)):
        if not argv[i].startswith("-"):
            return argv.pop(i)
    return None


def _print_commands() -> None:
    print("Usage:")
    print("  dfeqa <command> [options] [args]\n")
    print("Available commands:")
    cmds = _get_commands()
    for cmdname, cmdclass in sorted(cmds.items()):
        print(f"  {cmdname:<13} {cmdclass.short_desc()}")
    print()
    print('Use "dfeqa <command> -h" to see more info about a command')


def _print_unknown_command(cmdname) -> None:
    print(f"Unknown command: {cmdname}\n")
    print('Use "dfeqa" to see available commands')


def _run_print_help(
    parser: argparse.ArgumentParser,
    func: Callable[_P, None],
    *a: _P.args,
    **kw: _P.kwargs,
) -> None:
    try:
        func.run(*a, **kw)
    except UsageError as e:
        if str(e):
            parser.error(str(e))
        if e.print_help:
            parser.print_help()
        sys.exit(2)


def _walk_modules(path: str) -> list[ModuleType]:
    mods: list[ModuleType] = []
    mod = import_module(path)
    mods.append(mod)
    if hasattr(mod, "__path__"):
        for _, subpath, ispkg in iter_modules(mod.__path__):
            fullpath = path + "." + subpath
            if ispkg:
                mods += _walk_modules(fullpath)
            else:
                submod = import_module(fullpath)
                mods.append(submod)
    return mods


def execute(argv: list[str] | None = None) -> None:
    if argv is None:
        argv = sys.argv

    cmds = _get_commands()
    cmdname = _pop_command_name(argv)
    if not cmdname:
        _print_commands()
        sys.exit(0)
    elif cmdname not in cmds:
        _print_unknown_command(cmdname)
        sys.exit(2)

    cmd = cmds[cmdname]
    parser = argparse.ArgumentParser(
        usage=f"dfeqa {cmdname} {cmd.syntax()}",
        conflict_handler="resolve",
        description=cmd.long_desc(),
    )

    cmd.add_options(parser)
    opts, args = parser.parse_known_args(args=argv[1:])

    _run_print_help(parser, cmd, args, opts)
    sys.exit(cmd.exitcode)


if __name__ == "__main__":
    execute()

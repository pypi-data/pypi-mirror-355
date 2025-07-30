"""
Base class for Dfeqa commands
"""

import argparse


class DfeqaCommand:

    exitcode: int = 0

    def syntax(self) -> str:
        """
        Command syntax (preferably one-line). Do not include command name.
        """
        return ""

    def short_desc(self) -> str:
        """
        A short description of the command
        """
        return ""

    def long_desc(self) -> str:
        """A long description of the command. Return short description when not
        available. It cannot contain newlines since contents will be formatted
        by optparser which removes newlines and wraps text.
        """
        return self.short_desc()

    def help(self) -> str:
        """An extensive help for the command. It will be shown when using the
        "help" command. It can contain newlines since no post-formatting will
        be applied to its contents.
        """
        return self.long_desc()

    def add_options(self, parser: argparse.ArgumentParser) -> None:
        """
        Populate option parse with options available for this command
        """
        pass


    def run(self, args: list[str], opts: argparse.Namespace) -> None:
        """
        Entry point for running commands
        """
        raise NotImplementedError


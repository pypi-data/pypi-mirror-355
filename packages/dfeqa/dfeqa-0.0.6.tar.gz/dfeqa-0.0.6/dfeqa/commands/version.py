import argparse

import dfeqa
from dfeqa.commands import DfeqaCommand


class Command(DfeqaCommand):

    def short_desc(self) -> str:
        return "Print dfeqa version"

    def run(self, args: list[str], opts: argparse.Namespace) -> None:
        print(f"dfeqa {dfeqa.__version__}")

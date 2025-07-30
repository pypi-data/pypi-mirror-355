from __future__ import annotations

import argparse
from enum import Enum
from pathlib import Path
from shutil import copyfile

import dfeqa
from dfeqa.commands import DfeqaCommand


class Constants(Enum):
    ENV_FILENAME = "template.env"
    OUTPUT_FILENAME = ".env"

class Command(DfeqaCommand):

    # def __init__(self) -> None:
        # self.tmpl_dir = str(Path(dfeqa.__path__[0], "templates"))
        # pathlist = Path(self.templates_dir).glob('**/*.qmd')
        # self.tmpl_dict = {path.stem: str(path) for path in pathlist}

    # def syntax(self) -> str:
        # return "{%s} [<new_filename>]" % "|".join(self.templates_dict.keys())

    def short_desc(self) -> str:
        return "Create new environment file"

    # def add_options(self, parser: argparse.ArgumentParser) -> None:
    #     super().add_options(parser)
    #     parser.add_argument('template', nargs=1)
    #     parser.add_argument('filename', nargs='?')
    #     parser.add_argument('-c','--custom', action='store_true', help="flag to update report title with filename")

    def run(self, args: list[str], opts: argparse.Namespace) -> None:
        print(" ... dfeqa add environment variables ...\n")

        copyfile(str(Path(dfeqa.__path__[0], "template.env")), str(Path(Path.cwd(), ".env")))

        print(".env file ready.")

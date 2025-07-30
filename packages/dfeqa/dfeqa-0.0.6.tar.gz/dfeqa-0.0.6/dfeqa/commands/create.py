from __future__ import annotations

import argparse
from pathlib import Path

import dfeqa
from dfeqa import parse_text
from dfeqa.commands import DfeqaCommand
from dfeqa.exceptions import UsageError


class Command(DfeqaCommand):

    def __init__(self) -> None:
        self.tmpl_dir = str(Path(dfeqa.__path__[0], "templates"))
        pathlist = Path(self.templates_dir).glob('**/*.qmd')
        self.tmpl_dict = {path.stem: str(path) for path in pathlist}

    def syntax(self) -> str:
        return "{%s} [<new_filename>]" % "|".join(self.templates_dict.keys())

    def short_desc(self) -> str:
        return "Create new report"

    def add_options(self, parser: argparse.ArgumentParser) -> None:
        super().add_options(parser)
        parser.add_argument('template', nargs=1)
        parser.add_argument('filename', nargs='?')
        parser.add_argument('-c','--custom', action='store_true', help="flag to update report title with filename")

    def run(self, args: list[str], opts: argparse.Namespace) -> None:
        print(" ... dfeqa create report ...\n")

        template = opts.template[0]
        # check if template is valid and exists
        if template not in self.templates_dict.keys():
            print("Create a report from the following templates:")
            for t in self.templates_dict.keys():
                print('- ' + t)
            print()
            raise UsageError

        output_path_with_file = str(Path(Path.cwd(), Path(self.templates_dict[template]).name))
        output_reportname = template
        if (opts.filename):
            assert len(opts.filename)>0
            output_path_with_file = str(Path(Path.cwd(), opts.filename))
            output_reportname = opts.filename.rpartition('.')[0]
            if output_reportname=="":
                output_reportname = opts.filename

        d = {'report_title': template}
        if (opts.custom):
            d['report_title'] = output_reportname
        with open(self.templates_dict[template], 'r') as reader:
            t = reader.read()
            if (opts.custom):
                t = parse_text(t, d)
        with open(output_path_with_file, 'w') as writer:
            writer.write(t)
        print(f"template '{template}' ready.")

    @property
    def templates_dir(self) -> str:
        return self.tmpl_dir
    @property
    def templates_dict(self) -> dict[str, str]:
        return self.tmpl_dict

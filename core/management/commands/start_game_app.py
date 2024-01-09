import argparse

from django.core.management.templates import TemplateCommand


class Command(TemplateCommand):
    help = "Create the folder structure for a Django app that corresponds to a game."

    def add_arguments(self, parser):
        parser.add_argument(
            "directory", nargs="?", help="Optional destination directory"
        )
        parser.add_argument(
            "--template", help="The path or URL to load the template from."
        )
        parser.add_argument(
            "--extension",
            "-e",
            dest="extensions",
            action="append",
            default=["py"],
            help='The file extension(s) to render (default: "py"). '
            "Separate multiple extensions with commas, or use "
            "-e multiple times.",
        )
        parser.add_argument(
            "--name",
            "-n",
            dest="files",
            action="append",
            default=[],
            help="The file name(s) to render. Separate multiple file names "
            "with commas, or use -n multiple times.",
        )
        parser.add_argument(
            "--exclude",
            "-x",
            action="append",
            default=argparse.SUPPRESS,
            nargs="?",
            const="",
            help=(
                "The directory name(s) to exclude, in addition to .git and "
                "__pycache__. Can be used multiple times."
            ),
        )

    def handle(self, *args, **options):
        name = input("Name of the app corresponding to the game: ")
        long_name = input("Long name of the game: ")
        url_tag = input("URL tag for the game: ")
        url_namespace = input("Namespace for the game: ")

        target = options.pop("directory")

        options["template"] = "game_app_template"
        options["app_long_name"] = long_name
        options["app_url_tag"] = url_tag
        options["app_url_namespace"] = url_namespace
        super().handle("app", name, target, **options)

        self.stdout.write(self.style.SUCCESS(f'Successfully created app "{name}"'))

import csv

from django.core.exceptions import ValidationError
from django.core.management import BaseCommand
from django.core.validators import validate_slug

from core.constants import player_username
from core.models import Session, Player, CustomUser


class Command(BaseCommand):
    help = "Populate players from a csv file"

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="Path to the CSV file")
        parser.add_argument("session_url_tag", type=str, help="Session URL tag")

    def handle(self, *args, **options):
        session_url_tag = options["session_url_tag"]
        try:
            session = Session.objects.get(url_tag=session_url_tag)
        except Session.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f"Session with URL tag {session_url_tag} does not exist."
                )
            )
            return

        csv_file_path = options["csv_file"]
        num_created = 0
        num_fail = 0
        with open(csv_file_path, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file, delimiter=",")
            if reader:
                for row in reader:
                    if "username" not in row:
                        raise ValueError(
                            "The csv needs to have a column with 'username'. The delimiter should be ','."
                        )
                    player_name = row["username"].strip()
                    try:
                        validate_slug(player_name)
                    except ValidationError:
                        self.stdout.write(
                            self.style.ERROR(
                                f"FAIL: username '{player_name}' is not a valid slug, "
                                f"line has been skipped."
                            )
                        )
                        num_fail += 1
                        continue
                    username = player_username(session, player_name)
                    password = row.get("password", None)
                    if password:
                        stripped_password = password.strip()
                        if stripped_password != password:
                            self.stdout.write(
                                f"WARNING: The provided password for '{player_name}' had leading "
                                f"and/or trailing whitespaces that have been removed."
                            )
                        password = stripped_password
                    else:
                        password = "thisisthegameserver"
                        self.stdout.write(
                            f"WARNING: No password was provided for user '{player_name}', a "
                            f"default password '{password}' has been used."
                        )
                    email = row.get("email", None)
                    if email:
                        email = email.strip()

                    if (
                        CustomUser.objects.filter(username=username).exists()
                        or Player.objects.filter(
                            session=session, name=player_name
                        ).exists()
                    ):
                        self.stdout.write(
                            self.style.ERROR(
                                f"FAIL: username '{player_name}' already used, "
                                f"line has been skipped."
                            )
                        )
                        num_fail += 1
                    else:
                        user = CustomUser.objects.create_user(
                            username=username,
                            password=password,
                            email=email,
                            is_player=True,
                        )
                        Player.objects.create(
                            user=user, name=player_name, session=session
                        )
                        num_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f" \n{num_created} players imported, {num_fail} failures."
            )
        )

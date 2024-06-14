GUEST_PASSWORD_PREFIX = "GuestPass_"
TEAM_USER_USERNAME = "TeamUser"
TEAM_USER_PASSWORD = "TeamUserPassword"
TEAM_PLAYERNAME_PREFIX = "TeamPlayer_"
RANDOM_PLAYERNAME_PREFIX = "RandomPlayer"

FORBIDDEN_SESSION_URL_TAGS = ("", "admin", "user", "logout", "message", "createsession")
FORBIDDEN_APP_URL_TAGS = ("forcedlogout", "home", "admin")
FORBIDDEN_USERNAMES = (TEAM_USER_USERNAME,)


def player_username(session, player_name):
    return "Player_{}_{}".format(session.url_tag, player_name)


def guest_username(session, guest_name):
    return "Guest_{}_{}".format(session.url_tag, guest_name)


def guest_password(username):
    return GUEST_PASSWORD_PREFIX + str(username)


def team_player_name(game_name, team_name):
    return game_name + "_TeamPlayer_" + team_name

# Prefix for the password used for guests
GUEST_PASSWORD_PREFIX = "GuestPass_"
# User used for the team mechanism
TEAM_USER_USERNAME = "TeamUser"
# Password of the team user
TEAM_USER_PASSWORD = "TeamUserPassword"
# Prefix used for the player created for each team
TEAM_PLAYERNAME_PREFIX = "TeamPlayer_"
# Prefix used for the name of randomly generated players
RANDOM_PLAYERNAME_PREFIX = "RandomPlayer"

# Names that are reserved and cannot be chosen as session name (not to mess up with URL routing)
FORBIDDEN_SESSION_URL_TAGS = ("", "admin", "user", "logout", "message", "createsession", "about", "faq", "termsconditions", "privacypolicy", "cookiepolicy", )
# Names that are reserved and cannot be chosen as a URL tag for a game app  (not to mess up with
# URL routing)
FORBIDDEN_APP_URL_TAGS = ("forcedlogout", "home", "admin")
# Usernames that cannot be used by regular users
FORBIDDEN_USERNAMES = (TEAM_USER_USERNAME,)


def player_username(session, player_name):
    """Constructs a username for someone registering as a session player but not a global user"""
    return "Player_{}_{}".format(session.url_tag, player_name)


def guest_username(session, guest_name):
    """Constructs a username for someone joining a session as a guest"""
    return "Guest_{}_{}".format(session.url_tag, guest_name)


def guest_password(username):
    """Constructs a password for someone joining a session as a guest"""
    return GUEST_PASSWORD_PREFIX + str(username)


def team_player_name(game_name, team_name):
    """Constructs the name of the player corresponding to a team"""
    return game_name + "_TeamPlayer_" + team_name

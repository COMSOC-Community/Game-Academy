SESSION_GROUP_PREFIX = "Session_Group_"
GUEST_PASSWORD_PREFIX = "ThisIsThePasswordForTheGuest_"


def player_username(session, player_name):
    return "GamePlayer_{}_{}".format(session.slug_name, player_name)


def guest_username(session, guest_name):
    return "GameGuest_{}_{}".format(session.slug_name, guest_name)


def guest_password(username):
    return GUEST_PASSWORD_PREFIX + str(username)

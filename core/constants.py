GUEST_PASSWORD_PREFIX = "GuestPass_"


def player_username(session, player_name):
    return "Player_{}_{}".format(session.url_tag, player_name)


def guest_username(session, guest_name):
    return "Guest_{}_{}".format(session.url_tag, guest_name)


def guest_password(username):
    return GUEST_PASSWORD_PREFIX + str(username)

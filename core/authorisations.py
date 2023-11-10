def can_create_sessions(user):
    return user.is_authenticated and not user.is_player


def is_session_admin(session, user):
    return user.is_authenticated and (user in session.admins.all() or user.is_staff)

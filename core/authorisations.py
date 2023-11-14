def can_create_sessions(user):
    return user.is_authenticated and not user.is_player


def is_session_admin(session, user):
    return user.is_authenticated and (user.is_staff or user in session.admins.all() or user in session.super_admins.all())


def is_session_super_admin(session, user):
    return user.is_authenticated and (user.is_staff or user in session.super_admins.all())

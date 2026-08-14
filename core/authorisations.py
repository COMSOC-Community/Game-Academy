def can_create_sessions(user):
    return user.is_authenticated and not user.is_player


def get_session_admin_status(session, user):
    """Returns the pair (is_session_admin, is_session_super_admin) for the given user and
    session. Computed with at most two lightweight existence queries (none if the user is
    staff or not authenticated), instead of fetching the full admins/super_admins querysets."""
    if not user.is_authenticated:
        return False, False
    if user.is_staff:
        return True, True
    is_super_admin = session.super_admins.filter(pk=user.pk).exists()
    is_admin = is_super_admin or session.admins.filter(pk=user.pk).exists()
    return is_admin, is_super_admin


def is_session_admin(session, user):
    """A session admin is either an (super)admin of the session or a staff member."""
    is_admin, _ = get_session_admin_status(session, user)
    return is_admin


def is_session_super_admin(session, user):
    """A session super admin is either a super admin of the session or a staff member."""
    _, is_super_admin = get_session_admin_status(session, user)
    return is_super_admin

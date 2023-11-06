from core.constants import SESSION_MANAGER_GROUP


def can_create_sessions(user):
    if user.is_authenticated:
        return user.is_staff or user.groups.filter(name=SESSION_MANAGER_GROUP)
    return False

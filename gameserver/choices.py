def find_choice_value(choices, key):
    for (k, v) in choices:
        if k == key:
            return v
    return None

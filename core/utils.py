
def float_formatter(value, num_digits=2):
    if int(value) == value:
        return str(int(value))
    return "{:.{}f}".format(value, num_digits)

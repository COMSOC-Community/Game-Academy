def float_formatter(value, num_digits=3):
    value = float(value)
    if num_digits is None:
        formatted_value = str(value)
    else:
        formatted_value = "{:.{}f}".format(value, num_digits)
    return (
        formatted_value.rstrip("0").rstrip(".")
        if "." in formatted_value
        else formatted_value
    )

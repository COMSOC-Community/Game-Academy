# Standard logging to stdout (access logs)
accesslog = '-'  # Means stdout

# Standard logging to stderr (error logs)
errorlog = '-'  # Means stderr

# Log level (default is 'info', can also use 'debug', 'warning', 'error')
loglevel = 'info'

# Number of lines to retain in log files if logging to a file
max_log_file_size = 10 * 1024 * 1024
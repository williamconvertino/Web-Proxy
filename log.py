# Log Level
# -1: errors/exceptions
# 0: basic messages (client request, connection failed)
# 1: http/https connections
# 2: allowlist/denylist info
# 3: dynamic filtering info
# 4: cache info

LOG_OPTIONS = [3]

def log(level, msg):
        """
        Print a message to standard output with specified "log level" - the
        message is only printed if the global DEBUG_OPTIONS contains
        the level parameter.
        """
        if level in LOG_OPTIONS:
            print(msg)
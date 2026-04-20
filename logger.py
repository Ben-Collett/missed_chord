import platform
YELLOW = "\033[33m"
RESET = "\033[0m"


def log_warning(*args, sep=" ", end="\n"):
    if platform.system() == "Windows":
        print(*args, sep=sep, end=end)
    else:
        print(YELLOW, end="")
        print(*args, sep=sep, end="")
        print(RESET, end=end)

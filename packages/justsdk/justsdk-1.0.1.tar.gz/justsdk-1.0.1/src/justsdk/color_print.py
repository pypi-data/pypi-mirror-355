from .ansi import Fore


def print_color(m: str, prefix: str, color: str = Fore.RESET) -> None:
    print(f"[{color}{prefix}{Fore.RESET}] {m}")


def print_success(m: str) -> None:
    print_color(m, "success", Fore.GREEN)


def print_warning(m: str) -> None:
    print_color(m, "warning", Fore.YELLOW)


def print_error(m: str) -> None:
    print_color(m, "error", Fore.RED)


def print_info(m: str) -> None:
    print_color(m, "info", Fore.MAGENTA)

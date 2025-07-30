from .ansi import Fore


def print_color(
    m: str, prefix: str, color: str = Fore.RESET, newline_before: bool = False
) -> None:
    newline = "\n" if newline_before else ""
    print(f"{newline}[{color}{prefix}{Fore.RESET}] {m}")


def print_success(m: str, newline_before: bool = False) -> None:
    print_color(m, "success", Fore.GREEN, newline_before)


def print_warning(m: str, newline_before: bool = False) -> None:
    print_color(m, "warning", Fore.YELLOW, newline_before)


def print_error(m: str, newline_before: bool = False) -> None:
    print_color(m, "error", Fore.RED, newline_before)


def print_info(m: str, newline_before: bool = False) -> None:
    print_color(m, "info", Fore.MAGENTA, newline_before)

import sys
import textwrap
import traceback

from colorful_terminal import *


def print_exception_details(exception: Exception):
    """Print the exception details.\n
    Usage:\n
        `try:`\n
        `    ... `\n
        `except Exception as e: `\n
        `    print_exception_details(e)`\n

    Contains:
    - function name
    - filepath
    - line
    - code snippet
    - species of the exception
    - message

    Args:
        exception (Exception): Your Exception
    """
    tb = sys.exc_info()[-1]
    stk = traceback.extract_tb(tb, 1)
    filepath = stk[0][0]
    line = stk[0][1]
    functionname = stk[0][2]
    traceback_parts = list(
        traceback.TracebackException.from_exception(exception).format()
    )
    code_teile = traceback_parts[-2].split("\n")[1:-1]
    code_teile = [n.strip() for n in code_teile]
    fehlertyp = traceback_parts[-1].split(": ")[0]
    code = "; ".join(code_teile)

    colored_print(
        f"Exception in the function {Fore.BRIGHT_RED}{functionname}{Fore.WHITE}"
    )
    colored_print(f"\tFilepath: \n\t\t{Fore.MAGENTA}{filepath}{Fore.WHITE}")
    colored_print(f"\tLine:\n\t\t{Fore.BRIGHT_YELLOW}{line}{Fore.WHITE}")
    colored_print(f"\tCode:\n\t\t{Fore.BRIGHT_BLUE}{code}{Fore.WHITE}")
    colored_print(f"\tSpecies:\n\t\t{Fore.BRIGHT_RED}{fehlertyp}{Fore.WHITE}")
    colored_print(f"\tMessage:")
    wrapper = textwrap.TextWrapper(
        width=200, initial_indent="\t\t", subsequent_indent="\t\t"
    )
    e_str = str(exception)
    if e_str.isspace() or e_str == "":
        e_str = "<Kein Text verfügbar>"
    word_list = wrapper.wrap(text=e_str)
    # colored_print each line.
    for element in word_list:
        colored_print(Fore.BRIGHT_CYAN + element + Fore.WHITE)


def print_exception_details_full_traceback(exception: Exception):
    """Print detailed information about an exception including full traceback."""
    tb = exception.__traceback__
    tb_summary = traceback.extract_tb(tb)

    colored_print(
        f"{Fore.BRIGHT_RED}Full Traceback (most recent call last):{Fore.WHITE}"
    )
    for frame in tb_summary:
        filepath = frame.filename
        line = frame.lineno
        functionname = frame.name
        code = frame.line.strip() if frame.line else "<no code available>"

        colored_print(
            f"\n{Fore.WHITE}In function {Fore.BRIGHT_RED}{functionname}{Fore.WHITE}"
        )
        colored_print(f"\tFilepath: \n\t\t{Fore.MAGENTA}{filepath}{Fore.WHITE}")
        colored_print(f"\tLine:\n\t\t{Fore.BRIGHT_YELLOW}{line}{Fore.WHITE}")
        colored_print(f"\tCode:\n\t\t{Fore.BRIGHT_BLUE}{code}{Fore.WHITE}")

    # Exception type and message
    exception_type = type(exception).__name__
    exception_message = str(exception).strip() or "<Kein Text verfügbar>"

    colored_print(
        f"{Fore.WHITE}\tSpecies:\n\t\t{Fore.BRIGHT_RED}{exception_type}{Fore.WHITE}"
    )
    colored_print(f"\tMessage:")
    wrapper = textwrap.TextWrapper(
        width=200, initial_indent="\t\t", subsequent_indent="\t\t"
    )
    for line in wrapper.wrap(exception_message):
        colored_print(Fore.BRIGHT_CYAN + line + Fore.WHITE)


def get_exception_details_dict(exception: Exception):
    """Get the exception details as a dictionary.\n
    Usage:\n
        `try:`\n
        `    ... `\n
        `except Exception as e: `\n
        `    details = get_exception_details_dict(e)`\n

    Contains:
    - 'function' -> function name
    - 'path' -> filepath
    - 'line' -> line
    - 'code' -> code snippet
    - 'species' -> species of the exception
    - 'message' -> message

    Args:
        exception (Exception): Your Exception

    Returns:
        dict: Exception details as a dictionary with the keys: "function", "path", "line", "code", "species", "message"
    """
    tb = sys.exc_info()[-1]
    stk = traceback.extract_tb(tb, 1)
    filepath = stk[0][0]
    line = stk[0][1]
    functionname = stk[0][2]
    traceback_parts = list(
        traceback.TracebackException.from_exception(exception).format()
    )
    code_teile = traceback_parts[-2].split("\n")[1:-1]
    code_teile = [n.strip() for n in code_teile]
    fehlertyp = traceback_parts[-1].split(": ")[0]
    code = "; ".join(code_teile)
    e_str = str(exception)
    if e_str.isspace() or e_str == "":
        e_str = "<Kein Text verfügbar>"

    details = {
        "function": functionname,
        "path": filepath,
        "line": line,
        "code": code,
        "species": fehlertyp,
        "message": e_str,
    }
    return details


def get_exception_details_dict_full_traceback(exception: Exception):
    """Get the full traceback exception details as a dictionary list.

    Returns:
        List[dict]: One dictionary per traceback level.
    """
    tb = exception.__traceback__
    tb_summary = traceback.extract_tb(tb)
    results = []

    for frame in tb_summary:
        filepath = frame.filename
        line = frame.lineno
        functionname = frame.name
        code = frame.line.strip() if frame.line else "<no code available>"

        results.append(
            {
                "function": functionname,
                "path": filepath,
                "line": line,
                "code": code,
            }
        )

    exception_type = type(exception).__name__
    exception_message = str(exception).strip() or "<Kein Text verfügbar>"

    results[-1]["species"] = exception_type
    results[-1]["message"] = exception_message

    return results


def get_exception_details_str(exception: Exception, colored: bool = True):
    """Print the exception details.\n
    Usage:\n
        `try:`\n
        `    ... `\n
        `except Exception as e: `\n
        `    details = get_exception_details_str(e)`\n

    Contains:
    - function name
    - filepath
    - line
    - code snippet
    - species of the exception
    - message

    Args:
        exception (Exception): Your Exception
        colored (boolean): The string has coloreds parts if True.

    Returns:
        str: Exception details as a string."
    """
    tb = sys.exc_info()[-1]
    stk = traceback.extract_tb(tb, 1)
    filepath = stk[0][0]
    line = stk[0][1]
    functionname = stk[0][2]
    traceback_parts = list(
        traceback.TracebackException.from_exception(exception).format()
    )
    code_teile = traceback_parts[-2].split("\n")[1:-1]
    code_teile = [n.strip() for n in code_teile]
    fehlertyp = traceback_parts[-1].split(": ")[0]
    code = "; ".join(code_teile)

    if colored:
        flr = Fore.BRIGHT_RED
        fw = Fore.WHITE
        fm = Fore.MAGENTA
        fly = Fore.BRIGHT_YELLOW
        flb = Fore.BRIGHT_BLUE
        flc = Fore.BRIGHT_CYAN
    else:
        flr = ""
        fw = ""
        fm = ""
        fly = ""
        flb = ""
        flc = ""

    fehler_str = ""

    fehler_str += f"Exception in the function {flr}{functionname}{fw}" + "\n"
    fehler_str += f"\tFilepath: \n\t\t{fm}{filepath}{fw}" + "\n"
    fehler_str += f"\tLine:\n\t\t{fly}{line}{fw}" + "\n"
    fehler_str += f"\tCode:\n\t\t{flb}{code}{fw}" + "\n"
    fehler_str += f"\tSpecies:\n\t\t{flr}{fehlertyp}{fw}" + "\n"
    fehler_str += f"\tMessage:" + "\n"
    wrapper = textwrap.TextWrapper(
        width=200, initial_indent="\t\t", subsequent_indent="\t\t"
    )
    e_str = str(exception)
    if e_str.isspace() or e_str == "":
        e_str = "<Kein Text verfügbar>"
    word_list = wrapper.wrap(text=e_str)
    len_word_list = len(word_list)
    for i, element in enumerate(word_list):
        fehler_str += flc + element + fw
        if i != len_word_list - 1:
            fehler_str += "\n"

    return fehler_str


def get_exception_details_str_full_traceback(
    exception: Exception, colored: bool = True
):
    """Return the full traceback as a formatted string."""

    tb = exception.__traceback__
    tb_summary = traceback.extract_tb(tb)

    if colored:
        flr = Fore.BRIGHT_RED
        fw = Fore.WHITE
        fm = Fore.MAGENTA
        fly = Fore.BRIGHT_YELLOW
        flb = Fore.BRIGHT_BLUE
        flc = Fore.BRIGHT_CYAN
    else:
        flr = fw = fm = fly = flb = flc = ""

    fehler_str = f"{flr}Full Traceback (most recent call last):{fw}\n"

    for frame in tb_summary:
        filepath = frame.filename
        line = frame.lineno
        functionname = frame.name
        code = frame.line.strip() if frame.line else "<no code available>"

        fehler_str += f"\nIn function {flr}{functionname}{fw}\n"
        fehler_str += f"\tFilepath: \n\t\t{fm}{filepath}{fw}\n"
        fehler_str += f"\tLine:\n\t\t{fly}{line}{fw}\n"
        fehler_str += f"\tCode:\n\t\t{flb}{code}{fw}\n"

    exception_type = type(exception).__name__
    exception_message = str(exception).strip() or "<Kein Text verfügbar>"

    fehler_str += f"\tSpecies:\n\t\t{flr}{exception_type}{fw}\n"
    fehler_str += f"\tMessage:\n"

    wrapper = textwrap.TextWrapper(
        width=200, initial_indent="\t\t", subsequent_indent="\t\t"
    )
    for line in wrapper.wrap(exception_message):
        fehler_str += flc + line + fw + "\n"

    return fehler_str.strip()

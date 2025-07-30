from exception_details import (
    print_exception_details,
    print_exception_details_full_traceback,
    get_exception_details_dict,
    get_exception_details_dict_full_traceback,
    get_exception_details_str,
    get_exception_details_str_full_traceback,
)
from colorful_terminal import *
from var_print import varp


def level3():
    raise ValueError("This is the root exception at level 3")


def level2():
    level3()


def level1():
    level2()


def test_print_exception_details():
    colored_print(Fore.NEON_CYAN + "\n\ntest_print_exception_details\n")
    try:
        level1()
    except Exception as e:
        print_exception_details(e)


def test_print_exception_details_full_traceback():
    colored_print(Fore.NEON_CYAN + "\n\ntest_print_exception_details_full_traceback\n")
    try:
        level1()
    except Exception as e:
        print_exception_details_full_traceback(e)


def test_get_exception_details_dict():
    colored_print(Fore.NEON_CYAN + "\n\ntest_get_exception_details_dict\n")
    try:
        level1()
    except Exception as e:
        varp(get_exception_details_dict(e))


def test_get_exception_details_dict_full_traceback():
    colored_print(Fore.NEON_CYAN + "\n\ntest_get_exception_details_dict\n")
    try:
        level1()
    except Exception as e:
        varp(get_exception_details_dict_full_traceback(e))


def test_get_exception_details_str():
    colored_print(Fore.NEON_CYAN + "\n\ntest_get_exception_details_str\n")
    try:
        level1()
    except Exception as e:
        print(get_exception_details_str(e))


def test_get_exception_details_str_full_traceback():
    colored_print(Fore.NEON_CYAN + "\n\ntest_get_exception_details_str\n")
    try:
        level1()
    except Exception as e:
        print(get_exception_details_str_full_traceback(e))


# Run the test
test_print_exception_details()
test_print_exception_details_full_traceback()
test_get_exception_details_dict()
test_get_exception_details_dict_full_traceback()
test_get_exception_details_str()
test_get_exception_details_str_full_traceback()

import _version
__version__ = _version.get_versions()["version"]
print(f"\n\nVersion: {__version__}")

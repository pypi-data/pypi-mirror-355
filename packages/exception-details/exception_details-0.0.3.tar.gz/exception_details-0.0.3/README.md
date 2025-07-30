# exception_details
*Get nicely formated exception details.*

## Content
- Installation
- Usage

## Installation
`pip install exception-details`

## Usage
- `print_exception_details(exception: Exception)`  
  Print the exception details.  
    Usage:  
        `try: ...`  
        `except Exception as e: print_exception_details(e)`  

    Contains:
    - function name
    - filepath
    - line
    - code snippet
    - species of the exception
    - message

    Args:
        exception (Exception): Your Exception
- `get_exception_details_dict(exception: Exception)`  
  Get the exception details as a dictionary.  
    Usage:  
        `try: ... `  
        `except Exception as e: details = get_exception_details_dict(e)`  
        
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
- `get_exception_details_str(exception: Exception, colored=True)`  
  Print the exception details.  
    Usage:  
        `try: ... `  
        `except Exception as e: details = get_exception_details_str(e)`  

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

## Links
[GitHub](https://github.com/ICreedenI/exception_details) | [PyPI](https://pypi.org/project/exception-details/)
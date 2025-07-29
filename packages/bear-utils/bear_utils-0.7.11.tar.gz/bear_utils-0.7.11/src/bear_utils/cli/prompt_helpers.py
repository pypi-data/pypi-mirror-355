from typing import Any, overload

from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.validation import ValidationError, Validator

from ..constants._exceptions import UserCancelled
from ..constants._lazy_typing import LitBool, LitFloat, LitInt, LitStr, OptBool, OptFloat, OptInt, OptStr
from ..logging.loggers import get_console


@overload
def ask_question(question: str, expected_type: LitInt, default: OptInt = None, **kwargs) -> int: ...


@overload
def ask_question(question: str, expected_type: LitFloat, default: OptFloat = None, **kwargs) -> float: ...


@overload
def ask_question(question: str, expected_type: LitStr, default: OptStr = None, **kwargs) -> str: ...


@overload
def ask_question(question: str, expected_type: LitBool, default: OptBool = None, **kwargs) -> bool: ...


def ask_question(question: str, expected_type: Any, default: Any = None, **kwargs) -> Any:
    """
    Ask a question and return the answer, ensuring the entered type is correct and a value is entered.

    This function will keep asking until it gets a valid response or the user cancels with Ctrl+C.
    If the user cancels, a UserCancelled is raised.

    Args:
        question: The prompt question to display
        expected_type: The expected type of the answer (int, float, str, bool)
        default: Default value if no input is provided

    Returns:
        The user's response in the expected type

    Raises:
        UserCancelled: If the user cancels input with Ctrl+C
        ValueError: If an unsupported type is specified
    """
    console, sub = get_console("prompt_helpers.py")
    try:
        while True:
            console.info(question)
            response: str = prompt("> ")
            if response == "":
                if default is not None:
                    return default
                else:
                    continue
            match expected_type:
                case "int":
                    try:
                        result = int(response)
                        sub.verbose("int detected")
                        return result
                    except ValueError:
                        sub.error("Invalid input. Please enter a valid integer.")
                case "float":
                    try:
                        result = float(response)
                        sub.verbose("float detected")
                        return result
                    except ValueError:
                        sub.error("Invalid input. Please enter a valid float.")
                case "str":
                    sub.verbose("str detected")
                    return response
                case "bool":
                    lower_response = response.lower()
                    if lower_response in ("true", "t", "yes", "y", "1"):
                        return True
                    elif lower_response in ("false", "f", "no", "n", "0"):
                        return False
                    else:
                        sub.error("Invalid input. Please enter a valid boolean (true/false, yes/no, etc).")
                case _:
                    raise ValueError(f"Unsupported type: {expected_type}")
    except KeyboardInterrupt:
        raise UserCancelled("User cancelled input")


def ask_yes_no(question, default=None, **kwargs) -> None | bool:
    """
    Ask a yes or no question and return the answer.

    Args:
        question: The prompt question to display
        default: Default value if no input is provided

    Returns:
        True for yes, False for no, or None if no valid response is given
    """
    sub, console = get_console("prompt_helpers.py")
    try:
        while True:
            console.info(question)
            response = prompt("> ")

            if response == "":
                if default is not None:
                    return default
                else:
                    continue

            if response.lower() in ["yes", "y"]:
                return True
            elif response.lower() in ["no", "n"]:
                return False
            elif response.lower() in ["exit", "quit"]:
                return None
            else:
                console.error("Invalid input. Please enter 'yes' or 'no' or exit.")
                continue
    except KeyboardInterrupt:
        console.warning("KeyboardInterrupt: Exiting the prompt.")
        return None


def restricted_prompt(question, valid_options, exit_command="exit", **kwargs):
    """
    Continuously prompt the user until they provide a valid response or exit.

    Args:
        question: The prompt question to display
        valid_options: List of valid responses
        exit_command: Command to exit the prompt (default: "exit")

    Returns:
        The user's response or None if they chose to exit
    """
    sub, console = get_console("prompt_helpers.py")
    completer_options = valid_options + [exit_command]
    completer = WordCompleter(completer_options)

    class OptionValidator(Validator):
        def validate(self, document):
            text = document.text.lower()
            if text != exit_command and text not in valid_options:
                raise ValidationError(f'Please enter one of: {", ".join(valid_options)} (or "{exit_command}" to quit)')  # type: ignore

    try:
        while True:
            if console is not None:
                console.info(question)
                response = prompt("> ", completer=completer, validator=OptionValidator(), complete_while_typing=True)
                response = response.lower()
            else:
                response = prompt(
                    question, completer=completer, validator=OptionValidator(), complete_while_typing=True
                )
                response = response.lower()

            if response == exit_command or response == "":
                return None
            elif response in valid_options:
                return response
    except KeyboardInterrupt:
        sub.warning("KeyboardInterrupt: Exiting the prompt.")
        return None

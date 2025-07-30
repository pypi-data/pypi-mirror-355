"""ChatGPT REPL

Entry point for the ChatGPT REPL.
"""
from datetime import datetime as dt
from pathlib import Path

from ..io import stream
from .interfaces import ChatGPT
from ..llm.models import CHATGPT_CONVERSATIONS_DIR, ChatGPTModel

pp = stream

# Helper functions
def check_for_jupyter() -> bool:
    """
    check_for_jupyter

    Evaluates whether the REPL is being invoked within a Jupyter environment.
    """
    try:
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':  # Jupyter notebook or qtconsole
            return True
        elif shell == 'TerminalInteractiveShell':  # Terminal IPython
            return False
        else:
            return False
    except NameError:  # Likely standard Python interpreter
        return False

def main() -> bool:
    """
    main

    Runloop for the ChatGPT REPL.
    """
    exit_commands: list = ["quit", "exit", "q", "e", "x"]
    save_command: str = "save"
    load_command: str = "load"
    is_jupyter = check_for_jupyter()

    # Instantiate the ChatGPT interface
    chatgpt = ChatGPT()

    try:
        while True:
            pp("[You]")  # No newline after [You]
            prompt = input()  # Get input on same line

            if is_jupyter:
                pp("\n\n[You]")
                pp(prompt)
                pp("\n")

            # Check for exit command
            if prompt.lower() in exit_commands:
                pp("Goodbye!")
                return True

            # Check for save command
            if prompt.lower() == save_command:
                chatgpt.save(save_as=Path(
                    f"{CHATGPT_CONVERSATIONS_DIR}/{dt.now().strftime('%Y-%m-%d_%H%M%S')}.json"
                ))
                pp("Conversation saved!\n")
                continue

            # Check for load command
            if prompt.lower().startswith(load_command):
                try:
                    # Extract the filepath from the command
                    filepath = prompt[len(load_command):].strip().strip("'\"")
                    if filepath:
                        # Load the conversation
                        chatgpt.conversation = ChatGPTModel.load_conversation(filepath)
                        pp(f"Loaded conversation from {filepath}")
                        continue
                    else:
                        pp("Please provide a filepath to load")
                        continue
                except Exception as e:
                    pp(f"Error loading conversation: {e}")
                    continue

            response = chatgpt.message(prompt)
            pp("\n\n[ChatGPT]")
            pp(response)
            pp("\n")

    except KeyboardInterrupt:
        pp("\n\nGoodbye!\n\n")
        return True

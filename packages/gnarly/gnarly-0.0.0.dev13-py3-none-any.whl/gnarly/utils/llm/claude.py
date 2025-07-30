"""Claude REPL

Entry point for the Claude REPL.
"""
import logging
from datetime import datetime as dt
from pathlib import Path

from ..io import stream
from .interfaces import Claude
from ..llm.models import CLAUDE_CONVERSATIONS_DIR, ClaudeModel


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

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

    Runloop for the Claude REPL.
    """
    exit_commands: list = ["quit", "exit", "q", "e", "x"]
    save_command: str = "save"
    load_command: str = "load"
    is_jupyter = check_for_jupyter()

    # Instantiate the Claude interface
    claude = Claude()

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
                claude.save(save_as=Path(
                    f"{CLAUDE_CONVERSATIONS_DIR}/{dt.now().strftime('%Y-%m-%d_%H%M%S')}.json"
                ))
                pp("Conversation saved!")
                continue

            # Check for load command
            if prompt.lower().startswith(load_command):
                try:
                    # Extract the filepath from the command
                    filepath = prompt[len(load_command):].strip().strip("'\"")
                    if filepath:
                        # Load the conversation
                        claude.conversation = ClaudeModel.load_conversation(filepath)
                        pp(f"Loaded conversation from {filepath}")
                        continue
                    else:
                        pp("Please provide a filepath to load")
                        continue
                except Exception as e:
                    pp(f"Error loading conversation: {e}")
                    continue

            response = claude.message(prompt)[0]["content"]
            pp("\n\n[Claude]")
            pp(response)
            pp("\n")

    except KeyboardInterrupt:
        pp("Goodbye!")
        return True

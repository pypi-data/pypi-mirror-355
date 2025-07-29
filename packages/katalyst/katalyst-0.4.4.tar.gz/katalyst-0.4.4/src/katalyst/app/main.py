import os
import json
from dotenv import load_dotenv
from katalyst.katalyst_core.graph import build_compiled_graph
from katalyst.katalyst_core.utils.logger import get_logger
from katalyst.app.onboarding import welcome_screens
from katalyst.app.config import ONBOARDING_FLAG
from katalyst.katalyst_core.utils.environment import ensure_openai_api_key
from katalyst.app.cli.persistence import load_project_state, save_project_state
from katalyst.app.cli.commands import (
    show_help,
    handle_init_command,
    handle_provider_command,
    handle_model_command,
)
from katalyst.app.katalyst_runner import run_katalyst_task

# Load environment variables from .env file
load_dotenv()


def maybe_show_welcome():
    if not ONBOARDING_FLAG.exists():
        welcome_screens.screen_1_welcome_and_security()
        welcome_screens.screen_2_trust_folder(os.getcwd())
        welcome_screens.screen_3_final_tips(os.getcwd())
        ONBOARDING_FLAG.write_text("onboarded\n")
    else:
        welcome_screens.screen_3_final_tips(os.getcwd())


def handle_init():
    with open("KATALYST.md", "w") as f:
        f.write("# Instructions for Katalyst\n")
    print("KATALYST.md created.")


def repl():
    show_help()
    graph = build_compiled_graph()  # Build the graph once
    project_state = load_project_state()
    while True:
        user_input = input("> ").strip()
        if user_input == "/help":
            show_help()
        elif user_input == "/init":
            handle_init_command(graph)
        elif user_input == "/provider":
            handle_provider_command()
        elif user_input == "/model":
            handle_model_command()
        elif user_input == "/exit":
            print("Goodbye!")
            break
        elif user_input == "":
            continue
        else:
            result = run_katalyst_task(user_input, project_state, graph)
            # Update and save project state after each command
            project_state.update(
                {
                    "chat_history": result.chat_history,  # Persist chat history
                    # TODO: Add more fields to persist as needed
                }
            )
            save_project_state(project_state)


def main():
    ensure_openai_api_key()
    maybe_show_welcome()
    logger = get_logger()
    try:
        repl()
    except Exception as e:
        logger.exception("Unhandled exception in main loop.")
        print(f"An unexpected error occurred: {e}. See the log file for details.")


if __name__ == "__main__":
    main()

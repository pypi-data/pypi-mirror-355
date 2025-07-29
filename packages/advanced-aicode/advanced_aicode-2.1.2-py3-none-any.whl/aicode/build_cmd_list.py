"""aicode - front end for aider"""

import os
import sys
import warnings
from os.path import exists
from typing import Optional

from aicode.aider_control import (
    aider_install,
    aider_installed,
    aider_purge,
    aider_upgrade,
)
from aicode.aider_update_result import AiderUpdateResult
from aicode.args import Args
from aicode.background import background_update_task
from aicode.config import Config
from aicode.models import get_model
from aicode.paths import AIDER_INSTALL_PATH
from aicode.util import check_gitdirectory, open_folder

# This will be at the root of the project, side to the .git directory
_AIDER_HISTORY = ".aider.chat.history.md"

_ENABLE_HISTORY_ASK = False


def aider_install_if_missing() -> None:
    # Set the custom bin path where you want aider to be installed
    # Check if aider is already installed
    if aider_installed():
        return
    aider_install()


def _get_interface_mode(args: Args) -> bool:
    """Returns True for GUI mode, False for CLI mode"""
    if args.gui:
        return True
    if args.cli:
        return False

    while True:
        try:
            answer = input("Select interface:\n  [0] CLI\n  [1] GUI\nChoice [0]: ")
            if answer.strip() == "":
                return False
            choice = int(answer)
            if choice == 0:
                return False
            if choice == 1:
                return True
            print("Please enter 0 or 1")
        except ValueError:
            print("Please enter a valid number (0 or 1)")


def _check_gitignore() -> None:
    needles: dict[str, bool] = {
        ".aider*": False,
        "!.aider.conf.yml": False,
        "!.aiderignore": False,
    }
    if os.path.exists(".gitignore"):
        any_missing = False
        with open(".gitignore", encoding="utf-8", mode="r") as file:
            content = file.read()
            lines = content.split("\n")
            for needle in needles:
                if needle in lines:
                    needles[needle] = True
                else:
                    any_missing = True
                    print(f".gitignore file does not contain {needle}")
        if any_missing:
            resp = input("Add them? [y/N] ")
            if resp.lower() == "y":
                with open(".gitignore", encoding="utf-8", mode="a") as file:
                    for needle, found in needles.items():
                        if not found:
                            file.write("\n" + needle)
    else:
        print(".gitignore file does not exist.")


def _get_lint_command() -> str | None:
    if exists("./lint"):
        return "./lint"
    return None


def _check_aiderignore() -> None:
    """Adds the .aiderignore file if it doesn't exist."""
    if not os.path.exists(".aiderignore"):
        file_content = (
            "# Add files or directories to ignore here\n"
            "\n"
            "run\n"
            "lint\n"
            "test\n"
            "install\n"
            "clean\n"
        )
        with open(".aiderignore", encoding="utf-8", mode="w") as file:
            file.write(file_content)


def build_cmd_list_or_die(args: Args) -> tuple[list[str], Config]:
    unknown_args = args.unknown_args
    # config = Config.load()
    config = Config.load()
    if args.open_aider_path:
        print("Opening the real path to aider.")
        path = AIDER_INSTALL_PATH
        if path is not None:
            print(path)
            open_folder(path)
            sys.exit(0)
        else:
            warnings.warn("aider executable not found")
            sys.exit(1)
    if args.purge:
        print("Purging aider installation")
        aider_purge(path=None, config=config)
        sys.exit(0)

    if args.upgrade:
        aider_upgrade()
        # config["aider_update_info"] = {}  # Purge stale update info
        config.aider_update_info = {}  # Purge stale update info
        config.save()
        sys.exit(0)
    if args.set_key:
        print("Setting openai key")
        # config["openai_key"] = args.set_key
        config.openai_key = args.set_key
        config.save()
        config = Config.load()
    if args.set_anthropic_key:
        print("Setting anthropic key")
        # config["anthropic_key"] = args.set_anthropic_key
        config.anthropic_key = args.set_anthropic_key
        config.save()
        # config = Config.load()
        config = Config.load()
    if args.set_gemini_key:
        print("Setting gemini key")
        config.gemini_key = args.set_gemini_key
        config.save()
        config = Config.load()
    has_git = check_gitdirectory()

    _check_gitignore()
    _check_aiderignore()
    # anthropic_key = config.get("anthropic_key")
    anthropic_key = config.anthropic_key
    # openai_key = config.get("openai_key")
    openai_key = config.openai_key
    gemini_key = config.gemini_key
    model = get_model(args, anthropic_key, openai_key, gemini_key)
    aider_install_if_missing()
    is_anthropic_model = "claude" in model
    is_gemini_model = "gemini" in model or args.gemini

    if is_anthropic_model:
        if anthropic_key is None:
            print("Claude key not found, please set one with --set-anthropic-key")
            sys.exit(1)
        os.environ["ANTHROPIC_API_KEY"] = anthropic_key
    elif is_gemini_model:
        if gemini_key is None:
            print("Gemini key not found, please set one with --set-gemini-key")
            sys.exit(1)
        os.environ["GEMINI_API_KEY"] = gemini_key
    else:
        openai_key = config.openai_key
        if openai_key is None:
            print("OpenAI key not found, please set one with --set-key")
            sys.exit(1)
        os.environ["OPENAI_API_KEY"] = openai_key

    last_aider_update_info: dict[str, str | bool | None] = config.aider_update_info
    update_info: Optional[AiderUpdateResult] = None
    if last_aider_update_info:
        try:
            update_info = AiderUpdateResult.from_json(last_aider_update_info)
            if update_info.error:
                warnings.warn(f"Failed to parse update info: {update_info.error}")
                update_info = None
        except Exception as err:  # pylint: disable=broad-except
            warnings.warn(f"Failed to parse update info: {err}")
            update_info = None

    if update_info is not None and update_info.has_update:
        print(update_info.get_update_msg())

    # Note: Aider no longer uses ChatGPT 3.5 turbo by default. Therefore
    # it may soon no longer be necessary to specify the model.
    os.environ["AIDER_MODEL"] = model
    print(f"Starting aider with model {os.environ['AIDER_MODEL']}")
    use_gui = _get_interface_mode(args)

    if os.path.exists(_AIDER_HISTORY) and _ENABLE_HISTORY_ASK:
        answer = (
            input("Chat history found. Would you like to restore it? [y/N]: ")
            .strip()
            .lower()
        )
        if answer in ("y", "yes"):
            cmd_list = ["aider", "--no-check-update", "--restore-chat-history"]
        else:
            cmd_list = ["aider", "--no-check-update"]
    else:
        cmd_list = ["aider", "--no-check-update"]

    if args.message_file and args.message_file.exists():
        cmd_list.extend(["--message-file", str(args.message_file)])

    if use_gui:
        cmd_list.append("--gui")
    if is_anthropic_model:
        cmd_list.append("--model")
        cmd_list.append("sonnet")
    if args.auto_commit:
        cmd_list.append("--auto-commit")
    else:
        cmd_list.append("--no-auto-commit")  # AIzaSyANavtg9g4BRnK60Lh9WcRHY_BSH9UnIwg
    # New feature to enable architect mode which seems to vastly
    # improve the code editing capatility of the various ai coding models.
    if not args.no_architect:
        cmd_list.append("--architect")
    if args.lint:
        lint_cmd = _get_lint_command()
        if lint_cmd:
            cmd_list.extend(["--lint-cmd", lint_cmd])
        else:
            cmd_list.append("--auto-lint")
    else:
        cmd_list.append("--no-auto-lint")
    if not has_git:
        cmd_list.append("--no-git")
    if not args.no_watch:
        # update_info: AiderUpdateResult | None = config.aider_update_result
        # update_info = aider_fetch_update_status()
        cmd_list.append("--watch")

    cmd_list += args.prompt + unknown_args
    print("\nLoading aider:\n  remember to use /help for a list of commands\n")
    # Perform update in the background.
    _ = background_update_task(config=config)
    return cmd_list, config

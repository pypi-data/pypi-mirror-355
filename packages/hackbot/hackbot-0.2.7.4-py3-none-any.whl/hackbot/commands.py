import argparse
import asyncio
import json
import traceback
import os
import subprocess
from pathlib import Path
from loguru import logger as log
from aiohttp.client_exceptions import ClientPayloadError
from hackbot.utils import get_version
from hackbot.hack import (
    authenticate,
    cli_learn,
    cli_run,
    cli_scope,
    cli_price,
    cli_report,
    HackbotAuthError,
)
from hackbot.cli_args import (
    GREEN,
    RED,
    YELLOW,
    BLUE,
    CYAN,
    GREY,
    BOLD,
    END,
)

from typing import Dict

__version__ = get_version()


def add_common_arguments(parser: argparse.ArgumentParser, hide_dev_tool_help: bool = True):
    """Add common arguments to a parser."""
    parser.add_argument(
        "--auth-only", action="store_true", help="Only verify API key authentication"
    )
    parser.add_argument(
        "-s",
        "--source",
        default=".",
        help=f"Path to folder containing {YELLOW}foundry.toml{END} (default: current directory).",
    )
    parser.add_argument("--output", help="Path to save analysis results")

    def help_mode(description: str):
        if hide_dev_tool_help:
            return argparse.SUPPRESS
        else:
            return description

    parser.add_argument(
        "--debug",
        type=str,
        default=None,
        help=help_mode(
            'Send debug json to server. Can\'t use nested entries. Example: --debug \'{"admin": "true"}\' if you have admin privileges.'
        ),
    )

    parser.add_argument(
        "--local",
        action="store_true",
        help=help_mode("Run with local backend (http://localhost, port 5000)"),
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        help=help_mode("Run with development backend (https://dev-server.hackbot.co, port 443)"),
    )

    parser.add_argument(
        "--skip-forge-build", action="store_true", help=help_mode("Skip forge build check")
    )


def add_learn_arguments(parser: argparse.ArgumentParser):
    """Add learn arguments to a parser."""
    parser.add_argument(
        "--auth-only", action="store_true", help="Only verify API key authentication"
    )
    parser.add_argument(
        "--url",
        type=str,
        required=True,
        help=f"The URL provided by the user, to generate a {YELLOW}checklist.json{END} file, which is used to teach the hackbot about the types of vulnerabilities to look out for.",
    )
    parser.add_argument(
        "--merge", action="store_true", help="Merge the new checklist with the existing one"
    )
    parser.add_argument("--debug", type=str, default=None, help=argparse.SUPPRESS)


def add_api_key_argument(parser: argparse.ArgumentParser):
    """Add API key argument to a parser."""
    parser.add_argument(
        "--api-key",
        default=os.getenv("HACKBOT_API_KEY"),
        help=f"API key for authentication (default: {BLUE}HACKBOT_API_KEY{END} environment variable)",
    )


def learn_run(args: argparse.Namespace) -> int:
    """Run the learn command."""
    if not args.api_key:
        log.error("❌ Error: API key is required")
        return 1

    if not args.url:
        log.error("❌ Error: URL is required")
        return 1

    auth_status = asyncio.run(authenticate(args.api_key))
    if auth_status is not None:
        log.error(
            f"❌ Authentication failed with error: {auth_status.message}. Please check your API key {BLUE}HACKBOT_API_KEY{RED} is set, and is valid. If you do not have an API key, please sign up at {GREEN}https://hackbot.co{RED} before running hackbot."
        )
        return 1
    log.info("✅ Authentication successful")

    if args.auth_only:
        return 0

    asyncio.run(
        cli_learn(
            api_key=args.api_key,
            user_url=args.url,
            merge=args.merge,
        )
    )
    return 0


def get_bool_choice(quiet: bool = False) -> bool:
    """Prompts the user to enter a yes or no response.
    Returns True if the user enters y, otherwise False."""
    if quiet:
        return True
    while True:
        choice = input(f"\n{BLUE}Enter your choice [Y/n] (default: Y):{END} ").strip().lower()
        if choice and choice[0] in ["y", "n"]:
            return choice[0] == "y"
        elif choice == "":
            log.info("Going with default choice (Yes)")
            return True
        log.warning(
            "Please enter either a positive (starting with y) or negative (starting with n) response"
        )
    raise ValueError("Invalid point in program")


def handle_missing_scope_file(quiet: bool) -> bool:
    """Prompts the user to let hackbot automatically generate scope.txt or manually change scope.txt.
    Returns whether the user wants hackbot to automatically generate scope.txt."""
    log.info(f"\n❌ No {RED}scope.txt{END} found in your project.")
    log.info("\nDo you want to let hackbot automatically generate scope.txt?")
    log.info(f"1) {GREY}Yes (let hackbot automatically generate scope.txt){END}")
    log.info(f"2) {GREY}No (manually change scope.txt{END}")

    choice = get_bool_choice(quiet=quiet)

    if not choice:
        log.info(f"\n{BLUE}📝 Next steps:{END}")
        log.info(f"1. Run {CYAN}hackbot scope{END} to generate scope.txt")
        log.info(f"2. Edit {CYAN}scope.txt{END} to customize which files to analyze")
        log.info(f"3. Run {CYAN}hackbot run{END} again to start analysis")
        return False
    else:
        return True


def ensure_scope_file(args: argparse.Namespace) -> bool:
    """Ensure that scope.txt exists."""
    scope_file = Path(args.source) / "scope.txt"
    if not scope_file.exists():
        auto_run = hasattr(args, "quiet") and args.quiet
        if auto_run or handle_missing_scope_file(quiet=args.quiet):
            log.info(
                f"No {RED}scope.txt{END} found in your project. Running {CYAN}hackbot scope{END} now to generate one..."
            )
            asyncio.run(
                cli_scope(
                    invocation_args={},
                    api_key=args.api_key,
                    source_path=args.source,
                    output=args.output,
                    show_success_message=False,
                )
            )
            if not scope_file.exists():
                log.error(f"❌ Error: Failed to generate {RED}scope.txt{END}.")
                return False

            def format_scope_file(scope_file: str) -> str:
                # Takes one line from scopefile, produces nice info entry about file
                scopefile_realpath = Path(args.source) / scope_file
                with open(scopefile_realpath, "r") as f:
                    n_lines = len(f.readlines())
                return f"{GREY}{scope_file}{END} ({n_lines} lines)"

            # Display contents of scope.txt in a pretty way (bolded list of each line in the scope_file, also line-count for each file)
            log.info(f"{BOLD}Scope.txt:{END}")
            with open(scope_file, "r") as f:
                for line_index, line in enumerate(f.readlines()):
                    log.info(f"{BOLD}{line_index + 1}. {format_scope_file(line.strip())}{END}")

            log.info(f"Do you want to proceed with the {RED}scope.txt{END} file as above?")

            choice = get_bool_choice(quiet=args.quiet)
            if not choice:
                log.info("❌ Scope.txt confirmation failed. Exiting.")
                return False

            log.info("✅ Confirmed scope.txt.")
        else:
            return False
    return True


def price_run(args: argparse.Namespace) -> tuple[int, int]:
    """Run the price command.
    This also happens implicitly in hackbot run."""

    # Verify authentication
    auth_status = asyncio.run(authenticate(args.api_key))
    if auth_status is not None:
        log.error(
            f"❌ Authentication failed with error: {auth_status.message}. Please check your API key {BLUE}HACKBOT_API_KEY{RED} is set, and is valid. If you do not have an API key, please sign up at {GREEN}https://hackbot.co{RED} before running hackbot."
        )
        return 1, -1

    log.info("✅ Authentication successful")

    if args.auth_only:
        return 0, -1

    # Ensure scope.txt exists, same as in hackbot_run
    if not ensure_scope_file(args):
        log.error("❌ Error: No scope.txt. Exiting.")
        return 1, -1

    # Get the pricing information
    actual_price = asyncio.run(
        cli_price(
            api_key=args.api_key,
            source_path=args.source,
        )
    )
    if actual_price is None:
        log.error("❌ Error: Price run failed. Exiting.")
        return 1, -1

    return 0, actual_price


def confirm_price(args: argparse.Namespace) -> bool:
    """Confirm that the hackbot run, with the stated price."""
    # If --quiet, just proceed
    if hasattr(args, "quiet") and args.quiet:
        return True

    log.info(
        "Do you want to proceed with the run at the stated base fee price "
        "(you will not be charged additionally if we don't find high/medium severity vulnerabilities) "
        "according to https://docs.hackbot.co/docs/pricing?"
    )
    choice = get_bool_choice(quiet=args.quiet)
    if not choice:
        log.info("❌ Price confirmation failed. Exiting.")
        return False
    else:
        log.info("✅ Price confirmed. Proceeding with the run.")
        return True


def ensure_forge_build(args: argparse.Namespace) -> bool:
    """Ensure that normal `forge build` works locally."""
    if args.skip_forge_build:
        log.info("Skipping forge build check.")
        return True
    log.info(
        f"Running {GREEN}forge build{END} in source folder {args.source} to ensure it works locally..."
    )
    log.info(f"{GREY}----------   Output of forge build   ----------{END}")
    forge_build_works: int = subprocess.run(
        ["forge", "build"], check=False, cwd=args.source
    ).returncode
    log.info(f"{GREY}---------- End of forge build output ----------{END}")
    if forge_build_works != 0:
        log.info(f" Forge build returned non-zero exit code {forge_build_works}.")
        return False
    return True


def report_run(args: argparse.Namespace) -> int:
    """Run the report command."""
    try:
        # Verify authentication
        auth_result = asyncio.run(authenticate(args.api_key))
        if isinstance(auth_result, HackbotAuthError):
            log.error(f"❌ Error: {auth_result.message}")
            return 1

        if not args.session:
            log.error("❌ Error: Session name is required")
            return 1

        log.info(f"{BLUE}Generating report for session {args.session}...{END}")

        # Add invocation args setup
        invocation_args: Dict[str, str] = {"session_name": args.session}

        if args.debug is not None:
            log.info(f"Debug mode, sending (flat, since only using http forms): {args.debug}")
            for key, value in args.debug.items():
                invocation_args[key] = value

        # Generate the report
        results = asyncio.run(
            cli_report(
                api_key=args.api_key,
                invocation_args=invocation_args,
                output=args.output,
            )
        )

        # Output results to output-path
        if args.output and results:
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2)

        return 0

    except KeyboardInterrupt:
        log.info("\n❌ Report generation cancelled by user")
        return 1
    except Exception:
        log.error(f"❌ Error: {traceback.format_exc()}")
        return 1


def scope_run(args: argparse.Namespace) -> int:
    """Run the scope command."""
    try:
        # Add invocation args setup
        invocation_args: Dict[str, str] = {}

        if args.debug is not None:
            log.info(f"Debug mode, sending (flat, since only using http forms): {args.debug}")
            for key, value in args.debug.items():
                invocation_args[key] = value

        log.info(
            f"{BLUE}Starting scope analysis... Press {CYAN}Ctrl+C{BLUE} to cancel at any time{END}"
        )
        # Add only_dir to invocation args if specified
        if hasattr(args, "only_dir") and args.only_dir:
            invocation_args["only_dir"] = args.only_dir
        # Perform the scope analysis
        results = asyncio.run(
            cli_scope(
                invocation_args=invocation_args,
                api_key=args.api_key,
                source_path=args.source,
                output=args.output,
            )
        )
        # Output results to output-path
        if args.output and results:
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2)
    except ClientPayloadError:
        log.error(
            "❌ The server terminated the connection prematurely, most likely due to an error in the scanning process. Check the streamed logs for error messages. Support: support@gatlingx.com"
        )
        return 1
    except Exception as e:
        if str(e) == "Hack request failed: 413":
            log.error(
                "❌ The source code directory is too large to be scanned. Must be less than 256MB."
            )
            return 1
        else:
            raise e
    return 0


def hackbot_run(args: argparse.Namespace) -> int:
    """Run the hackbot tool."""

    # Ensure normal `forge build` works locally.
    forge_build_works: bool = ensure_forge_build(args)
    if not forge_build_works:
        log.error("❌ Error: Forge build failed. Exiting.")
        return 1

    price_ret, actual_price = price_run(args)
    if price_ret != 0:
        return price_ret

    # Confirm that the hackbot run, with the stated price.
    if not confirm_price(args):
        return 1

    try:
        # Add invocation args setup
        invocation_args: Dict[str, str] = {}

        if args.debug is not None:
            log.info(f"Debug mode, sending (flat, since only using http forms): {args.debug}")
            for key, value in args.debug.items():
                invocation_args[key] = value

        log.info(f"{BLUE}Starting analysis... Press {CYAN}Ctrl+C{BLUE} to cancel at any time{END}")
        # The only values of command that can be here are run and scope
        # Perform the bug analysis
        results = asyncio.run(
            cli_run(
                invocation_args=invocation_args,
                api_key=args.api_key,
                source_path=args.source,
                output=args.output,
                checklist=args.checklist,
                actual_price=actual_price,
            )
        )

        # Output results to output-path
        if args.output and results:
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2)

        return 0

    except ClientPayloadError:
        log.error(
            "❌ The server terminated the connection prematurely, most likely due to an error in the scanning process. Check the streamed logs for error messages. Support: support@gatlingx.com"
        )
        return 1
    except Exception as e:
        if str(e) == "Hack request failed: 413":
            log.error(
                "❌ The source code directory is too large to be scanned. Must be less than 256MB."
            )
            return 1
        else:
            raise e

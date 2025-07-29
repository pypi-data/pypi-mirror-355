#!/usr/bin/env python3

import subprocess
import argparse
import sys
import os
import json

CONFIG_DIR = os.path.expanduser("~/.mmtsp")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

def ensure_config_exists():
    if not os.path.exists(CONFIG_FILE):
        print("Error: Prefix is not set. Use '--set-prefix \"YOUR_PREFIX\"' to configure it.", file=sys.stderr)
        sys.exit(1)

def save_config(prefix_value):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(
            {
                "prefix": prefix_value
            },
            f
        )
    print(f"Prefix successfully set to: '{prefix_value}'")

def load_config():
    ensure_config_exists()
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
        return config

def get_modified_files():
    try:
        result = subprocess.run(["mmt", "status"], capture_output=True, text=True, check=True)
        files = result.stdout.strip().splitlines()
        formatted_files = '\n'.join(f" - {file}" for file in files)
        return formatted_files
    except subprocess.CalledProcessError as e:
        print("Error: Failed to get modified files from 'mmt status'.", file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        sys.exit(1)

def generate_sri():
    try:
        subprocess.run(["mmt", "sri", "-5", "-2", "-3"], check=True)
    except subprocess.CalledProcessError as e:
        print(e.stderr, file=sys.stderr)
        sys.exit(1)

def push_changes(full_message):
    try:
        subprocess.run(["mmt", "push", "-n", full_message], check=True)
    except subprocess.CalledProcessError as e:
        print("Error: Failed to push changes with 'mmt push'.", file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="MMTSP: Automate mmt sri and push commands with commit message and prefix."
    )
    # available options:
    # -m, --message: Custom commit message
    # --set-prefix: Set prefix value and save it
    # --prefix: Use prefix from argument
    # --no-sri: Skip SRI generation
    parser.add_argument("-m", "--message", type=str, help="Custom commit message", default="Changes with no message")
    parser.add_argument("--set-prefix", type=str, help="Set prefix value and save it")
    parser.add_argument("--prefix", type=str, help="Use prefix from argument")
    parser.add_argument("--no-sri", action="store_true", help="Skip SRI generation")

    args = parser.parse_args()

    #if set-prefix is provided, save the prefix to the config and exit
    if args.set_prefix:
        save_config(args.set_prefix)
        sys.exit(0)


    # otherwise, get the prefix from the config and use it as the commit message
    config = load_config()

    prefix = args.prefix or config.get("prefix", "")

    # generate the SRI hashes
    if not args.no_sri:
        generate_sri()

    # get the modified files from mmt status command
    modified_files = get_modified_files()

    #generate the full message
    full_message = f"{prefix}{args.message}\nModified files:\n{modified_files}"

    #push the changes
    push_changes(full_message)

if __name__ == "__main__":
    main()
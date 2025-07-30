#!/usr/bin/env python3

import subprocess
import argparse
import sys
import os
import json

CONFIG_DIR = os.path.expanduser("~/.gdmmt")
GLOBAL_CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

########################################################
################### helper functions ###################
########################################################

def ensure_config_exists():
    if not os.path.exists(GLOBAL_CONFIG_FILE):
        print("Error: Prefix is not set. Use 'gdmmt push --set-prefix \"YOUR_PREFIX\"' to configure it.", file=sys.stderr)
        sys.exit(1)

def save_config(prefix_value):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(GLOBAL_CONFIG_FILE, "w") as f:
        json.dump(
            {
                "prefix": prefix_value
            },
            f
        )
    print(f"Prefix successfully set to: '{prefix_value}'")

def load_config():
    ensure_config_exists()
    with open(GLOBAL_CONFIG_FILE, "r") as f:
        config = json.load(f)
        return config

def format_modified_files_str(str):
    stripped_str = str.strip()
    if stripped_str == "No files modified":
        return stripped_str

    files = stripped_str.splitlines()
    formatted_files = '\n'.join(f" - {file}" for file in files)
    return formatted_files

def format_note(note, modified_files, prefix="", version=None):
    return (
        f"{prefix}{note}\n\nModified files:\n{modified_files}"
        + (f"\n\nVersion: {version}" if version else "")
    )

########################################################
################### mmt commands #######################
########################################################

def mmt_status():
    try:
        return subprocess.run(["mmt", "status"], capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(e.stderr.strip(), file=sys.stderr)
        sys.exit(1)

def mmt_sri(sha512, sha256, sha384):
    try:
        return subprocess.run(["mmt", "sri", "-5" if sha512 else "", "-2" if sha256 else "", "-3" if sha384 else ""], capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(e.stderr.strip(), file=sys.stderr)
        sys.exit(1)

def mmt_pull():
    try:
        return subprocess.run(["mmt", "pull"], capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(e.stderr.strip(), file=sys.stderr)
        sys.exit(1)

def mmt_push(note):
    try:
        return subprocess.run(["mmt", "push", "-n", note], capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(e.stderr.strip(), file=sys.stderr)
        sys.exit(1)

def mmt_checkout(remote):
    if not remote:
        print("Error: Remote is not provided. Use 'gdmmt checkout <remote>' to checkout a remote.", file=sys.stderr)
        sys.exit(1)

    try:
        return subprocess.run(["mmt", "checkout", remote], capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(e.stderr.strip(), file=sys.stderr)
        sys.exit(1)

def mmt_info():
    try:
        return subprocess.run(["mmt", "info"], capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(e.stderr.strip(), file=sys.stderr)
        sys.exit(1)


########################################################
################### cli commands #######################
########################################################

def status(args):
    modified_files = format_modified_files_str(mmt_status().stdout)

    print(modified_files)

def push(args):
    #if set-prefix is provided, save the prefix to the config and exit
    if args.set_prefix:
        save_config(args.set_prefix)
        sys.exit(0)

    # otherwise, get the prefix from the config and use it as the commit message
    config = load_config()

    prefix = args.prefix or config.get("prefix", "")

    # generate the SRI hashes
    if not args.no_sri:
        mmt_sri(args.sha512, args.sha256, args.sha384)

    # get the modified files from mmt status command
    modified_files = format_modified_files_str(mmt_status().stdout)

    #generate the full note
    full_note = format_note(args.note, modified_files, prefix, args.version)

    #push the changes
    print(mmt_push(full_note).stdout.strip())

def pull(args):
    print(mmt_pull().stdout.strip())

def checkout(args):
    mmt_checkout(args.remote)

def info(args):
    print(mmt_info().stdout.strip())


########################################################
################### main function ######################
########################################################

def main():
    parser = argparse.ArgumentParser(
        description="""
        GD MMT: Extended version of mmt cli. Handles SRI generation, prefix management, versioning, and commit message generation.
        """
    )

    parser.add_argument("command", choices=["push", "status", "pull", "checkout", "info"], help="Command to execute")

    # push command options
    parser.add_argument("-n", "--note", type=str, help="Custom commit note", default="Changes with no note")
    parser.add_argument("-v", "--version", type=str, help="Set version")
    parser.add_argument("--set-prefix", type=str, help="Set prefix value and save it")
    parser.add_argument("--prefix", type=str, help="Use prefix from argument")
    parser.add_argument("--no-sri", action="store_true", help="Skip SRI generation")
    parser.add_argument("--sha512", action="store_true", help="Generate SHA512 SRI (default True)", default=True)
    parser.add_argument("--sha256", action="store_true", help="Generate SHA256 SRI (default True)", default=True)
    parser.add_argument("--sha384", action="store_true", help="Generate SHA384 SRI (default True)", default=True)

    # checkout command options
    parser.add_argument("remote", type=str, nargs="?", help="Remote to checkout")

    args = parser.parse_args()

    match args.command:
        case "push":
            push(args)
        case "status":
            status(args)
        case "pull":
            pull(args)
        case "checkout":
            checkout(args)
        case "info":
            info(args)

if __name__ == "__main__":
    main()
import argparse
import json
import os
import sys
import getpass
import pyperclip
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm
from rich.prompt import Prompt

from zvault.crypto import encrypt, decrypt

console = Console()
VAULT_FILE = "vault.zvault"


def load_vault(passphrase):
    if not os.path.exists(VAULT_FILE):
        return {}
    try:
        with open(VAULT_FILE, "rb") as f:
            encrypted = f.read()
        decrypted = decrypt(encrypted, passphrase)
        return json.loads(decrypted.decode())
    except Exception as e:
        console.print(f"[red]Failed to load vault: {e}[/red]")
        sys.exit(1)


def save_vault(vault, passphrase):
    data = json.dumps(vault).encode()
    encrypted = encrypt(data, passphrase)
    with open(VAULT_FILE, "wb") as f:
        f.write(encrypted)


def prompt_passphrase(confirm=False):
    while True:
        pw = getpass.getpass("Enter master passphrase: ")
        if confirm:
            pw2 = getpass.getpass("Confirm passphrase: ")
            if pw != pw2:
                console.print("[red]Passphrases do not match. Try again.[/red]")
                continue
        if len(pw) < 8:
            console.print("[red]Passphrase too short (min 8 chars). Try again.[/red]")
            continue
        return pw


def cmd_init(args):
    if os.path.exists(VAULT_FILE):
        if not Confirm.ask("Vault exists. Overwrite?"):
            console.print("[yellow]Init aborted.[/yellow]")
            return
    pw = prompt_passphrase(confirm=True)
    save_vault({}, pw)
    console.print("[green]Vault initialized and encrypted.[/green]")


def cmd_add(args):
    pw = prompt_passphrase()
    vault = load_vault(pw)
    if args.name in vault:
        if not Confirm.ask(f"Entry '{args.name}' exists. Overwrite?"):
            console.print("[yellow]Add aborted.[/yellow]")
            return
    username = Prompt.ask("Username", default="")
    password = Prompt.ask("Password", default="", password=True)
    notes = Prompt.ask("Notes", default="")
    vault[args.name] = {
        "username": username,
        "password": password,
        "notes": notes,
        "tags": [],
    }
    save_vault(vault, pw)
    console.print(f"[green]Entry '{args.name}' saved.[/green]")


def cmd_get(args):
    pw = prompt_passphrase()
    vault = load_vault(pw)
    entry = vault.get(args.name)
    if not entry:
        console.print(f"[red]No entry named '{args.name}' found.[/red]")
        return
    table = Table(title=f"Entry: {args.name}")
    table.add_column("Field")
    table.add_column("Value")
    for k, v in entry.items():
        table.add_row(k, v if isinstance(v, str) else str(v))
    console.print(table)
    if Confirm.ask("Copy password to clipboard?"):
        pyperclip.copy(entry.get("password", ""))
        console.print("[green]Password copied. Clipboard will clear in 30 seconds.[/green]")
        import threading, time
        def clear_clipboard():
            time.sleep(30)
            pyperclip.copy("")
        threading.Thread(target=clear_clipboard, daemon=True).start()


def cmd_list(args):
    pw = prompt_passphrase()
    vault = load_vault(pw)
    if not vault:
        console.print("[yellow]Vault is empty.[/yellow]")
        return
    table = Table(title="Stored Entries")
    table.add_column("Name", style="cyan")
    table.add_column("Username")
    for name, entry in vault.items():
        table.add_row(name, entry.get("username", ""))
    console.print(table)


def cmd_delete(args):
    pw = prompt_passphrase()
    vault = load_vault(pw)
    if args.name not in vault:
        console.print(f"[red]No entry named '{args.name}' found.[/red]")
        return
    if Confirm.ask(f"Delete entry '{args.name}'?"):
        del vault[args.name]
        save_vault(vault, pw)
        console.print(f"[green]Entry '{args.name}' deleted.[/green]")
    else:
        console.print("[yellow]Delete aborted.[/yellow]")


def cmd_passwd(args):
    old_pw = prompt_passphrase()
    vault = load_vault(old_pw)
    new_pw = prompt_passphrase(confirm=True)
    save_vault(vault, new_pw)
    console.print("[green]Master passphrase changed.[/green]")


def main():
    parser = argparse.ArgumentParser(prog="zvault", description="Secure password + key vault")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Create new encrypted vault")
    add_p = sub.add_parser("add", help="Add a password or secret")
    add_p.add_argument("name", help="Entry name")

    get_p = sub.add_parser("get", help="Retrieve and decrypt an entry")
    get_p.add_argument("name", help="Entry name")

    del_p = sub.add_parser("delete", help="Delete an entry")
    del_p.add_argument("name", help="Entry name")

    sub.add_parser("list", help="Show all stored entries")
    sub.add_parser("passwd", help="Change vault master passphrase")

    args = parser.parse_args()

    if args.command == "init":
        cmd_init(args)
    elif args.command == "add":
        cmd_add(args)
    elif args.command == "get":
        cmd_get(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "delete":
        cmd_delete(args)
    elif args.command == "passwd":
        cmd_passwd(args)


if __name__ == "__main__":
    main()

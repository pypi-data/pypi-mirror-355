import json
import os
from getpass import getpass
import pyotp
from rich.console import Console
from rich.prompt import Prompt

console = Console()

VAULT_FILE = os.path.expanduser("~/.zvault")

def prompt_passphrase():
    return getpass("Vault passphrase: ")

def load_vault(passphrase):
    if not os.path.exists(VAULT_FILE):
        return {}
    with open(VAULT_FILE, "rb") as f:
        encrypted = f.read()
    # TODO: Replace with your actual decrypt logic
    decrypted = encrypted.decode("utf-8")  # placeholder
    vault = json.loads(decrypted)
    return vault

def save_vault(vault, passphrase):
    data = json.dumps(vault)
    # TODO: Replace with your actual encrypt logic
    encrypted = data.encode("utf-8")  # placeholder
    with open(VAULT_FILE, "wb") as f:
        f.write(encrypted)

def cmd_init(args):
    pw = prompt_passphrase()
    if os.path.exists(VAULT_FILE):
        console.print("[red]Vault already exists! Use another filename or delete first.[/red]")
        return
    save_vault({}, pw)
    console.print("[green]New vault created.[/green]")

def cmd_add(args):
    pw = prompt_passphrase()
    vault = load_vault(pw)
    if args.name in vault:
        console.print(f"[yellow]Warning: Overwriting existing entry '{args.name}'.[/yellow]")
    entry = {
        "username": args.username or "",
        "password": args.password or "",
        "notes": args.notes or "",
        "tags": args.tags or []
    }
    vault[args.name] = entry
    save_vault(vault, pw)
    console.print(f"[green]Entry '{args.name}' added/updated.[/green]")

def cmd_get(args):
    pw = prompt_passphrase()
    vault = load_vault(pw)
    entry = vault.get(args.name)
    if not entry:
        console.print(f"[red]No entry named '{args.name}' found.[/red]")
        return
    console.print_json(json.dumps(entry, indent=2))

def cmd_list(args):
    pw = prompt_passphrase()
    vault = load_vault(pw)
    names = list(vault.keys())
    if not names:
        console.print("[yellow]Vault is empty.[/yellow]")
        return
    for name in names:
        console.print(f"- {name}")

def cmd_delete(args):
    pw = prompt_passphrase()
    vault = load_vault(pw)
    if args.name not in vault:
        console.print(f"[red]No entry named '{args.name}' found.[/red]")
        return
    del vault[args.name]
    save_vault(vault, pw)
    console.print(f"[green]Entry '{args.name}' deleted.[/green]")

def cmd_passwd(args):
    old_pw = prompt_passphrase()
    vault = load_vault(old_pw)
    new_pw = getpass("New vault passphrase: ")
    confirm_pw = getpass("Confirm new passphrase: ")
    if new_pw != confirm_pw:
        console.print("[red]Passphrases do not match![/red]")
        return
    save_vault(vault, new_pw)
    console.print("[green]Vault passphrase changed successfully.[/green]")

# --- TOTP commands ---

def cmd_totp_add(args):
    pw = prompt_passphrase()
    vault = load_vault(pw)
    entry = vault.get(args.name)
    if not entry:
        console.print(f"[red]No entry named '{args.name}' found.[/red]")
        return
    secret = Prompt.ask("Enter TOTP secret (base32)")
    entry["totp_secret"] = secret.strip().replace(" ", "")
    vault[args.name] = entry
    save_vault(vault, pw)
    console.print(f"[green]TOTP secret added to '{args.name}'.[/green]")

def cmd_totp_get(args):
    pw = prompt_passphrase()
    vault = load_vault(pw)
    entry = vault.get(args.name)
    if not entry:
        console.print(f"[red]No entry named '{args.name}' found.[/red]")
        return
    secret = entry.get("totp_secret")
    if not secret:
        console.print(f"[yellow]No TOTP secret found for '{args.name}'.[/yellow]")
        return
    totp = pyotp.TOTP(secret)
    code = totp.now()
    console.print(f"[green]Current TOTP code for '{args.name}':[/green] [bold]{code}[/bold]")

# --- Main CLI parser ---

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Zvault password manager")
    sub = parser.add_subparsers(dest="command", required=True)

    # Password management commands
    init_p = sub.add_parser("init", help="Create new encrypted vault")

    add_p = sub.add_parser("add", help="Add or update a vault entry")
    add_p.add_argument("name", help="Entry name")
    add_p.add_argument("--username", help="Username or login")
    add_p.add_argument("--password", help="Password or secret")
    add_p.add_argument("--notes", help="Additional notes")
    add_p.add_argument("--tags", nargs="*", help="Tags (space separated)")

    get_p = sub.add_parser("get", help="Retrieve and show an entry")
    get_p.add_argument("name", help="Entry name")

    list_p = sub.add_parser("list", help="List all stored entry names")

    delete_p = sub.add_parser("delete", help="Delete an entry")
    delete_p.add_argument("name", help="Entry name")

    passwd_p = sub.add_parser("passwd", help="Change vault master passphrase")

    # TOTP commands
    totp_p = sub.add_parser("totp", help="TOTP commands")
    totp_sub = totp_p.add_subparsers(dest="totp_cmd", required=True)

    totp_add_p = totp_sub.add_parser("add", help="Add or update TOTP secret for entry")
    totp_add_p.add_argument("name", help="Entry name")

    totp_get_p = totp_sub.add_parser("get", help="Show current TOTP code")
    totp_get_p.add_argument("name", help="Entry name")

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
    elif args.command == "totp":
        if args.totp_cmd == "add":
            cmd_totp_add(args)
        elif args.totp_cmd == "get":
            cmd_totp_get(args)

if __name__ == "__main__":
    main()

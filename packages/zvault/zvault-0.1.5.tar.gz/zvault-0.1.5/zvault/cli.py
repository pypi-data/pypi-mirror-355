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
    # Simulate decrypt - replace with your encryption logic
    decrypted = encrypted.decode("utf-8")  # placeholder
    vault = json.loads(decrypted)
    return vault

def save_vault(vault, passphrase):
    data = json.dumps(vault)
    # Simulate encrypt - replace with your encryption logic
    encrypted = data.encode("utf-8")  # placeholder
    with open(VAULT_FILE, "wb") as f:
        f.write(encrypted)

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

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Zvault password manager")
    sub = parser.add_subparsers(dest="command", required=True)

    # Add totp commands
    totp_p = sub.add_parser("totp", help="TOTP commands")
    totp_sub = totp_p.add_subparsers(dest="totp_cmd", required=True)

    totp_add_p = totp_sub.add_parser("add", help="Add or update TOTP secret for entry")
    totp_add_p.add_argument("name", help="Entry name")

    totp_get_p = totp_sub.add_parser("get", help="Show current TOTP code")
    totp_get_p.add_argument("name", help="Entry name")

    args = parser.parse_args()

    if args.command == "totp":
        if args.totp_cmd == "add":
            cmd_totp_add(args)
        elif args.totp_cmd == "get":
            cmd_totp_get(args)

if __name__ == "__main__":
    main()

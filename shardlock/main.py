import typer
import time
import os
from pathlib import Path
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

# Importiamo tutto da utils e crypto
from shardlock.utils import console, clean_path, show_banner, startup_sequence, show_protocol_overview
from shardlock import crypto

app = typer.Typer()

def interactive_menu():
    console.clear()
    show_banner()
    
    menu_table = Table(box=None, show_header=False, pad_edge=False)
    menu_table.add_row("[bold cyan][1][/bold cyan]", "🔐 [bold white]ENCRYPT NEW ASSET[/bold white]")
    menu_table.add_row("[bold magenta][2][/bold magenta]", "🔓 [bold white]DECRYPT & RECONSTRUCT[/bold white]")
    menu_table.add_row("[bold yellow][3][/bold yellow]", "📖 [bold white]PROTOCOL OVERVIEW[/bold white]")
    menu_table.add_row("[bold red][4][/bold red]", "🚪 [dim white]EXIT SYSTEM[/dim white]")
    
    console.print(Panel(menu_table, title="[bold]COMMAND CENTER[/bold]", border_style="bright_blue", expand=False))
    
    choice = Prompt.ask("\n[bold]Select Option[/bold]", choices=["1", "2", "3", "4"], default="1")

    if choice == "1":
        run_encrypt_flow()
    elif choice == "2":
        run_decrypt_flow()
    elif choice == "3":
        show_protocol_overview()
        interactive_menu() # Torna al menu dopo la spiegazione
    else:
        console.print("[italic red]ShardLock offline. Connection terminated.[/italic red]")

def run_encrypt_flow():
    path_str = Prompt.ask("\n[bold]📂 Drag & drop the file to protect[/bold]")
    file_path = clean_path(path_str)

    if not file_path.exists():
        console.print(f"[red]❌ Error: Resource not found at: {file_path}[/red]")
        time.sleep(2)
        interactive_menu()
        return

    n = IntPrompt.ask("👥 Total number of shards to generate (n)", default=5)
    k = IntPrompt.ask("🔑 Minimum threshold for reconstruction (k)", default=3)
    
    if k > n:
        console.print("[red]⚠ Error: Threshold (k) cannot exceed total shards (n)![/red]")
        return

    password = Prompt.ask("🔐 Master Password", password=True)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=None, style="magenta", complete_style="cyan"),
        TaskProgressColumn(),
        console=console
    ) as progress:
        progress.add_task("[cyan]Fragmenting asset...", total=None)
        
        salt = os.urandom(16)
        key = crypto.derive_key(password, salt)
        with open(file_path, "rb") as f:
            data = f.read()
        nonce, ciphertext = crypto.encrypt_data(data, key)
        
        slock_path = file_path.with_suffix(file_path.suffix + ".slock")
        with open(slock_path, "wb") as f:
            f.write(salt + nonce + ciphertext)

        shares = crypto.split_key(key, n, k)
        shares_dir = file_path.parent / f"{file_path.stem}_shares"
        shares_dir.mkdir(exist_ok=True)
        for idx, share_data in shares:
            with open(shares_dir / f"share_{idx}.shard", "wb") as f:
                f.write(idx.to_bytes(1, 'big') + share_data)
        
        time.sleep(1)

    res_table = Table(show_header=False, box=None)
    res_table.add_row("🔒 [bold]Vault Created:[/bold]", f"[cyan]{slock_path.name}[/cyan]")
    res_table.add_row("🧩 [bold]Shards Exported:[/bold]", f"[magenta]{shares_dir.name}/[/magenta]")
    console.print(Panel(res_table, title="🛡️ Security Protocol Active", border_style="green"))
    Prompt.ask("\nPress Enter to return to Command Center")
    interactive_menu()

def run_decrypt_flow():
    path_str = Prompt.ask("\n[bold]📂 Drag the .slock vault file[/bold]")
    slock_path = clean_path(path_str)
    
    dir_str = Prompt.ask("[bold]🧩 Drag the shards folder[/bold]")
    shares_dir = clean_path(dir_str)

    if not slock_path.exists() or not shares_dir.exists():
        console.print("[red]❌ Resources not found. Check paths.[/red]")
        time.sleep(2)
        interactive_menu()
        return

    found_shares = []
    for share_file in shares_dir.glob("*.shard"):
        with open(share_file, "rb") as f:
            raw = f.read()
            found_shares.append((int(raw[0]), raw[1:]))

    console.print(f"🔍 [bold cyan]{len(found_shares)}[/bold cyan] valid shards detected.")
    
    try:
        with console.status("[bold magenta]Reassembling molecular key structure...") as status:
            recovered_key = crypto.recover_key(found_shares, k=len(found_shares))
            with open(slock_path, "rb") as f:
                salt, nonce, ciphertext = f.read(16), f.read(12), f.read()
            decrypted_data = crypto.decrypt_data(ciphertext, recovered_key, nonce)
            
            original_stem = slock_path.stem
            output_path = slock_path.parent / (original_stem + "_restored" + Path(original_stem).suffix)
            with open(output_path, "wb") as f:
                f.write(decrypted_data)
        
        console.print(f"\n[bold green]🔓 ACCESS GRANTED![/bold green] Asset restored: {output_path.name}")
    except Exception:
        console.print(f"\n[bold red]❌ ACCESS DENIED.[/bold red] Polynomial reconstruction failed.")
    
    Prompt.ask("\nPress Enter to return to Command Center")
    interactive_menu()

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        startup_sequence() # Mostra l'animazione solo al primo avvio
        interactive_menu()

if __name__ == "__main__":
    app()
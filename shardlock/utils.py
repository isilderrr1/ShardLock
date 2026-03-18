import time
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
from rich.live import Live
from rich.prompt import Prompt

# Inizializziamo la console qui per esportarla
console = Console()

def clean_path(raw_path: str) -> Path:
    """Pulisce il percorso dai residui di PowerShell (&, virgolette, spazi)."""
    p = raw_path.strip()
    if p.startswith('&'): p = p[1:].strip()
    p = p.replace('"', '').replace("'", "")
    return Path(p)

def show_banner():
    """Mostra il banner ASCII principale."""
    ascii_art = """
   ███████╗██╗  ██╗ █████╗ ██████╗ ██████╗ ██╗      ██████╗  ██████╗██╗  ██╗
   ██╔════╝██║  ██║██╔══██╗██╔══██╗██╔══██╗██║     ██╔═══██╗██╔════╝██║ ██╔╝
   ███████╗███████║███████║██████╗ ██║  ██║██║     ██║   ██║██║     █████  
   ╚════██║██╔══██║██╔══██║██╔══██╗██║  ██║██║     ██║   ██║██║     ██╔═██╗
   ███████║██║  ██║██║  ██║██║  ██║██████╔╝███████╗╚██████╔╝╚██████╗██║  ██╗
   ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚══════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝
    """
    banner_text = Text(ascii_art, style="bold cyan")
    panel = Panel(
        Align.center(banner_text),
        subtitle="[bold magenta]v1.0.0 - Cryptographic Fragmentation Protocol[/bold magenta]",
        border_style="bright_blue",
        padding=(1, 2)
    )
    console.print(panel)

def startup_sequence():
    """Sequenza di avvio estetica."""
    steps = [
        "📡 Establishing AES-GCM kernel...",
        "🧮 Initializing Finite Fields GF(2^8)...",
        "🧬 Seeding Shamir Polynomials...",
        "🛡️ Verifying cryptographic integrity...",
        "✅ ShardLock System Online."
    ]
    
    with Live(console=console, refresh_per_second=4) as live:
        for i, step in enumerate(steps):
            content = "\n".join([f"[dim green]✔ {s}[/dim green]" for s in steps[:i]])
            if i < len(steps):
                content += f"\n[bold cyan]➜ {steps[i]}[/bold cyan]"
            live.update(Align.left(content))
            time.sleep(0.3)
    time.sleep(0.4)

def show_protocol_overview():
    """Spiegazione tecnica del protocollo."""
    console.clear()
    show_banner()
    
    text = Text()
    text.append("\n1. THE VAULT (AES-256-GCM)\n", style="bold cyan")
    text.append("Files are sealed using AES-GCM, providing both encryption and hardware-level integrity checks.\n", style="dim")
    
    text.append("\n2. KEY DERIVATION (PBKDF2)\n", style="bold cyan")
    text.append("Your password is hardened through 600,000 iterations of SHA-256 to block brute-force attacks.\n", style="dim")
    
    text.append("\n3. THE SHARDING (SHAMIR'S SECRET SHARING)\n", style="bold cyan")
    text.append("The key is NOT stored. It's transformed into a mathematical polynomial. We split this polynomial into 'n' shards.\n", style="dim")
    
    text.append("\n4. THRESHOLD SECURITY (k of n)\n", style="bold cyan")
    text.append("You only need 'k' shards to reconstruct the key. With fewer than 'k' shards, decryption is mathematically impossible.\n", style="dim")

    console.print(Panel(text, title="[bold white]HOW IT WORKS[/bold white]", border_style="magenta", expand=False))
    Prompt.ask("\n[bold yellow]Press Enter to return to Command Center[/bold yellow]")
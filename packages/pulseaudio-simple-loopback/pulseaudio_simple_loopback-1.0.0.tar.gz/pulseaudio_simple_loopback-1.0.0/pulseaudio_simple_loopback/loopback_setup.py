from subprocess import run, PIPE, CalledProcessError
import re
import time
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm

console = Console()

def run_cmd(cmd):
    result = run(cmd, shell=True, check=True, stdout=PIPE, text=True)
    return result.stdout.strip()

def parse_pactl_entries(raw):
    entries = []
    for line in raw.splitlines():
        parts = line.split('\t')
        if len(parts) >= 2 and not parts[1].endswith(".monitor"):
            entries.append(parts[1])
    return entries

def is_bt_sink(sink):
    return "bluez" in sink.lower()

def get_bt_mac_from_sink(bt_sink):
    match = re.search(r"bluez_output\.([0-9A-Fa-f_]+)", bt_sink)
    if match:
        mac = match.group(1).replace('_', ':').upper()
        return mac
    return None

def reconnect_bt_dev(mac):
    console.print(f"[bold blue]Disconnecting Bluetooth device {mac}...")
    run(["bluetoothctl", "disconnect", mac])
    console.print(f"[green]Bluetooth device disconnected, sleeping for 2 seconds...")
    console.print(f"[bold blue]Reconnecting Bluetooth device {mac}...")
    run(["bluetoothctl", "connect", mac])
    console.print(f"[bold green]Bluetooth device reconnected")
    

def display_table(title, entries):
    table = Table(title=title)
    table.add_column("Index", justify="right", style="cyan")
    table.add_column("Name", style="magenta")

    for (i, name) in enumerate(entries):
        table.add_row(str(i), name)
    console.print(table)

def select_device(entries, label):
    while True:
        try:
            index = int(Prompt.ask(f"[cyan]Select {label} index[/]"))
            if 0 <= index < len(entries):
                return entries[index]
            else:
                console.print(f"[red]Invalid index. Enter a number between 0 and {len(entries)}[/]")
        except ValueError:
            console.print("[red]Invalid input. Enter a number[/]")

def main():
    try:
        sources_raw = run_cmd("pactl list short sources")
        sinks_raw = run_cmd("pactl list short sinks")

        sources = parse_pactl_entries(sources_raw)
        sinks = parse_pactl_entries(sinks_raw)

        display_table("Available Sources", sources)
        source = select_device(sources, "audio source")
        display_table("Available Sinks", sinks)
        sink = select_device(sinks, "audio sink")

        console.print(f"\n[bold blue]Setting loopback from:[/] [green]{source}[/] to [yellow]{sink}[/]")
        
        cmd = f"pactl load-module module-loopback source={source} sink={sink} latency_msec=10"
        result = run(cmd, shell=True, check=True)

        if is_bt_sink(sink):
            mac = get_bt_mac_from_sink(sink)
            console.print(f"[cyan]Detected Bluetooth sink: [bold blue]{sink}[/bold blue], MAC: [yellow]{mac}[/yellow]")
            console.print("[cyan]The script detected you've selected a bluetooth device as the loopback sink")
            console.print("[cyan]In some instances the device needs to be disconnected and reconnected if the loopback does not start on its own")
            if mac and Confirm.ask("[yellow]Do you want to disconnect and reconnect your Bluetooth device now?"):
                reconnect_bt_dev(mac)

        console.print("[bold green]Loopback enabled succesfully")
    except CalledProcessError:
        console.print(f"[bold red]Command failed:[/] {e}")
    except KeyboardInterrupt:
        console.print("[yellow]Interrupted by user[/]")

if __name__ == "__main__":
    main()

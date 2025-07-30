import time
import os
import psutil
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich import box

import sys
import termios
import tty
import select

DEFAULT_REFRESH = 3.0
# PAGE_SIZE will be set dynamically in main()
PAGE_SIZE = 15

import sys
console = Console(file=sys.stdout)
# print(console.is_terminal)
# print(console.size)


def get_processes():
    """Get a list of process info dicts for the current system, sorted by CPU usage descending."""
    procs = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
        try:
            info = proc.info
            mem_info = info['memory_info']
            cpu = info['cpu_percent'] if info['cpu_percent'] is not None else 0.0
            procs.append({
                'pid': info['pid'],
                'name': info['name'],
                'cpu': cpu,
                'mem': mem_info.rss / (1024 * 1024) if mem_info else 0,
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return sorted(procs, key=lambda p: p['cpu'], reverse=True)


def build_table(processes, selected_idx, page_size, is_frozen=False, status_msg=None):
    term_height = console.size.height
    usable_height = term_height - 6  # Reserve for header/title/etc
    page_size = 20

    # Calculate the window of processes to display
    total = len(processes)
    if total <= page_size:
        start = 0
        end = total
    else:
        # Calculate start position to keep selected process in view
        start = max(0, min(selected_idx - page_size // 2, total - page_size))
        end = start + page_size

    visible = processes[start:end]
    visible_selected = selected_idx - start

    # Get terminal width and calculate column widths
    term_width = console.width - 40
    pid_width = 12
    cpu_width = 10
    ram_width = 12
    name_width = 100  # 7 for borders and padding

    table = Table(
        title=f"pybtm - Interactive Process Monitor (showing {start+1}-{end} of {total}){' [FROZEN]' if is_frozen else ''}",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold white",
        title_style="bold white",
        # width=term_width
    )
    table.add_column("PID", style="cyan", no_wrap=True, width=pid_width)
    table.add_column("Name" + (" (Frozen)" if is_frozen else ""), style="magenta", width=name_width)
    table.add_column("CPU %", style="green", justify="right", width=cpu_width, no_wrap=True)
    table.add_column("RAM (MB)", style="yellow", justify="right", width=ram_width, no_wrap=True)
    
    for idx, proc in enumerate(visible):
        style = "on blue" if idx == visible_selected else ""
        table.add_row(
            str(proc['pid']),
            proc['name'] or "",
            f"{proc['cpu']:.1f}",
            f"{proc['mem']:.1f}",
            style=style
        )

    if status_msg:
        table.caption = f"[bold red]{status_msg}[/bold red]"

    return table


def getch(timeout=0.05):
    """Get a single character from stdin, non-blocking, with a timeout."""
    fd = sys.stdin.fileno()
    rlist, _, _ = select.select([fd], [], [], timeout)
    if rlist:
        ch = sys.stdin.read(1)
        if ch == '\x1b':  # Arrow keys
            ch += sys.stdin.read(2)
        return ch
    return None


def kill_process(pid):
    try:
        p = psutil.Process(pid)
        p.kill()
        return True
    except Exception as e:
        return False


def main():
    import argparse
    global PAGE_SIZE
    status_msg = None

    parser = argparse.ArgumentParser(description="pybtm: Interactive process monitor.")
    parser.add_argument("-f", "--frequency", type=float, default=DEFAULT_REFRESH, help="Snapshot frequency in seconds (default: 3)")
    args = parser.parse_args()

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    selected_idx = 0
    processes = get_processes()
    last_update = time.time()
    is_frozen = False
    frozen_processes = None
    # Initial PAGE_SIZE
    table = build_table(processes, selected_idx, PAGE_SIZE, is_frozen)

    with Live(table, refresh_per_second=20, console=console, screen=True) as live:
        while True:
            now = time.time()
            updated = False
            # Refresh process list only at the specified frequency
            if now - last_update > args.frequency:
                if is_frozen:
                    # When frozen, only update CPU and memory values for existing processes
                    new_processes = get_processes()
                    if frozen_processes is None:
                        frozen_processes = processes
                    
                    # Create a mapping of PID to process info
                    process_map = {p['pid']: p for p in new_processes}
                    
                    # Update existing processes with new CPU/memory values
                    for proc in frozen_processes:
                        if proc['pid'] in process_map:
                            proc['cpu'] = process_map[proc['pid']]['cpu']
                            proc['mem'] = process_map[proc['pid']]['mem']
                    
                    # Remove processes that no longer exist
                    frozen_processes = [p for p in frozen_processes if p['pid'] in process_map]
                    processes = frozen_processes
                else:
                    processes = get_processes()
                    frozen_processes = None
                
                if selected_idx >= len(processes):
                    selected_idx = max(0, len(processes) - 1)
                last_update = now
                updated = True
            
            # Handle input
            tty.setcbreak(sys.stdin.fileno())
            ch = getch(timeout=0.05)
            if ch:
                if ch in ('j', '\x1b[B'):  # Down arrow or 'j'
                    selected_idx = min(selected_idx + 1, len(processes) - 1)
                    updated = True
                elif ch in ('k', '\x1b[A'):  # Up arrow or 'k'
                    selected_idx = max(selected_idx - 1, 0)
                    updated = True
                elif ch in ('x', 'X'):
                    if processes:
                        pid = processes[selected_idx]['pid']
                        if kill_process(pid):
                            status_msg = f"[bold red]Killed process {pid} - {processes[selected_idx]['name']}[/bold red]"
                        else:
                            status_msg = f"[bold yellow]Failed to kill process {pid} - {processes[selected_idx]['name']}[/bold yellow]"
                        time.sleep(0.5)
                        # Remove the killed process from both lists
                        processes = [p for p in processes if p['pid'] != pid]
                        if frozen_processes:
                            frozen_processes = [p for p in frozen_processes if p['pid'] != pid]
                        selected_idx = min(selected_idx, len(processes) - 1)
                        last_update = time.time()  # Reset update timer after kill
                        updated = True
                elif ch == ' ':  # Spacebar to toggle freeze
                    is_frozen = not is_frozen
                    if is_frozen:
                        frozen_processes = processes.copy()
                    updated = True
                elif ch in ('q', '\x03', '\x1b'):
                    break
            
            # Only update the table if something changed
            if updated:
                table = build_table(processes, selected_idx, PAGE_SIZE, is_frozen, status_msg)
                live.update(table)

    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

if __name__ == "__main__":
    main() 

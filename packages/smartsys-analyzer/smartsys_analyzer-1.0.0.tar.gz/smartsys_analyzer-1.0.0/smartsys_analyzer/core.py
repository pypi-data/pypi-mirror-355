import psutil
import humanize
import datetime
import platform
import schedule
import time
import threading
from pydantic import BaseModel, ValidationError, conint
from colorama import Fore, Style, init
from rich.console import Console
from rich.table import Table
from tabulate import tabulate
import matplotlib.pyplot as plt
from pydantic import BaseModel, Field
from typing import Annotated

from .config import DEFAULT_THRESHOLD
from .utils import log_info, log_warning, log_critical

init(autoreset=True)
console = Console()

Percent = conint(ge=1, le=100)

class ThresholdConfig(BaseModel):
    cpu: Annotated[int, Field(ge=1, le=100)]
    memory: Annotated[int, Field(ge=1, le=100)]
    disk: Annotated[int, Field(ge=1, le=100)]

class Analyzer:
    def __init__(self, thresholds: dict = None):
        try:
            self.thresholds = ThresholdConfig(**(thresholds or DEFAULT_THRESHOLD))
        except ValidationError as e:
            raise ValueError("Invalid threshold configuration") from e

    def get_cpu_usage(self):
        return psutil.cpu_percent(interval=1)

    def get_memory_info(self):
        mem = psutil.virtual_memory()
        return mem.percent, mem.total, mem.used

    def get_disk_info(self):
        disk = psutil.disk_usage('/')
        return disk.percent, disk.total, disk.used

    def get_processes_summary(self, top_n=5):
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        return processes[:top_n]

    def print_system_info(self):
        uname = platform.uname()
        console.print(f"[bold cyan]System:[/bold cyan] {uname.system}")
        console.print(f"[bold cyan]Node Name:[/bold cyan] {uname.node}")
        console.print(f"[bold cyan]Release:[/bold cyan] {uname.release}")
        console.print(f"[bold cyan]Processor:[/bold cyan] {uname.processor}")
        console.print(f"[bold cyan]Boot Time:[/bold cyan] {datetime.datetime.fromtimestamp(psutil.boot_time())}")

    def print_status_table(self):
        cpu = self.get_cpu_usage()
        mem_percent, mem_total, mem_used = self.get_memory_info()
        disk_percent, disk_total, disk_used = self.get_disk_info()

        table = Table(title="Smart System Resource Status")

        table.add_column("Resource", justify="left", style="bold")
        table.add_column("Usage", justify="right")
        table.add_column("Total", justify="right")

        table.add_row("CPU", f"{cpu}%", "-")
        table.add_row("Memory", f"{mem_percent}%", humanize.naturalsize(mem_total))
        table.add_row("Disk", f"{disk_percent}%", humanize.naturalsize(disk_total))

        console.print(table)

        # Logging warnings
        if cpu > self.thresholds.cpu:
            log_warning(f"High CPU usage: {cpu}%")
        if mem_percent > self.thresholds.memory:
            log_warning(f"High Memory usage: {mem_percent}%")
        if disk_percent > self.thresholds.disk:
            log_warning(f"High Disk usage: {disk_percent}%")

    def print_top_processes(self, top_n=5):
        procs = self.get_processes_summary(top_n)
        if not procs:
            console.print("No processes found.", style="bold red")
            return

        headers = ["PID", "Name", "CPU %", "Memory %"]
        rows = [[p['pid'], p['name'], p['cpu_percent'], round(p['memory_percent'], 2)] for p in procs]
        console.print("\n[bold yellow]Top Processes by CPU:[/bold yellow]")
        console.print(tabulate(rows, headers=headers, tablefmt="fancy_grid"))

    def plot_usage(self):
        labels = ['CPU', 'Memory', 'Disk']
        values = [
            self.get_cpu_usage(),
            self.get_memory_info()[0],
            self.get_disk_info()[0]
        ]
        colors = ['#ff9999','#66b3ff','#99ff99']

        plt.figure(figsize=(5,5))
        plt.pie(values, labels=labels, colors=colors, autopct='%1.1f%%')
        plt.title("System Resource Usage")
        plt.tight_layout()
        plt.show()

    def analyze_now(self, show_plot=False):
        console.rule("[bold green]System Analysis")
        self.print_system_info()
        self.print_status_table()
        self.print_top_processes()
        if show_plot:
            self.plot_usage()

    def schedule_analysis(self, interval_minutes=10):
        schedule.every(interval_minutes).minutes.do(self.analyze_now)
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(1)
        thread = threading.Thread(target=run_scheduler, daemon=True)
        thread.start()
        console.print(f"[bold magenta]Scheduled analysis every {interval_minutes} minutes...[/bold magenta]")

def print_summary():
    from rich import print
    from .utils import get_cpu_usage, get_memory_usage, get_disk_usage

    print("[bold cyan]System Summary:[/bold cyan]")
    print(f"  • CPU Usage    : {get_cpu_usage()}%")
    print(f"  • Memory Usage : {get_memory_usage()}%")
    print(f"  • Disk Usage   : {get_disk_usage()}%")


def main():
    from rich import print
    print("[bold green]SmartSys Analyzer running...[/bold green]")
    print_summary()


# CLI Entry (optional run)
if __name__ == "__main__":
    analyzer = Analyzer()
    analyzer.analyze_now(show_plot=True)

import time
import argparse
import csv
import os
from datetime import datetime
from rich.console import Console

console = Console()

SESSION_LOG = "session_log.csv"

def log_session(session_type, duration):
    now = datetime.now().isoformat()
    with open(SESSION_LOG, "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([now, session_type, duration])

def run_timer(minutes, label):
    total_seconds = minutes * 60
    console.print(f"\n[bold yellow]{label}[/bold yellow] - {minutes} minutes")
    for remaining in range(total_seconds, 0, -1):
        mins, secs = divmod(remaining, 60)
        timer_display = f"{mins:02d}:{secs:02d}"
        print(f"\r[ {timer_display} ] remaining ")
        time.sleep(1)
    print("\n[Timer finished]\n")

def maybe_git_commit():
    response = input("\nCommit changes to Git? [y/N]: ").strip().lower()
    if response == 'y':
        message = input("Commit message: ").strip()
        os.system(f"git add . && git commit -m \"{message}\"")

def main():
    parser = argparse.ArgumentParser(description="DevTimer: Pomodoro with Git integration")
    parser.add_argument("--work", type=int, default=25, help="Work duration in minutes")
    parser.add_argument("--break-time", type=int, default=5, help="Break duration in minutes")
    parser.add_argument("--no-commit", action="store_true", help="Disable git commit prompt")
    args = parser.parse_args()

    console.print(f":hourglass_flowing_sand: [bold green]Work Time - {args.work} minutes[/bold green]")
    run_timer(args.work, "Work Session")
    log_session("work", args.work)

    if not args.no_commit:
        maybe_git_commit()

    console.print(f"\n:coffee: [bold blue]Break Time - {args.break_time} minutes[/bold blue]")
    run_timer(args.break_time, "Break")
    log_session("break", args.break_time)

def run():
    main()


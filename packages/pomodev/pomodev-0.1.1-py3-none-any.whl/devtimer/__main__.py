import time
import argparse
import csv
import os
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table

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
        print(f"\r[ {timer_display} ] remaining ", end="")
        time.sleep(1)
    print("\n[Timer finished]\a\n")  # Sound alert (cross-platform bell character)


def maybe_git_commit():
    response = input("\nCommit changes to Git? [y/N]: ").strip().lower()
    if response == 'y':
        message = input("Commit message: ").strip()
        os.system(f"git add . && git commit -m \"{message}\"")


def show_history():
    if not os.path.exists(SESSION_LOG):
        console.print("[italic red]No session history found.[/italic red]")
        return

    table = Table(title="Pomodev Session History")
    table.add_column("Time", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Duration (min)", justify="right")

    with open(SESSION_LOG, newline="") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            table.add_row(row[0], row[1], row[2])

    console.print(table)


def show_streak():
    if not os.path.exists(SESSION_LOG):
        console.print("[italic red]No streak data found.[/italic red]")
        return

    today = datetime.now().date()
    week_ago = today - timedelta(days=6)
    sessions_today = 0
    sessions_this_week = 0

    with open(SESSION_LOG, newline="") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            session_time = datetime.fromisoformat(row[0]).date()
            if row[1] == "work":
                if session_time == today:
                    sessions_today += 1
                if week_ago <= session_time <= today:
                    sessions_this_week += 1

    console.print(f"\n[bold green]Today's Work Sessions:[/bold green] {sessions_today}")
    console.print(f"[bold blue]This Week's Work Sessions:[/bold blue] {sessions_this_week}\n")


def main():
    parser = argparse.ArgumentParser(description="Pomodev: Pomodoro CLI with Git integration and session tracking")
    parser.add_argument("--work", type=int, default=25, help="Work duration in minutes")
    parser.add_argument("--break-time", type=int, default=5, help="Break duration in minutes")
    parser.add_argument("--no-commit", action="store_true", help="Disable git commit prompt")
    parser.add_argument("--history", action="store_true", help="Show session history")
    parser.add_argument("--streak", action="store_true", help="Show today's and weekly streaks")
    args = parser.parse_args()

    if args.history:
        show_history()
        return

    if args.streak:
        show_streak()
        return

    console.print(f":hourglass_flowing_sand: [bold green]Work Time - {args.work} minutes[/bold green]")
    run_timer(args.work, "Work Session")
    log_session("work", args.work)

    if not args.no_commit:
        maybe_git_commit()

    console.print(f"\n:coffee: [bold blue]Break Time - {args.break_time} minutes[/bold blue]")
    run_timer(args.break_time, "Break")
    log_session("break", args.break_time)


if __name__ == "__main__":
    main()
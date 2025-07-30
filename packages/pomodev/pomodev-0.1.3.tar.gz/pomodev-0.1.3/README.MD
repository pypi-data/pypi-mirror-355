# ⏳ pomodev

**A developer-first CLI Pomodoro tool** with built-in Git integration, streak tracking, session history, and sound alerts. Designed to keep you in the flow while working on projects.

---

## ✨ Features

* ⏱️ Simple Pomodoro work/break timer
* ✅ Auto Git commit prompt after each work session
* 📊 `--history`: View all your sessions in a rich table
* 🔁 `--streak`: See how consistent you’ve been today and this week
* 🔔 Sound alert when timers finish
* 📁 CSV log file (`session_log.csv`) stores all your sessions locally

---

## 📦 Installation

```bash
pip install pomodev
```

Make sure your Python user bin is in your PATH, or use:

```bash
source ~/.zshrc  # or your shell config file
```

---

## 🚀 Usage

```bash
pomodev
```

By default, this starts a 25-minute work session, followed by a 5-minute break, and prompts you to Git commit when done.

---

### 🎠 Options

| Flag           | Description                               |
| -------------- | ----------------------------------------- |
| `--work`       | Set custom work duration (minutes)        |
| `--break-time` | Set custom break duration (minutes)       |
| `--no-commit`  | Skip Git commit prompt                    |
| `--history`    | Show all logged sessions                  |
| `--streak`     | Display your current day/week work streak |

---

## 🧪 Examples

### Regular session (default 25/5)

```bash
pomodev
```

### Deep work (50 minutes) with no break

```bash
pomodev --work 50 --break-time 0 --no-commit
```

### View past sessions

```bash
pomodev --history
```

### See your streak stats

```bash
pomodev --streak
```

---

## 📁 Where data is stored

All sessions are logged to `session_log.csv` in the working directory.

---

## 👨‍💻 Who is it for?

If you:

* Work on side projects and want accountability
* Want lightweight time tracking tied to Git activity
* Like working in the terminal and hate bloated apps

This is for you.

---

## ✅ Roadmap Ideas

* [ ] Preset durations via config
* [ ] Web dashboard (`--export-html`)
* [ ] Live UI with [Textual](https://github.com/Textualize/textual)
* [ ] Daily goal + streak gamification

---

Built with ❤️ by Dhruv

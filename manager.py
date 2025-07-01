import os
import json
import subprocess
import tkinter as tk
from tkinter import messagebox, scrolledtext


class Project:
    """Represent a single npm project and its running process."""

    def __init__(self, name, path, command, port):
        self.name = name
        self.path = path
        self.command = command
        self.port = port
        self.process = None  # subprocess.Popen instance when running

    def start(self, log_fn):
        """Start the project's npm command with PORT set."""
        if self.process and self.process.poll() is None:
            log_fn(f"{self.name} already running on port {self.port}\n")
            return

        env = os.environ.copy()
        env["PORT"] = str(self.port)
        try:
            # Start the command in a new process
            self.process = subprocess.Popen(
                self.command,
                cwd=self.path,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                shell=True,
                text=True,
            )
            log_fn(f"Starting {self.name} on port {self.port}\n")
        except FileNotFoundError:
            log_fn(f"Failed to start {self.name}: command not found\n")
            self.process = None
            return

        # Read initial output asynchronously
        self._read_output_async(log_fn)

    def _read_output_async(self, log_fn):
        """Read one line from process output and schedule next read."""
        if self.process is None:
            return

        line = self.process.stdout.readline()
        if line:
            log_fn(f"[{self.name}] {line}")
        if self.process.poll() is None:
            # Schedule next read
            root.after(100, self._read_output_async, log_fn)
        else:
            log_fn(f"{self.name} stopped\n")

    def stop(self, log_fn):
        """Stop the running process if any."""
        if self.process and self.process.poll() is None:
            self.process.terminate()
            log_fn(f"Stopping {self.name}\n")
        else:
            log_fn(f"{self.name} is not running\n")

    def update(self, log_fn):
        """Run 'git pull origin main' in the project directory."""
        try:
            result = subprocess.run(
                ["git", "pull", "origin", "main"],
                cwd=self.path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            log_fn(result.stdout + "\n")
            if result.returncode != 0:
                messagebox.showerror(self.name, "Git pull failed")
        except FileNotFoundError:
            log_fn("Git not found. Is it installed?\n")


def load_projects(cfg_path):
    """Load project definitions from a JSON configuration file."""
    with open(cfg_path) as f:
        data = json.load(f)

    projects = []
    for entry in data.get("projects", []):
        projects.append(
            Project(
                entry.get("name"),
                entry.get("path"),
                entry.get("command", "npm start"),
                entry.get("port", 3000),
            )
        )
    return projects


def build_gui(projects):
    """Create the tkinter UI for managing projects."""
    global root
    root = tk.Tk()
    root.title("NPM Project Manager")

    log_box = scrolledtext.ScrolledText(root, width=80, height=20)
    log_box.grid(row=len(projects) + 1, column=0, columnspan=4, padx=5, pady=5)

    def log(message):
        log_box.insert(tk.END, message)
        log_box.see(tk.END)

    for idx, proj in enumerate(projects):
        tk.Label(root, text=proj.name).grid(row=idx, column=0, padx=5, pady=5, sticky="w")
        tk.Label(root, text=f"Port: {proj.port}").grid(row=idx, column=1, padx=5, pady=5)

        tk.Button(root, text="Start", command=lambda p=proj: p.start(log)).grid(row=idx, column=2)
        tk.Button(root, text="Stop", command=lambda p=proj: p.stop(log)).grid(row=idx, column=3)
        tk.Button(root, text="Update", command=lambda p=proj: p.update(log)).grid(row=idx, column=4)

    return root


if __name__ == "__main__":
    config_file = os.path.join(os.path.dirname(__file__), "projects.json")
    if not os.path.exists(config_file):
        messagebox.showerror("Error", f"Configuration file {config_file} not found")
        raise SystemExit

    projs = load_projects(config_file)
    gui = build_gui(projs)
    gui.mainloop()

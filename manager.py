import os
import sys
import json
import subprocess
import threading
from typing import List

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QInputDialog,
    QPlainTextEdit,
    QMessageBox,
)
from PySide6.QtCore import Qt


class Project:
    """Represent a single npm project and its running processes."""

    def __init__(self, name: str, path: str, commands: List[str], port: int):
        self.name = name
        self.path = path
        self.commands = commands
        self.port = port
        self.processes: List[subprocess.Popen] = []

    def _log_prefix(self, msg: str) -> str:
        """Prefix log messages with the project name."""
        return f"[{self.name}] {msg}"

    def update(self, log_fn) -> None:
        """Run 'git pull origin main' for this project."""
        log_fn(self._log_prefix("running git pull origin main"))
        try:
            result = subprocess.run(
                ["git", "pull", "origin", "main"],
                cwd=self.path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            log_fn(self._log_prefix(result.stdout))
            if result.returncode != 0:
                QMessageBox.critical(None, self.name, "Git pull failed")
        except FileNotFoundError:
            log_fn(self._log_prefix("git not found"))

    def configure(self, commands: List[str], log_fn) -> None:
        """Update the commands used to launch this project."""
        self.commands = commands
        log_fn(self._log_prefix("commands updated"))

    def set_port(self, port: int, log_fn) -> None:
        """Update the port for this project."""
        self.port = port
        log_fn(self._log_prefix(f"port set to {port}"))

    def _read_output(self, process: subprocess.Popen, log_fn) -> None:
        """Forward output from a subprocess to the log."""
        for line in iter(process.stdout.readline, ""):
            if line:
                log_fn(self._log_prefix(line.rstrip()))
        log_fn(self._log_prefix("process exited"))

    def launch(self, log_fn) -> None:
        """Run 'npm install' then start project commands concurrently."""
        env = os.environ.copy()
        env["PORT"] = str(self.port)
        log_fn(self._log_prefix("running npm install"))
        subprocess.run(["npm", "install"], cwd=self.path, env=env)

        for cmd in self.commands:
            process = subprocess.Popen(
                cmd,
                cwd=self.path,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                shell=True,
                text=True,
            )
            self.processes.append(process)
            thread = threading.Thread(
                target=self._read_output, args=(process, log_fn), daemon=True
            )
            thread.start()
        log_fn(self._log_prefix("launched"))

    def stop(self, log_fn) -> None:
        """Terminate all running processes for this project."""
        for proc in self.processes:
            if proc.poll() is None:
                proc.terminate()
        self.processes.clear()
        log_fn(self._log_prefix("stopped"))


def load_projects(cfg_path: str) -> List[Project]:
    """Load project definitions from a JSON configuration file."""
    with open(cfg_path) as f:
        data = json.load(f)

    projects = []
    for entry in data.get("projects", []):
        commands = entry.get("commands") or [entry.get("command", "npm start")]
        projects.append(
            Project(
                entry.get("name", "unnamed"),
                entry.get("path", "."),
                commands,
                entry.get("port", 3000),
            )
        )
    return projects


def save_projects(cfg_path: str, projects: List[Project]) -> None:
    """Write current project configuration back to JSON."""
    data = {
        "projects": [
            {
                "name": p.name,
                "path": p.path,
                "commands": p.commands,
                "port": p.port,
            }
            for p in projects
        ]
    }
    with open(cfg_path, "w") as f:
        json.dump(data, f, indent=2)


class MainWindow(QMainWindow):
    """Qt window for managing multiple npm projects."""

    def __init__(self, projects: List[Project], cfg_path: str) -> None:
        super().__init__()
        self.projects = projects
        self.cfg_path = cfg_path
        self.setWindowTitle("NPM Project Manager")
        self._build_ui()

    # UI construction -----------------------------------------------------
    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        self.vbox = QVBoxLayout()
        central.setLayout(self.vbox)

        # Add UI rows for each project
        for project in self.projects:
            self._add_project_row(project)

        add_btn = QPushButton("Add Project")
        add_btn.clicked.connect(self._add_project_dialog)
        self.vbox.addWidget(add_btn)

        self.log_widget = QPlainTextEdit()
        self.log_widget.setReadOnly(True)
        self.vbox.addWidget(self.log_widget)

    def _add_project_row(self, project: Project) -> None:
        """Create UI elements for a single project."""
        row = QHBoxLayout()

        name_label = QLabel(project.name)
        port_label = QLabel(f"Port: {project.port}")

        update_btn = QPushButton("Update")
        update_btn.clicked.connect(lambda: project.update(self._log))

        config_btn = QPushButton("Configure")
        config_btn.clicked.connect(lambda: self._configure_project(project))

        port_btn = QPushButton("Set port")
        port_btn.clicked.connect(lambda: self._set_port(project, port_label))

        launch_btn = QPushButton("Launch")
        launch_btn.clicked.connect(lambda: project.launch(self._log))

        stop_btn = QPushButton("Stop")
        stop_btn.clicked.connect(lambda: project.stop(self._log))

        for widget in [name_label, port_label, update_btn, config_btn, port_btn, launch_btn, stop_btn]:
            row.addWidget(widget)

        container = QWidget()
        container.setLayout(row)
        self.vbox.addWidget(container)

    def _log(self, message: str) -> None:
        """Append a message to the log window."""
        self.log_widget.appendPlainText(message)
        self.log_widget.ensureCursorVisible()

    # Dialog helpers ------------------------------------------------------
    def _add_project_dialog(self) -> None:
        """Prompt the user for new project information and add it."""
        path = QFileDialog.getExistingDirectory(self, "Select Project Folder")
        if not path:
            return
        name, ok = QInputDialog.getText(self, "Project Name", "Name:")
        if not ok or not name:
            return
        cmd_text, ok = QInputDialog.getMultiLineText(
            self,
            "Commands",
            "Enter commands (one per line):",
            "npm start",
        )
        if not ok:
            return
        port, ok = QInputDialog.getInt(self, "Port", "Port:", 3000, 1, 65535)
        if not ok:
            return

        commands = [c.strip() for c in cmd_text.splitlines() if c.strip()]
        project = Project(name, path, commands, port)
        self.projects.append(project)
        self._add_project_row(project)
        save_projects(self.cfg_path, self.projects)

    def _configure_project(self, project: Project) -> None:
        """Edit the commands for an existing project."""
        current = "\n".join(project.commands)
        cmd_text, ok = QInputDialog.getMultiLineText(
            self,
            "Configure Commands",
            "Commands (one per line):",
            current,
        )
        if ok:
            commands = [c.strip() for c in cmd_text.splitlines() if c.strip()]
            project.configure(commands, self._log)
            save_projects(self.cfg_path, self.projects)

    def _set_port(self, project: Project, label: QLabel) -> None:
        """Prompt for a new port and update the project."""
        port, ok = QInputDialog.getInt(
            self, "Set Port", "Port:", project.port, 1, 65535
        )
        if ok:
            project.set_port(port, self._log)
            label.setText(f"Port: {project.port}")
            save_projects(self.cfg_path, self.projects)


# Application entry point -------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    cfg_file = os.path.join(os.path.dirname(__file__), "projects.json")
    if not os.path.exists(cfg_file):
        QMessageBox.critical(None, "Error", f"Configuration file {cfg_file} not found")
        sys.exit(1)

    projects = load_projects(cfg_file)
    window = MainWindow(projects, cfg_file)

    # Ensure all processes stop when the application closes
    def _cleanup() -> None:
        for p in projects:
            p.stop(lambda msg: None)

    app.aboutToQuit.connect(_cleanup)
    window.show()
    sys.exit(app.exec())

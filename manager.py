import json
import os
import subprocess
import sys

from dataclasses import dataclass, field
from typing import Dict, List, Optional

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
    QSpinBox,
    QMessageBox,
    QPlainTextEdit,
)

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "projects.json")

@dataclass
class Project:
    """Represents a Node.js application managed with PM2."""

    path: str
    port: int = 3000
    # Optional PM2 process name override. When None the folder name is used.
    custom_name: Optional[str] = None
    # Optional additional environment variables used when running the project
    env: Dict[str, str] = field(default_factory=dict)

    @property
    def name(self) -> str:
        """Return the PM2 process name."""
        # Use the custom name if provided, otherwise fallback to folder name
        return self.custom_name or os.path.basename(os.path.abspath(self.path))


def load_projects(cfg_path: str) -> List[Project]:
    """Load project configuration from JSON."""
    if not os.path.exists(cfg_path):
        return []
    with open(cfg_path) as fh:
        data = json.load(fh)
    # Map loaded JSON dictionaries to Project instances, preserving any
    # custom name that was saved previously.
    return [
        Project(
            p["path"],
            p.get("port", 3000),
            p.get("name"),
            # Load optional environment variable mapping
            p.get("env", {}),
        )
        for p in data.get("projects", [])
    ]


def save_projects(cfg_path: str, projects: List[Project]) -> None:
    """Persist project configuration to JSON."""
    # Serialize Project instances back to dictionaries, including the custom
    # name only when it is explicitly set.
    data = {
        "projects": [
            {k: v for k, v in {
                "path": p.path,
                "port": p.port,
                "name": p.custom_name,
                # Include environment variables only when defined
                "env": p.env if p.env else None,
            }.items() if v is not None}
            for p in projects
        ]
    }
    with open(cfg_path, "w") as fh:
        json.dump(data, fh, indent=2)


class ProjectRow(QWidget):
    """Widget row for a single project."""

    def __init__(self, project: Project, save_cb, log_cb):
        super().__init__()
        self.project = project
        self.save_cb = save_cb
        self.log_cb = log_cb

        layout = QHBoxLayout()
        self.setLayout(layout)

        self.path_label = QLabel(project.path)
        layout.addWidget(self.path_label)

        # Display the current PM2 process name
        self.name_label = QLabel(project.name)
        layout.addWidget(self.name_label)

        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(project.port)
        self.port_spin.valueChanged.connect(self._port_changed)
        layout.addWidget(self.port_spin)

        update_btn = QPushButton("Update")
        update_btn.clicked.connect(self._update)
        layout.addWidget(update_btn)

        run_btn = QPushButton("Run")
        run_btn.clicked.connect(self._run)
        layout.addWidget(run_btn)

        stop_btn = QPushButton("Stop")
        stop_btn.clicked.connect(self._stop)
        layout.addWidget(stop_btn)

        rename_btn = QPushButton("Change Name")
        rename_btn.clicked.connect(self._change_name)
        layout.addWidget(rename_btn)

        env_btn = QPushButton("Env")
        env_btn.clicked.connect(self._edit_env)
        layout.addWidget(env_btn)

        # status label to display the last command outcome
        self.status_label = QLabel("Idle")
        layout.addWidget(self.status_label)

    def _port_changed(self, value: int) -> None:
        """Update the project port and save configuration."""
        self.project.port = value
        self.save_cb()

    def _update(self) -> None:
        """Run 'git pull origin main' in the project directory."""
        cmd = ["git", "pull", "origin", "main"]
        self.status_label.setText("Updating...")
        self.log_cb(f"Running: {' '.join(cmd)} in {self.project.path}")
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project.path,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError:
            # git executable could not be located - show an error message
            err = f"{cmd[0]} not found. Is it installed and on your PATH?"
            self.log_cb(err)
            self.status_label.setText("Error")
            QMessageBox.critical(self, self.project.name, err)
            return
        self.log_cb(result.stdout or result.stderr)
        self.status_label.setText("OK" if result.returncode == 0 else "Error")
        QMessageBox.information(self, self.project.name, result.stdout or result.stderr)

    def _run(self) -> None:
        """Launch the app via PM2 using 'npm start'."""
        env = os.environ.copy()
        env["PORT"] = str(self.project.port)
        # Merge in any user-defined environment variables
        env.update(self.project.env)
        cmd = ["pm2", "start", "npm", "--name", self.project.name, "--", "start"]
        self.status_label.setText("Running...")
        self.log_cb(f"Running: {' '.join(cmd)} in {self.project.path}")
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project.path,
                env=env,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError:
            # PM2 or npm could not be located. Inform the user and abort.
            err = f"{cmd[0]} not found. Is it installed and on your PATH?"
            self.log_cb(err)
            self.status_label.setText("Error")
            QMessageBox.critical(self, self.project.name, err)
            return
        self.log_cb(result.stdout or result.stderr)
        self.status_label.setText("OK" if result.returncode == 0 else "Error")

    def _stop(self) -> None:
        """Stop the PM2 process if it is running."""
        # Invoke PM2 to stop the process by name
        cmd = ["pm2", "stop", self.project.name]
        self.status_label.setText("Stopping...")
        self.log_cb(f"Running: {' '.join(cmd)}")
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError:
            # pm2 command missing - cannot stop the process
            err = f"{cmd[0]} not found. Is it installed and on your PATH?"
            self.log_cb(err)
            self.status_label.setText("Error")
            QMessageBox.critical(self, self.project.name, err)
            return
        self.log_cb(result.stdout or result.stderr)
        self.status_label.setText("OK" if result.returncode == 0 else "Error")

    def _change_name(self) -> None:
        """Prompt the user for a new process name and save it."""
        # Let the user enter a new name. If none is provided, keep the current
        # one.
        new_name, ok = QInputDialog.getText(self, "Process Name", "New name:", text=self.project.name)
        if not ok or not new_name:
            return
        self.project.custom_name = new_name
        self.name_label.setText(self.project.name)
        self.save_cb()

    def _edit_env(self) -> None:
        """Allow editing of custom environment variables."""
        # Prepare a multi-line string in KEY=VALUE format
        current = "\n".join(f"{k}={v}" for k, v in self.project.env.items())
        text, ok = QInputDialog.getMultiLineText(
            self,
            "Environment Variables",
            "KEY=VALUE per line:",
            current,
        )
        if not ok:
            return
        env = {}
        for line in text.splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
        self.project.env = env
        self.save_cb()


class MainWindow(QMainWindow):
    """Main application window for managing Node.js apps."""

    def __init__(self, projects: List[Project]):
        super().__init__()
        self.projects = projects
        self.setWindowTitle("PM2 Frontend")

        central = QWidget()
        self.setCentralWidget(central)
        self.vbox = QVBoxLayout()
        central.setLayout(self.vbox)

        for project in self.projects:
            self._add_project_row(project)

        add_btn = QPushButton("Add Project")
        add_btn.clicked.connect(self._add_project)
        self.vbox.addWidget(add_btn)

        # log widget displays executed commands and their output
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.vbox.addWidget(self.log)

    def _add_project_row(self, project: Project) -> None:
        row = ProjectRow(project, self._save, self._log_message)
        self.vbox.addWidget(row)

    def _log_message(self, msg: str) -> None:
        """Append a message to the log widget."""
        self.log.appendPlainText(msg)

    def _add_project(self) -> None:
        # Ask the user for a project directory
        path = QFileDialog.getExistingDirectory(self, "Select Node.js Project")
        if not path:
            return
        # Ask for the port the app should listen on
        port, ok = QInputDialog.getInt(self, "Port", "Port:", 3000, 1, 65535)
        if not ok:
            return
        # Ask for an optional PM2 process name
        name, ok = QInputDialog.getText(self, "Process Name", "Process name:")
        if not ok or not name:
            name = None
        # Ask for optional environment variables
        env_text, ok = QInputDialog.getMultiLineText(
            self,
            "Environment Variables",
            "KEY=VALUE per line:",
        )
        if not ok:
            env = {}
        else:
            env = {}
            for line in env_text.splitlines():
                if "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
        project = Project(path, port, name, env)
        self.projects.append(project)
        self._add_project_row(project)
        self._save()

    def _save(self) -> None:
        save_projects(CONFIG_FILE, self.projects)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    projects = load_projects(CONFIG_FILE)
    window = MainWindow(projects)
    window.show()
    sys.exit(app.exec())

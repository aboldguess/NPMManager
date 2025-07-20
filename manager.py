import json
import os
import subprocess
import sys

from dataclasses import dataclass, field
from typing import Dict, List

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
    # optional extra environment variables required to launch the app
    extra_env: Dict[str, str] = field(default_factory=dict)

    @property
    def name(self) -> str:
        """Use the folder name as the PM2 process name."""
        return os.path.basename(os.path.abspath(self.path))


def load_projects(cfg_path: str) -> List[Project]:
    """Load project configuration from JSON."""
    if not os.path.exists(cfg_path):
        return []
    with open(cfg_path) as fh:
        data = json.load(fh)
    # create Project objects while passing optional environment variables
    return [
        Project(p["path"], p.get("port", 3000), p.get("env", {}))
        for p in data.get("projects", [])
    ]


def save_projects(cfg_path: str, projects: List[Project]) -> None:
    """Persist project configuration to JSON."""
    data = {
        "projects": [
            {"path": p.path, "port": p.port, "env": p.extra_env}
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

        # button to configure additional environment variables
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
        result = subprocess.run(
            cmd,
            cwd=self.project.path,
            capture_output=True,
            text=True,
        )
        self.log_cb(result.stdout or result.stderr)
        self.status_label.setText("OK" if result.returncode == 0 else "Error")
        QMessageBox.information(self, self.project.name, result.stdout or result.stderr)

    def _edit_env(self) -> None:
        """Allow the user to edit additional environment variables."""
        current = "\n".join(f"{k}={v}" for k, v in self.project.extra_env.items())
        text, ok = QInputDialog.getMultiLineText(
            self,
            "Environment Variables",
            "KEY=VALUE per line:",
            current,
        )
        if not ok:
            return

        env_vars: Dict[str, str] = {}
        for line in text.splitlines():
            if "=" not in line:
                continue
            key, val = line.split("=", 1)
            env_vars[key.strip()] = val.strip()
        self.project.extra_env = env_vars
        self.save_cb()

    def _run(self) -> None:
        """Launch the app via PM2 using 'npm start'."""
        env = os.environ.copy()
        env["PORT"] = str(self.project.port)
        # include any additional environment variables configured for the project
        env.update(self.project.extra_env)
        cmd = ["pm2", "start", "npm", "--name", self.project.name, "--", "start"]
        self.status_label.setText("Running...")
        self.log_cb(
            f"Running: {' '.join(cmd)} in {self.project.path} with PORT={self.project.port}"
        )
        result = subprocess.run(
            cmd,
            cwd=self.project.path,
            env=env,
            capture_output=True,
            text=True,
        )
        self.log_cb(result.stdout or result.stderr)
        self.status_label.setText("OK" if result.returncode == 0 else "Error")


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
        path = QFileDialog.getExistingDirectory(self, "Select Node.js Project")
        if not path:
            return
        port, ok = QInputDialog.getInt(self, "Port", "Port:", 3000, 1, 65535)
        if not ok:
            return
        # allow the user to enter optional environment variables during creation
        env_text, _ = QInputDialog.getMultiLineText(
            self,
            "Environment Variables",
            "KEY=VALUE per line:",
            "",
        )
        env_vars: Dict[str, str] = {}
        for line in env_text.splitlines():
            if "=" not in line:
                continue
            key, val = line.split("=", 1)
            env_vars[key.strip()] = val.strip()

        project = Project(path, port, env_vars)
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

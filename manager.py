import json
import os
import subprocess
import sys

from dataclasses import dataclass
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
    QSpinBox,
    QMessageBox,
)

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "projects.json")

@dataclass
class Project:
    """Represents a Node.js application managed with PM2."""

    path: str
    port: int = 3000

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
    return [Project(p["path"], p.get("port", 3000)) for p in data.get("projects", [])]


def save_projects(cfg_path: str, projects: List[Project]) -> None:
    """Persist project configuration to JSON."""
    data = {"projects": [{"path": p.path, "port": p.port} for p in projects]}
    with open(cfg_path, "w") as fh:
        json.dump(data, fh, indent=2)


class ProjectRow(QWidget):
    """Widget row for a single project."""

    def __init__(self, project: Project, save_cb):
        super().__init__()
        self.project = project
        self.save_cb = save_cb

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

    def _port_changed(self, value: int) -> None:
        """Update the project port and save configuration."""
        self.project.port = value
        self.save_cb()

    def _update(self) -> None:
        """Run 'git pull origin main' in the project directory."""
        result = subprocess.run(
            ["git", "pull", "origin", "main"],
            cwd=self.project.path,
            capture_output=True,
            text=True,
        )
        QMessageBox.information(self, self.project.name, result.stdout or result.stderr)

    def _run(self) -> None:
        """Launch the app via PM2 using 'npm start'."""
        env = os.environ.copy()
        env["PORT"] = str(self.project.port)
        subprocess.run(
            ["pm2", "start", "npm", "--name", self.project.name, "--", "start"],
            cwd=self.project.path,
            env=env,
        )


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

    def _add_project_row(self, project: Project) -> None:
        row = ProjectRow(project, self._save)
        self.vbox.addWidget(row)

    def _add_project(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Node.js Project")
        if not path:
            return
        port, ok = QInputDialog.getInt(self, "Port", "Port:", 3000, 1, 65535)
        if not ok:
            return
        project = Project(path, port)
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

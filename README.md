# NPMManager

This application provides a PySide6 GUI for managing multiple NPM projects. Each
project can be updated from git, launched on a specific port, and stopped from
the interface. Configuration is stored in `projects.json`.

## Configuration

Projects are listed in `projects.json` as follows:

```json
{
  "projects": [
    {
      "name": "project1",
      "path": "/path/to/project1",
      "commands": ["npm start"],
      "port": 3000
    }
  ]
}
```

- `name` – display name for the project.
- `path` – folder containing the project.
- `commands` – list of commands to launch the project. Each runs with the
  `PORT` environment variable set.
- `port` – port number to use when launching.

Edit this file or use the **Add Project** button in the GUI to manage your
projects.

## Usage

1. Install Python 3.x and the `PySide6` package.
2. Run the manager with:

```bash
python3 manager.py
```

The main window lists all configured projects. For each project you can:

- **Update** – run `git pull origin main` in the project directory.
- **Configure** – edit the commands used to launch the project.
- **Set port** – change the port passed to `npm` via the `PORT` environment
  variable.
- **Launch** – run `npm install` followed by the configured commands.
- **Stop** – terminate all running commands for that project.

A log view at the bottom of the window displays progress output from all
processes.

This application requires a graphical environment capable of running Qt
applications.

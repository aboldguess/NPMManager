# NPMManager

This project provides a simple Tkinter GUI for managing multiple NPM projects. It allows you to start servers on specific ports, update each project using `git pull origin main`, and view console output in one place.

## Configuration

Projects are defined in `projects.json` as a list of entries:

```json
{
  "projects": [
    {
      "name": "project1",
      "path": "c:/code/project1",
      "command": "npm start",
      "port": 3000
    }
  ]
}
```

- `name` – display name for the project
- `path` – path to the folder containing the project
- `command` – command to start the server (for example `npm start` or `npm run dev`)
- `port` – port number to set in the `PORT` environment variable when running the command

Edit this file to match your projects.

## Usage

1. Install Python 3.x.
2. Run the manager with:

```bash
python3 manager.py
```

The GUI shows each project with **Start**, **Stop**, and **Update** buttons. Clicking **Start** runs the project's command with `PORT` set to the specified value. **Update** runs `git pull origin main` in the project directory.

This application requires a graphical environment to display the Tkinter window.

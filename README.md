# PM2 Frontend

This project provides a small PySide6 GUI for working with the [PM2](https://pm2.keymetrics.io/) process manager.  It allows you to keep a list of Node.js application folders and start them with `pm2` on a chosen port.

## Configuration file

Projects are stored in `projects.json`:

```json
{
  "projects": [
    {
      "path": "/path/to/app",
      "port": 3000,
      "name": "my-app",
      "env": {
        "DEBUG": "1",
        "SECRET": "value"
      }
    }
  ]
}
```

Each entry defines the folder containing the Node.js project, the port to use
when starting it, an optional custom PM2 process name and an optional
`env` object with additional environment variables that will be passed to the
process when launched.

## Setup

Run `install.ps1` on Windows or install the dependencies manually:

```bash
python -m pip install -r requirements.txt
```

PM2 must also be installed globally:

```bash
npm install -g pm2
```
If `pm2` isn't found after installation, ensure that the global npm binaries
directory (for example `%APPDATA%\npm` on Windows) is included in your `PATH`
environment variable and restart the terminal.

## Usage

Launch the GUI with:

```bash
python manager.py
```

For every configured project you can:

- **Update** – run `git pull origin main` inside the project directory.
- **Run** – start the project with `pm2` using `npm start` and the selected port.
- **Stop** – stop the running PM2 process.
- **Change Name** – set a custom name for the PM2 process.
- **Env** – configure additional environment variables.

New projects can be added using the **Add Project** button. When adding a
project you will be prompted for environment variables in `KEY=VALUE` format.

The application requires a graphical environment capable of running Qt applications.

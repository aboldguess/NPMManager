# PM2 Frontend

This project provides a small PySide6 GUI for working with the [PM2](https://pm2.keymetrics.io/) process manager.  It allows you to keep a list of Node.js application folders and start them with `pm2` on a chosen port.

## Configuration file

Projects are stored in `projects.json` and can include optional environment
variables and a custom name for the port variable:

```json
{
  "projects": [
{ "path": "/path/to/app", "port": 3000, "port_var": "PORT", "env": { "NODE_ENV": "production" } }
  ]
}
```

Each entry defines the folder containing the Node.js project and the port to use
when starting it.  The `port_var` field specifies the environment variable name
used to pass the port to the application (default `PORT`).  Additional
environment variables may be provided in an optional `env` object and will be
passed to the process when launched.

## Setup

Run `install.ps1` on Windows or install the dependencies manually:

```bash
python -m pip install -r requirements.txt
```

PM2 must also be installed globally:

```bash
npm install -g pm2
```

## Usage

Launch the GUI with:

```bash
python manager.py
```

For every configured project you can:

- **Update** – run `git pull origin main` inside the project directory.
- **Run** – start the project with `pm2` using `npm start` and the selected port.
  Additional environment variables can be configured per project via the **Env**
  button.  The port variable name can be edited directly in the project row.

New projects can be added using the **Add Project** button.
When adding a project you can also supply environment variables and choose the
port variable name if required.

The application requires a graphical environment capable of running Qt applications.


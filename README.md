# PM2 Frontend

This project provides a small PySide6 GUI for working with the [PM2](https://pm2.keymetrics.io/) process manager.  It allows you to keep a list of Node.js application folders and start them with `pm2` on a chosen port.

## Configuration file

Projects are stored in `projects.json`:

```json
{
  "projects": [
    { "path": "/path/to/app", "port": 3000 }
  ]
}
```

Each entry defines the folder containing the Node.js project and the port to use when starting it.

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

New projects can be added using the **Add Project** button.

The application requires a graphical environment capable of running Qt applications.

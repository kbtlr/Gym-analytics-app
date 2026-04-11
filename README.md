# Gym-analytics-app

A desktop-first gym analytics application for tracking training progress, workout volume, and personal bests over time.

## Project overview

This project combines:
- a **Python Flask backend** for authentication, data handling, and database access
- an **Electron desktop shell** that wraps the current HTML/CSS/JavaScript interface
- a simple frontend UI for login, registration flow, and gym progress views

The current structure keeps the existing interface while moving away from a browser-only workflow. The UI is loaded inside Electron as a desktop app, while the Python backend remains available for auth, stats, and persistence.

## Current stack

### Backend
- Python
- Flask
- Flask-Login
- Flask-SQLAlchemy
- PyMySQL

### Desktop shell
- Electron
- Node.js / npm

### Frontend
- HTML
- CSS
- JavaScript

## Features and intended direction

The application is designed to support:
- user login and registration
- workout logging
- personal best tracking
- total volume tracking over time
- cycle progress tracking
- a desktop app experience using the existing frontend layout

Some backend routes are still scaffolded and contain placeholder logic, but the project structure is in place.

## Repository notes

This repository does **not** commit local dependency folders such as:
- `node_modules/`
- `venv/`

These are intentionally ignored with `.gitignore` and must be installed locally after cloning.

## Setup

### 1. Clone the repository
```powershell
git clone https://github.com/kbtlr/Gym-analytics-app.git
cd Gym-analytics-app
```

### 2. Create and activate a Python virtual environment
```powershell
py -m venv venv
.\venv\Scripts\Activate
```

If PowerShell blocks activation, run:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate again:
```powershell
.\venv\Scripts\Activate
```

### 3. Install Python dependencies
```powershell
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
```

### 4. Install Node / Electron dependencies
```powershell
npm install
```

## Running the project

### Start the Flask backend
```powershell
py run.py
```

### Start the Electron desktop shell
Open a second terminal in the project root and run:
```powershell
npm start
```

## Development notes

- The Electron entry point is `electron/main.js`
- The desktop window currently loads `core.html`
- The main frontend script is `scripts/main.js`
- Python dependencies are listed in `requirements.txt`
- Node/Electron dependencies are listed in `package.json`

## Important note about dependencies

If you clone this repository on a new machine, you must restore local dependencies yourself:

```powershell
py -m pip install -r requirements.txt
npm install
```

Do not commit `node_modules` or `venv` back into the repository.

## Next steps

Likely next improvements include:
- connecting the frontend forms and buttons to the Flask backend routes
- replacing placeholder route logic in `app/auth.py` and `app/stats.py`
- moving database secrets into environment variables
- packaging the Electron app into a distributable installer

# Gym-analytics-app

A desktop-first gym analytics application for tracking training progress, workout volume, and personal bests over time.

## Project overview

This project combines:
- a Python Flask backend for authentication, data handling, and database access
- an Electron desktop shell that wraps the current HTML/CSS/JavaScript interface
- a simple frontend UI for login, registration flow, and gym progress views

The current structure keeps the existing interface while moving away from a browser-only workflow. The UI is loaded inside Electron as a desktop app, while the Python backend remains available for auth, stats, and persistence.

## Current stack

### Backend
- Python
- Flask
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

## To Do

Next targets:
- UI updates
- Backtack glitch
- Data edge cases








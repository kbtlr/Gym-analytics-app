# Gym-analytics-app
A desktop-first gym analytics application for tracking training progress, workout volume, and personal bests over time.

## Project overview
This project combines:
- a Python Flask backend for authentication, data handling, and database access
- an Electron desktop shell that wraps the current HTML/CSS/JavaScript interface
- a simple frontend UI for login, registration flow, and gym progress views

The current structure keeps the existing interface while moving away from a browser-only workflow. The UI is loaded inside Electron as a desktop app, while the Python backend remains available for auth, stats, and persistence.

In one window, type:
npm run start:backend

In another, run the shell with:
npm run start



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

  <img width="1920" height="1009" alt="Your Gym Pal 27_09_2026 00_39_51" src="https://github.com/user-attachments/assets/ce28b5f5-94ab-4943-bfc4-314895af67e8" />


## Features and intended direction
The application is designed to support:
- user login and registration
- workout logging
- personal best tracking
- total volume tracking over time
- cycle progress tracking

## To Do
Current UI is skewed on the main dashboard. Login credentials are successfully saved so UI troubleshooting is viable now.
Will work on UI before attending to backtrack glitch and data handling.








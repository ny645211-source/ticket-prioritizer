
# Ticket Prioritizer

A tool that automatically prioritizes customer support tickets using NLP, so urgent issues get attention first.

## Features
- Reads incoming support tickets
- Scores each ticket by urgency using NLP
- Shows a sorted support queue

## Tech Stack
- Backend: Python
- Frontend: React + Vite
- Database: SQLite
- Deployment: Docker

## How to Run

### Option 1: Docker

docker-compose up --build


### Option 2: Manually

Backend:

cd backend
pip install -r requirements.txt


Frontend:

cd frontend
npm install
npm run dev


Then open the URL shown in the terminal (usually http://localhost:5173).

## Author
ny645211-source
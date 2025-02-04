# Numbers Game - Backend (Flask Server)

This is the backend for **Numbers Game**, a multiplayer game where players compete by choosing numbers based on a strategic calculation.

## 🚀 Features
- **Game Management:** Create and manage game sessions.
- **REST API:** Provides endpoints for player interactions.
- **Game Logic:** Computes winners based on player choices.
- **Hosted on Vercel:** Fully deployed, no local setup required.

## 📡 API Endpoints

### Game Management
- POST /game/create → Creates a new game
- POST /game/join → Joins a game
- POST /game/start → Starts the game
- POST /round/submit → Submits a number
- GET /game/results → Retrieves round results
- POST /game/end_round → Ends the current round
- POST /game/next_round → Starts the next round
- POST /round/calculate_winner → Calculates the winner



## 🔧 Setup & Deployment
1. Clone the repository:
   git clone https://github.com/YourUsername/NumbersGame-Backend.git
   cd NumbersGame-Backend

2. Install dependencies:
   pip install -r requirements.txt

3. Run the server locally:
   python app.py

## 📜 License
This project is licensed under the **MIT License**.

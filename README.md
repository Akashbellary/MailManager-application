# EmailFlow

I built **EmailFlow** as part of the hiring process at **Linkenite**.  
The goal was to make an email management system with AI features, while also showing my skills across backend, frontend, and integration.

![Dashboard Screenshot](Screenshot%202025-09-09%20020146.jpg)

---

## Features

- Manage emails in one place  
- AI classification and search using NVIDIA Build API models  
- Dashboard with patterns and quick stats  
- Fast search with simple UI  
- Fully built solo (frontend + backend + AI + styling)

---

## Tech Stack

| Area       | Tech Used                        |
|------------|----------------------------------|
| Backend    | Python (Flask)                   |
| Database   | MongoDB                          |
| AI Models  | NVIDIA Build API (Qwen, Gemma, DeepSeek) |
| Frontend   | HTML, CSS, Jinja templates       |
| Other      | JavaScript for interactivity     |

---

## Setup Instructions

1. Clone the repo:
   ```bash
   git clone https://github.com/Akashbellary/MailManager-application.git
   cd MailManager-application

2. Create virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   pip install -r requirements.txt


3. Create a .env file in the project root:
   ```bash
   NVIDIA_API_KEY=your_nvidia_key
   MONGODB_URI=your_mongodb_connection_string


Run the app: python -m emailflow.main
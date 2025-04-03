# Flask Project

## 📌 Introduction

This project is a simple web application built with Flask. It includes REST API functionality and template rendering and can be run in a local development environment.

## 🚀 Getting Started

### 1. Set Up Virtual Environment & Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment (Linux & Mac)
source venv/bin/activate

# Activate virtual environment (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Update requirements.txt
pip freeze > requirements.txt
```

### 2. Run the Application

```bash
python run.py
```

Open your browser and go to `http://127.0.0.1:5000/` to check the application.

## 📌 Features

- `/` : Main page (HTML rendering)
- `/about` : About page
- `/user/<name>` : Dynamic route example
- `/api/data` : Returns JSON data

## 🛠️ API Example

```bash
curl http://127.0.0.1:5000/api/data
```

Response example:

```json
{
  "message": "CORS setup complete!"
}
```

## 📂 Project Structure

```
📦 Project Root
├── 📂 templates          # HTML template folder
│   ├── index.html       # Main page
├── 📂 static             # Static files (CSS, JS, images, etc.)
├── .gitignore           # Files to exclude from Git
├── requirements.txt     # Dependency list
├── app.py               # Flask application main file
└── README.md            # Project description file
```

## 🌐 Deployment

For production, run the application using Gunicorn.

```bash
pip install gunicorn

gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 📝 License

MIT License

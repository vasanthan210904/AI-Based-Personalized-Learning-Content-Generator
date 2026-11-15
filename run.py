"""Development entry point.

Run with:
    python run.py

The app factory creates the SQLite database and seeds the admin account,
subjects and topics on first start.
"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)

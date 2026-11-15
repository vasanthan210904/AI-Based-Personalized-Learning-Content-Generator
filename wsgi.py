from app import create_app

app = create_app()
handler = app

if __name__ == "__main__":
    app.run()

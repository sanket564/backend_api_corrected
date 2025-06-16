from app import create_app  # Import your app factory function
import os

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Render provides the PORT env variable
    app.run(host="0.0.0.0", port=port)

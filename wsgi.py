import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Required by Render
    app.run(host="0.0.0.0", port=port)

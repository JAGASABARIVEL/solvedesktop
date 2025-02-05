
from app import create_app


# Create the app and pass the filename if needed
app = create_app()

if __name__ == '__main__':
    app.run(port=5002, debug=False)
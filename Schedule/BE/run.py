from app import create_app
from waitress import serve

# Create the Flask app object
app = create_app()

if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5002)

from flask import Flask
from flask_cors import CORS
from routes.historical_events import historical_events_bp

app = Flask(__name__)

# Configure CORS to allow requests from the frontend
CORS(app, 
     origins=["http://localhost:3000"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"],
     supports_credentials=True)

# Register blueprints
app.register_blueprint(historical_events_bp, url_prefix='/api/historical-events')

@app.route('/')
def index():
    return {"message": "Welcome to Morocco History API"}

if __name__ == '__main__':
    app.run(debug=True, port=5000) 
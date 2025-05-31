from flask import Flask
from flask_cors import CORS
from routes.historical_events import historical_events_bp

app = Flask(__name__)
CORS(app)

# Register blueprints
app.register_blueprint(historical_events_bp, url_prefix='/api/historical-events')

@app.route('/')
def index():
    return {"message": "Welcome to Morocco History API"}

if __name__ == '__main__':
    app.run(debug=True, port=5000) 
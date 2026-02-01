
import os
import flask

app = Flask(__name__) # Error: Flask not imported

@app.route('/')
def index():
    return "Hello World"

def connect_db():
    # Error: Hardcoded password
    password = "super_secret_password_123"
    print(f"Connecting with {password}")

if __name__ == "__main__":
    app.run(debug=True)

# Importing required libraries
import os
from app import create_app

# Get the environment variables
global_variable = os.environ.get('GLOBAL_VARIABLE')
quizz_variable = os.environ.get('QUIZZ_VARIABLE')

# Create the Flask app
app = create_app()

# Set the secret key from environment variable
app.secret_key = 'your_secret_key'

if __name__ == '__main__':
    # Run the app
    app.run(debug=True)

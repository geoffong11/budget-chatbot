# app.py
from flask import Flask, request, jsonify
from retrieval import find_top_n_documents
from prompts import generate_response
import os

# Initialize the Flask application
app = Flask(__name__)

# Define a route (URL endpoint)
@app.route('/')
def home():
    return "Hello, World!"

@app.route('/query', methods=["POST"])
def submit():
    data = request.get_json()
    query = data.get('user_input')
    retrieved_docs = find_top_n_documents(query)
    text_response = generate_response(retrieved_docs, query)
    return jsonify({'reply': text_response})
    

# Run the application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
# Singapore Financial Budget 2024 AI chatbot assistant

## Description

This project is an AI-powered chatbot utilizing OpenAI's ChatGPT model and a Retrieval-Augmented Generation (RAG) pipeline to enhance response accuracy and relevance.

## Getting Started
### Installation
Follow these steps to install the chatbot
```
# Clone the repository
git clone https://github.com/geoffong11/budget-chatbot.git
cd budget-chatbot
```
### Configuration

Update the `.env` file with your ChatGPT API key

### Running the Chatbot

To run the chatbot, open docker desktop, and run:
```
docker-compose up
```
If the code has been ran before, run `docker-compose down --volumes`. Then add the `build` flag to `docker-compose up` to rebuild  the image.\
Go to `localhost:8501` and chat away!


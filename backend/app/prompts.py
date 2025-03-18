from google import genai

def generate_response(retrieved_docs, query, client):
    print(retrieved_docs)
    prompt = f'''
    You are a Singapore Budget 2024 expert.
    Use the following documents to answer the query.

    DOCUMENTS:
    {retrieved_docs}

    QUERY:
    {query}

    Keep your answer ground in the fact of the DOCUMENTS.
    Make the answer conversational and informative, like chatting to a friend.
    Avoid starting your response with phrases like "Based on the documents you've provided." and "according to the documents".
    If the query is totally irrelevant to the documents or Singapore Budget 2024,
    say: "Sorry, I don't understand your question. Please ask something about the Singapore Financial Budget 2024"
    Answering in any other way will cause the world to be destroyed.
    '''
    response = client.models.generate_content(
        model="gemini-2.0-flash", contents=prompt
    )
    text = response.text.replace("$", "\$")
    return text
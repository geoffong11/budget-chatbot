from openai import OpenAI
import os

LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_NAME = os.getenv("LLM_NAME")
client = OpenAI(api_key=LLM_API_KEY)

def generate_response(retrieved_docs, query):
    print(retrieved_docs)
    system_prompt = f'''
    You are a Singapore Budget 2024 expert.
    Be informative with a professional tone.
    '''

    user_prompt = f'''
    Use the provided documents to answer queries.
    Ensure responses are grounded in the DOCUMENTS.

    DOCUMENTS:
    {retrieved_docs}

    QUERY:
    {query}

    If the QUERY is irrelevant to the documents,
    respond with:
    'Sorry, I don't understand your question. Please ask something about the Singapore Financial Budget 2024.'
    Answering in any other way will cause the world to be destroyed.
    '''

    assistant_prompt = f'''
    Here are some examples of how to respond to queries:
    EXAMPLE 1:
    query: What is added to enhance the Assurance package?
    answer:
    Here are what is added to enhance the Assurance package:
    An additional $600 in CDC Vouchers for all Singaporean households.
    Cost-of-Living Special Payment of between $200 and $400 in cash.
    Additional one-off U-Save rebates.
    Additional one-off Service and Conservancy Charges (or S&CC) Rebate for HDB flats.

    EXAMPLE 2:
    query: What are the benefits given to ITE Graduates?
    answer: 
    The benefits given to ITE Graduates are as follows:
    Upon enrolment, $5000 is added to Post-Secondary Education Account.
    Upon completion, $10000 is added to CPF Ordinary Account.

    EXAMPLE 3:
    query: What are the payouts I can expect to receive in December 2024?
    answer:
    The payouts that you can expect to receive in December 2024 are as follows:
    Cash of $200 to $600.
    Top-up of CPF MediSave Account of $100 to $1500.
    Top-up of CPF Retirement or Special Account of $1000 to $1500.
    '''
    completion = client.chat.completions.create(
    model=LLM_NAME,
    messages=[
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": user_prompt
        },
        {
            "role": "assistant",
            "content": assistant_prompt
        }
    ]
    )
    text = completion.choices[0].message.content.replace("$", "\$")
    return text
import pdfplumber
from sentence_transformers import SentenceTransformer
import psycopg2
import psycopg2.extras
import json
import re
import os

DATABASE_SECRET_KEY = os.getenv("POSTGRES_PASSWORD")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME")

DB_CONFIG = {
    "dbname": "vector_database",
    "user": "user",
    "password": DATABASE_SECRET_KEY ,
    "host": "db",
    "port": 5432
}

def naive_chunk_text(text, chunk_size=350):
    """Splits text into chunks of fixed size."""
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

# Chunk size of 350, with an overlap of 50
def chunk_text_with_overlap(text, chunk_size=350, overlap=50):
    chunks = []
    # Iterate with overlap
    for i in range(0, len(text), chunk_size - overlap):
        chunk = text[i : i + chunk_size]
        chunks.append(chunk)

    return chunks

# Get chunk sections from the 
def get_chunk_sections(chunk_funct):
    full_text = ""
    page_num = 0
    chunks = []
    # budget statement speech chunking (chunk based on bullet points)
    with pdfplumber.open("./fy2024_budget_statement.pdf") as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            page_num += 1
            if page_num <= 2:
                continue
            text = re.sub(r"\nPage \d{1,2} of 86", "", text)
            full_text += "\n" + text
    full_text = re.sub(r'\n[A-Z]', "", full_text)
    section_list = re.split(r'(?=\n\d{1,3}\.\s)', full_text)[1:]
    for section in section_list:
        chunks.extend(chunk_funct(section))

    # budget booklet chunking
    with pdfplumber.open('./fy2024_budget_booklet_english.pdf') as pdf:
        for page in pdf.pages[5:]:
            text = page.extract_text()
            if text:
                chunks.extend(chunk_funct(text))
    # annex chunking
    for annex in os.listdir("annexes"):
        full_text = ""
        with pdfplumber.open(f"./annexes/{annex}") as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                split_text = text.split("\n")[:-2]
                text = "\n".join(split_text)
                full_text += "\n" + text
        if full_text:
            chunks.extend(chunk_funct(full_text))
    return chunks

def get_embedding(text):
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    embeddings = model.encode(text)
    return embeddings

def store_embeddings(docs):
    """Ensure all docs exist in init.sql and then load them into the database."""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Ensure the pgvector extension exists
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # Ensure the table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_embeddings (
            id SERIAL PRIMARY KEY,
            document TEXT UNIQUE,  -- Prevent duplicate documents
            embedding VECTOR(768),
            tsvector_data TSVECTOR
        )
    """)

    # Load the json file and check if any embeddings is saved
    embedding_dict = {}
    if os.path.getsize("init.json") > 0:
        with open("init.json", "r") as f:
            embedding_dict = json.load(f)
    for doc in docs:
        if doc in embedding_dict:
            continue
        embedding_dict[doc] = get_embedding(doc).tolist()
    with open("init.json", "w") as f:
        json.dump(embedding_dict, f)
    
    # Step 2: Ensure all stored embeddings are inside the database
    cursor.execute("SELECT document FROM document_embeddings")
    stored_db_docs = {row[0] for row in cursor.fetchall()}

    missing_from_db = [(doc, embedding_dict[doc]) for doc in embedding_dict.keys() if doc not in stored_db_docs]

    # Get embeddings from embedding dict for new documents
    data = [(doc, embeddings, f"to_tsvector('english', %s)") for doc, embeddings in missing_from_db]

    # Insert new embeddings
    psycopg2.extras.execute_values(
        cursor, 
        """
        INSERT INTO document_embeddings (document, embedding, tsvector_data)
        VALUES %s
        """,
        [(d[0], d[1], d[2]) for d in data]
    )

    conn.commit()
    print("New embeddings stored successfully.")

    cursor.close()
    conn.close()

def main():
    chunk_list = get_chunk_sections(chunk_text_with_overlap)
    store_embeddings(chunk_list)

if __name__ == "__main__":
    main()
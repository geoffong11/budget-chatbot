import pdfplumber
from sentence_transformers import SentenceTransformer
import psycopg2
import psycopg2.extras
import re
import os

DATABASE_SECRET_KEY = os.getenv("POSTGRES_PASSWORD")

DB_CONFIG = {
    "dbname": "vector_database",
    "user": "user",
    "password": DATABASE_SECRET_KEY ,
    "host": "db",
    "port": 5432
}

def naive_chunk_text(text, chunk_size=512):
    """Splits text into chunks of fixed size."""
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

def get_chunk_sections():
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
        chunks.extend(naive_chunk_text(section))
    # budget booklet chunking
    with pdfplumber.open('./fy2024_budget_booklet_english.pdf') as pdf:
        for page in pdf.pages[5:]:
            text = page.extract_text()
            if text:
                chunks.extend(naive_chunk_text(text))
    # annex chunking
    for annex in os.listdir("annexes"):
        with pdfplumber.open(f"./annexes/{annex}") as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                split_text = text.split("\n")[:-2]
                text = "\n".join(split_text)
                if text:
                    chunks.extend(naive_chunk_text(text))
    return chunks


def get_embedding(text, model_name="all-mpnet-base-v2"):
    model = SentenceTransformer(model_name)
    embeddings = model.encode(text)
    return embeddings

def store_embeddings(docs):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Ensure the pgvector extension exists
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # Ensure the table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_embeddings (
            id SERIAL PRIMARY KEY,
            document TEXT UNIQUE,  -- Prevent duplicate documents
            embedding VECTOR(768)
        )
    """)

    # Find documents that are already embedded
    cursor.execute("SELECT document FROM document_embeddings")
    stored_docs = {row[0] for row in cursor.fetchall()}  # Convert to set for fast lookup

    # Filter out docs that are already stored
    new_docs = [doc for doc in docs if doc not in stored_docs]

    if not new_docs:
        print("All documents are already embedded. Skipping embedding computation.")
    else:
        print(f"Embedding {len(new_docs)} new documents...")

        # Compute embeddings for new documents
        data = [(doc, get_embedding(doc)) for doc in new_docs]

        # Insert new embeddings
        psycopg2.extras.execute_values(
            cursor, 
            """
            INSERT INTO document_embeddings (document, embedding)
            VALUES %s
            """,
            [(d[0], d[1].tolist()) for d in data]
        )

        conn.commit()
        print("New embeddings stored successfully.")

    cursor.close()
    conn.close()

def main():
    chunk_list = get_chunk_sections()
    store_embeddings(chunk_list)

if __name__ == "__main__":
    main()
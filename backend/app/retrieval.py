from sentence_transformers import SentenceTransformer
import psycopg2
import os

DATABASE_SECRET_KEY = os.getenv("POSTGRES_PASSWORD")
DB_CONFIG = {
    "dbname": "vector_database",
    "user": "user",
    "password": DATABASE_SECRET_KEY,
    "host": "db",
    "port": 5432
}

def find_top_n_documents(query, n=7, model_name="all-mpnet-base-v2"):
    model = SentenceTransformer(model_name)
    query_embedding = model.encode(query)
    
    # Establish connection to the database
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    # Create index (if not already created) for efficient retrieval
    cur.execute("CREATE INDEX IF NOT EXISTS document_embeddings_embedding_index ON document_embeddings USING ivfflat (embedding vector_cosine_ops);")
    
    # Execute the retrieval query
    cur.execute(
        "SELECT document, embedding <=> %s::vector AS distance FROM document_embeddings ORDER BY distance LIMIT %s;",
        (query_embedding.tolist(), n)
    )
    
    # Fetch results
    results = cur.fetchall()

    # Close connection
    cur.close()
    conn.close()
    return results

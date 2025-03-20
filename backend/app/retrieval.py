from sentence_transformers import SentenceTransformer
import psycopg2
import os
import numpy as np

DATABASE_SECRET_KEY = os.getenv("POSTGRES_PASSWORD")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME")

DB_CONFIG = {
    "dbname": "vector_database",
    "user": "user",
    "password": DATABASE_SECRET_KEY,
    "host": "db",
    "port": 5432
}

def find_top_n_documents(query, n_take=20, n_final=20):
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    query_embedding = model.encode(query)
    
    # Establish connection to the database
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Create BM25 index (if not already created)
    cur.execute("CREATE INDEX IF NOT EXISTS document_embeddings_tsvector_index ON document_embeddings USING GIN (tsvector_data);")
    # Perform BM25-based search
    cur.execute("""
        SELECT id, document, ts_rank_cd(tsvector_data, plainto_tsquery('english', %s)) AS rank
        FROM document_embeddings
        WHERE tsvector_data @@ plainto_tsquery('english', %s)
        ORDER BY rank DESC
        LIMIT %s;
    """, (query, query, n_take))
    
    bm25_results = {row[0]: {'document': row[1], 'bm25_score': row[2], 'dense_score': None} for row in cur.fetchall()}

    # Perform dense vector-based search using cosine similarity
    cur.execute("""
        SELECT id, document, 1 - (embedding <=> %s::vector) AS similarity
        FROM document_embeddings
        ORDER BY similarity DESC
        LIMIT %s;
    """, (query_embedding.tolist(), n_take))
    
    dense_results = {row[0]: {'document': row[1], 'bm25_score': None, 'dense_score': row[2]} for row in cur.fetchall()}

    # Merge BM25 and Dense search results
    for doc_id, data in dense_results.items():
        if doc_id in bm25_results:
            bm25_results[doc_id]['dense_score'] = data['dense_score']
        else:
            bm25_results[doc_id] = data

    # Normalize scores
    bm25_scores = np.array([v['bm25_score'] or 0 for v in bm25_results.values()])
    dense_scores = np.array([v['dense_score'] or 0 for v in bm25_results.values()])

    if len(bm25_scores) > 0:
        bm25_scores = (bm25_scores - np.min(bm25_scores)) / (np.ptp(bm25_scores) + 1e-6)
    if len(dense_scores) > 0:
        dense_scores = (dense_scores - np.min(dense_scores)) / (np.ptp(dense_scores) + 1e-6)

    for i, doc_id in enumerate(bm25_results.keys()):
        bm25_results[doc_id]['bm25_score'] = bm25_scores[i]
        bm25_results[doc_id]['dense_score'] = dense_scores[i]

    
    # Weighted ranking
    alpha = 0.7
    ranked_results = sorted(
        bm25_results.items(),
        key=lambda x: (1 - alpha) * x[1]['bm25_score'] + alpha * x[1]['dense_score'],
        reverse=True
    )

    final_results = [(item[1]['document'], item[1]['bm25_score'], item[1]['dense_score']) for item in ranked_results[:n_final]]

    # Close connection
    cur.close()
    conn.close()
    print(final_results)
    return final_results

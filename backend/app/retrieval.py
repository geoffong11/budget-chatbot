from sentence_transformers import SentenceTransformer
import psycopg2
import os
import re
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

# Retrieve the top `n_take` documents from both keyword-based and vector-based searches.
# Merge the results, ensuring no duplicates, and compute a weighted relevance score for each document.
# The final relevance score is calculated as a weighted average of keyword score and vector similarity scores.
# Select the top `n_final` documents based on the computed scores for the final output.
def find_top_n_documents(query, n_take=20, n_final=20):
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    query_embedding = model.encode(query)
    
    # Establish connection to the database
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    keyword_query = re.sub(r"[^a-zA-Z\s]", "", query)
    keyword_query = re.sub(r"\s+", " ", keyword_query)
    formatted_query = " | ".join(keyword_query.split())
    # Create keyword index (if not already created)
    cur.execute("CREATE INDEX IF NOT EXISTS document_embeddings_tsvector_index ON document_embeddings USING GIN (tsvector_data);")
    # Perform keyword-based search
    cur.execute("""
        SELECT id, document, ts_rank_cd(tsvector_data, query, 32 /* rank/(rank+1) */ ) AS rank
        FROM document_embeddings, to_tsquery('english', %s) query
        WHERE query @@ tsvector_data
        ORDER BY rank DESC
        LIMIT %s;
    """, (formatted_query, n_take))
    
    keyword_results = {row[0]: {'document': row[1], 'keyword_score': row[2], 'dense_score': None} for row in cur.fetchall()}

    # Perform dense vector-based search using cosine similarity
    cur.execute("""
        SELECT id, document, 1 - (embedding <=> %s::vector) AS similarity
        FROM document_embeddings
        ORDER BY similarity DESC
        LIMIT %s;
    """, (query_embedding.tolist(), n_take))
    
    dense_results = {row[0]: {'document': row[1], 'keyword_score': None, 'dense_score': row[2]} for row in cur.fetchall()}

    # Merge keyword and Dense search results
    for doc_id, data in dense_results.items():
        if doc_id in keyword_results:
            keyword_results[doc_id]['dense_score'] = data['dense_score']
        else:
            keyword_results[doc_id] = data

    # Normalize scores
    keyword_scores = np.array([v['keyword_score'] or 0 for v in keyword_results.values()])
    dense_scores = np.array([v['dense_score'] or 0 for v in keyword_results.values()])

    if len(keyword_scores) > 0:
        keyword_scores = (keyword_scores - np.min(keyword_scores)) / (np.ptp(keyword_scores) + 1e-6)
    if len(dense_scores) > 0:
        dense_scores = (dense_scores - np.min(dense_scores)) / (np.ptp(dense_scores) + 1e-6)

    for i, doc_id in enumerate(keyword_results.keys()):
        keyword_results[doc_id]['keyword_score'] = keyword_scores[i]
        keyword_results[doc_id]['dense_score'] = dense_scores[i]

    
    # Weighted ranking
    alpha = 0.7
    ranked_results = sorted(
        keyword_results.items(),
        key=lambda x: (1 - alpha) * x[1]['keyword_score'] + alpha * x[1]['dense_score'],
        reverse=True
    )

    final_results = [(item[1]['document'], item[1]['keyword_score'], item[1]['dense_score']) for item in ranked_results[:n_final]]

    cur.close()
    conn.close()
    return final_results

# Singapore Financial Budget 2024 AI chatbot assistant
This file will talk and explain the RAG implementation.
## RAG Pipeline
### Illustration
![RAG pipeline illustration](images/rag-pipeline.png)

### Tech Stack
Frontend: Streamlit

Backend: Flask

database: PostgreSQL database (pgvector)

### Implementation

#### Models used
Embedding model used: `all-mpnet-base-v2` from `Sentence-Transformers`\
LLM used: `gpt-4o` from `openai`\
Note: Better models could be used. However, my credits expired in 2023, hence I need to work with a limited budget.

#### Chunking
I use different chunking strategies depending on the document type:

- Budget Statement: I chunk by the numbered list, as each numbered section corresponds to a distinct point. This segmentation preserves the document's natural structure and meaning.
- Budget Booklet: I chunk by pages since most information on financial packages or payouts is self-contained within a single page for readability.
- Annexes: Given their document-like nature, I use overlapping chunking to maintain context and coherence.

For both the Budget Statement and Budget Booklet, if a page or segment exceeds the maximum sequence length of the sentence transformer (384 tokens), I apply overlapping chunking to ensure no critical information is lost.

#### Retrieval strategy
I use Hybrid Search for retrieval, combining Vector Search and Full Keyword Search to leverage the strengths of both methods. Vector Search captures semantic similarity, enabling the retrieval of contextually relevant documents even when exact terms do not match. Meanwhile, Full Keyword Search retrieves documents based on exact keyword occurrences, ensuring precise matches for specific terms. PostgreSQL’s `tsvector` and `tsquery` provide efficient keyword search capabilities, complementing pgvector’s implementation of semantic search.

#### Generation and prompting strategy
I make use of system, user and assistant prompts.
- For system prompts, I prompted the LLM to act like a Singapore Budget 2024 expert, and told the LLM to have a professional tone.
- For user prompts, I include the documents that I retrieved and the query. In order to prevent hallucination, I explicitly told the LLM not to answer if the query is not relevant to the documents.
- For assistant prompt, I use few-shot prompting as it gives the LLM a template for it to work with. From trial-and-error, I realized that without the template, the LLM will answer the questions in many different ways, which may not be ideal.

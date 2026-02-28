import chromadb, re
from chromadb.utils import embedding_functions
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

client = chromadb.PersistentClient(path="./chroma_db")
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="paraphrase-multilingual-MiniLM-L12-v2"
)
collection = client.get_or_create_collection(
    name="university_docs",
    embedding_function=embedding_fn,
    metadata={"hnsw:space": "cosine"},
)

def clean_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s\.,;:!?\-\(\)\/\'\"«»àâäéèêëîïôùûüç\u0600-\u06FF]', ' ', text)
    lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 15]
    return '\n'.join(lines)

def ingest_document(path: str) -> int:
    loader = PyPDFLoader(path)
    pages  = loader.load()
    for p in pages:
        p.page_content = clean_text(p.page_content)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=400, chunk_overlap=80,
        separators=["\n\n", "\n", ".", "!", "?", ",", " "],
    )
    chunks = [c for c in splitter.split_documents(pages) if len(c.page_content.strip()) > 50]

    # Remove old chunks for this document
    try:
        old = collection.get(where={"source": path})
        if old["ids"]:
            collection.delete(ids=old["ids"])
    except Exception:
        pass

    for i in range(0, len(chunks), 50):
        batch = chunks[i:i+50]
        collection.upsert(
            ids=[f"{path}_{i+j}" for j in range(len(batch))],
            documents=[c.page_content for c in batch],
            metadatas=[{"source": path, "page": c.metadata.get("page", 0), "chunk_index": i+j}
                       for j, c in enumerate(batch)],
        )
    return len(chunks)

def get_context(query: str, n_results: int = 6) -> str:
    if collection.count() == 0:
        return ""
    try:
        res  = collection.query(query_texts=[query], n_results=min(n_results, collection.count()),
                                include=["documents", "distances", "metadatas"])
        docs      = res["documents"][0]
        distances = res["distances"][0]
        metas     = res["metadatas"][0]

        relevant = [(d, dist, m) for d, dist, m in zip(docs, distances, metas) if dist < 0.7]
        if not relevant:
            relevant = list(zip(docs[:3], distances[:3], metas[:3]))
        relevant.sort(key=lambda x: x[1])

        parts = []
        for doc, _, meta in relevant[:4]:
            src  = meta.get("source", "document").split("/")[-1].replace(".pdf", "")
            page = meta.get("page", 0)
            parts.append(f"[Source: {src}, Page {page+1}]\n{doc}")
        return "\n\n---\n\n".join(parts)
    except Exception as e:
        print(f"RAG error: {e}")
        return ""
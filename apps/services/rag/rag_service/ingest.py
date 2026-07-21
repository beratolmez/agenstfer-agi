import os
import glob
try:
    from langchain_text_splitters import MarkdownHeaderTextSplitter
except ImportError:
    class MarkdownHeaderTextSplitter:
        def __init__(self, headers_to_split_on=None):
            pass
        def split_text(self, text):
            class Page:
                def __init__(self, content):
                    self.page_content = content
                    self.metadata = {}
            return [Page(text)]
import chromadb
from chromadb.utils import embedding_functions

# Connect to local ChromaDB
# For a real system, this would be a persistent client or HTTP client.
chroma_client = chromadb.PersistentClient(path="./chroma_db")

# Use a local embedding function (e.g. sentence-transformers)
# This will download the model on first run if not present
embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

def get_or_create_collection():
    return chroma_client.get_or_create_collection(
        name="okf_wiki",
        embedding_function=embedding_func
    )

def ingest_markdown_files(docs_dir: str):
    """Reads OKF Markdown files, chunks them, and stores them in ChromaDB."""
    collection = get_or_create_collection()
    
    # Headers to split on for OKF
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)

    files = glob.glob(os.path.join(docs_dir, "**/*.md"), recursive=True)
    
    for file_path in files:
        print(f"Processing {file_path}...")
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Split markdown
        md_header_splits = markdown_splitter.split_text(content)
        
        # Prepare for Chroma
        documents = []
        metadatas = []
        ids = []
        
        for i, split in enumerate(md_header_splits):
            documents.append(split.page_content)
            # Merge file path into metadata
            meta = split.metadata.copy()
            meta["source"] = file_path
            metadatas.append(meta)
            ids.append(f"{file_path}_{i}")
            
        if documents:
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            print(f"Added {len(documents)} chunks from {file_path}")

def ingest_markdown_file(file_path: str):
    """Reads a single OKF Markdown file, chunks it, and stores it in ChromaDB."""
    collection = get_or_create_collection()
    
    # Headers to split on for OKF
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)

    print(f"Processing {file_path}...")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Split markdown
    md_header_splits = markdown_splitter.split_text(content)
    
    # Prepare for Chroma
    documents = []
    metadatas = []
    ids = []
    
    for i, split in enumerate(md_header_splits):
        documents.append(split.page_content)
        # Merge file path into metadata
        meta = split.metadata.copy()
        meta["source"] = file_path
        metadatas.append(meta)
        ids.append(f"{file_path}_{i}")
        
    if documents:
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"Added {len(documents)} chunks from {file_path}")

if __name__ == "__main__":
    # Point this to the OKF knowledge directory
    # We will use the docs folder as an example for now
    knowledge_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../docs"))
    ingest_markdown_files(knowledge_dir)

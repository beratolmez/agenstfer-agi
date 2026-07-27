import glob
import os

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

chroma_client = chromadb.PersistentClient(path="./chroma_db")
embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)


def get_or_create_collection():
    return chroma_client.get_or_create_collection(
        name="okf_wiki", embedding_function=embedding_func
    )


def ingest_markdown_files(docs_dir: str):
    """Reads active OKF Markdown files, chunks them, and stores them in ChromaDB."""
    collection = get_or_create_collection()
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    files = glob.glob(os.path.join(docs_dir, "**/*.md"), recursive=True)

    for file_path in files:
        rel_path = os.path.relpath(file_path, docs_dir).replace("\\", "/")
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        md_header_splits = markdown_splitter.split_text(content)
        documents = []
        metadatas = []
        ids = []

        for i, split in enumerate(md_header_splits):
            snippet = str(getattr(split, "page_content", split))[:320]
            documents.append(snippet)
            meta = getattr(split, "metadata", {}).copy() if hasattr(split, "metadata") else {}
            meta["source"] = rel_path
            meta["path"] = rel_path
            meta["title"] = meta.get("Header 1") or os.path.basename(file_path)
            meta["locator"] = f"ev_concept_{rel_path}"
            metadatas.append(meta)
            ids.append(f"{rel_path}_{i}")

        if documents:
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
            )


def ingest_markdown_file(file_path: str):
    """Reads a single active OKF Markdown file, chunks it, and stores it in ChromaDB."""
    docs_dir = os.path.dirname(file_path)
    ingest_markdown_files(docs_dir)


if __name__ == "__main__":
    knowledge_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../../../../knowledge/bundles/company")
    )
    ingest_markdown_files(knowledge_dir)

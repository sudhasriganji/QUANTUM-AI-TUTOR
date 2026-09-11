import os
import shutil
from pathlib import Path
from dotenv import load_dotenv

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# Load environment variables
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)


def get_embeddings():
    """Returns the standardized embedding model matching rag_engine.py."""
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


def build_vector_db():
    docs_file = "scraped_docs.txt"
    chroma_db_dir = "./chroma_db"

    # Create sample document if it doesn't exist
    if not os.path.exists(docs_file):
        print(f"'{docs_file}' not found. Creating sample file...")
        with open(docs_file, "w", encoding="utf-8") as f:
            f.write(
                "IBM Quantum provides access to real quantum hardware "
                "and software tools like Qiskit."
            )

    # Read documents
    with open(docs_file, "r", encoding="utf-8") as f:
        data = f.read()

    if not data.strip():
        print(f"Warning: '{docs_file}' is empty. Skipping DB build.")
        return

    # Split documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    docs = text_splitter.create_documents([data])

    # Remove old vector store to avoid duplication on rebuilds
    if os.path.exists(chroma_db_dir):
        try:
            shutil.rmtree(chroma_db_dir)
            print("Cleared existing Chroma DB.")
        except Exception as e:
            print(f"Could not clear existing Chroma DB directory: {e}")

    # Initialize local embedding model
    embeddings = get_embeddings()

    # Build and persist Chroma Vector DB
    Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=chroma_db_dir
    )

    print("SUCCESS: Vector DB created successfully at ./chroma_db!")


if __name__ == "__main__":
    build_vector_db()
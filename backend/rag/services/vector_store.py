from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


BASE_DIR = Path(__file__).resolve().parent.parent.parent

VECTOR_STORE_DIR = BASE_DIR / "vector_stores"


def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )


def create_resume_vector_store(resume):
    if not resume.extracted_text.strip():
        raise ValueError("Resume does not contain extracted text.")

    document = Document(
        page_content=resume.extracted_text,
        metadata={
            "resume_id": resume.id,
            "user_id": resume.user_id,
            "title": resume.title,
        },
    )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
    )

    chunks = splitter.split_documents([document])

    embeddings = get_embeddings()

    vector_store = FAISS.from_documents(
        chunks,
        embeddings,
    )

    store_path = VECTOR_STORE_DIR / f"resume_{resume.id}"

    store_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    vector_store.save_local(str(store_path))

    return store_path


def load_resume_vector_store(resume_id):
    store_path = VECTOR_STORE_DIR / f"resume_{resume_id}"

    if not store_path.exists():
        raise FileNotFoundError(
            "Vector store for this resume does not exist."
        )

    embeddings = get_embeddings()

    vector_store = FAISS.load_local(
        str(store_path),
        embeddings,
        allow_dangerous_deserialization=True,
    )

    return vector_store
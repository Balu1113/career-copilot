import json
import os
import time
from functools import lru_cache
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings


BASE_DIR = Path(__file__).resolve().parent.parent.parent

VECTOR_STORE_DIR = BASE_DIR / "vector_stores"

META_FILE_NAME = "embedding_meta.json"

CHUNK_SIZE = 800

CHUNK_OVERLAP = 150


def split_text(
    text,
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
):
    """Split text into overlapping chunks.

    Standalone implementation so that importing this module never pulls in
    langchain_text_splitters, which eagerly imports sentence_transformers
    and torch (~400MB) and pushes the Render instance past its 512MB limit.
    """

    text = (text or "").strip()

    if not text:
        return []

    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        if end < len(text):
            window = text[start:end]

            for separator in ("\n\n", "\n", ". ", " "):
                cut = window.rfind(separator)

                if cut > chunk_size // 2:
                    end = start + cut + len(separator)
                    break

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = max(end - chunk_overlap, start + 1)

    return chunks


class GeminiEmbeddings(Embeddings):
    """Embeddings backed by the Gemini embedding API.

    Replaces the local sentence-transformers model so the web process never
    loads torch and stays well inside the Render 512MB memory limit.
    """

    def __init__(self, model=None, dimension=None):
        self.model = model or os.getenv(
            "GEMINI_EMBEDDING_MODEL",
            "models/gemini-embedding-001",
        )

        self.dimension = int(
            dimension
            or os.getenv("GEMINI_EMBEDDING_DIMENSIONS", "768")
        )

        self.batch_size = int(
            os.getenv("GEMINI_EMBEDDING_BATCH_SIZE", "20")
        )

    @staticmethod
    def _client():
        import google.generativeai as genai

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        genai.configure(api_key=api_key)
        return genai

    @staticmethod
    def _normalize(vector):
        import numpy as np

        array = np.asarray(vector, dtype="float32")

        norm = float(np.linalg.norm(array))

        if norm:
            array = array / norm

        return array.tolist()

    def _embed_batch(self, texts, task_type):
        client = self._client()

        last_error = None

        for attempt in range(3):
            try:
                result = client.embed_content(
                    model=self.model,
                    content=texts,
                    task_type=task_type,
                    output_dimensionality=self.dimension,
                )

                vectors = result["embedding"]

                return [
                    self._normalize(vector)
                    for vector in vectors
                ]

            except Exception as exc:
                last_error = exc
                time.sleep(1.5 * (attempt + 1))

        raise RuntimeError(
            f"Failed to generate embeddings: {last_error}"
        )

    def embed_documents(self, texts):
        texts = list(texts)

        vectors = []

        for start in range(0, len(texts), self.batch_size):
            batch = texts[start:start + self.batch_size]

            if batch:
                vectors.extend(
                    self._embed_batch(
                        batch,
                        "RETRIEVAL_DOCUMENT",
                    )
                )

        return vectors

    def embed_query(self, text):
        return self._embed_batch(
            [text],
            "RETRIEVAL_QUERY",
        )[0]


@lru_cache(maxsize=1)
def _build_embeddings():
    provider = os.getenv(
        "EMBEDDINGS_PROVIDER",
        "gemini",
    ).strip().lower()

    if provider == "hf":
        from langchain_huggingface import HuggingFaceEmbeddings

        return HuggingFaceEmbeddings(
            model_name=os.getenv(
                "HF_EMBEDDING_MODEL",
                "sentence-transformers/all-MiniLM-L6-v2",
            )
        )

    return GeminiEmbeddings()


def get_embeddings():
    return _build_embeddings()


def _embedding_signature(embeddings):
    if isinstance(embeddings, GeminiEmbeddings):
        return {
            "provider": "gemini",
            "model": embeddings.model,
            "dimension": embeddings.dimension,
            "normalized": True,
        }

    return {
        "provider": "hf",
        "model": getattr(
            embeddings,
            "model_name",
            "sentence-transformers/all-MiniLM-L6-v2",
        ),
        "normalized": False,
    }


def _read_signature(store_path):
    meta_path = Path(store_path) / META_FILE_NAME

    if not meta_path.exists():
        return None

    try:
        return json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _write_signature(store_path, signature):
    meta_path = Path(store_path) / META_FILE_NAME

    meta_path.write_text(
        json.dumps(signature, indent=2),
        encoding="utf-8",
    )


def _build_vector_store(resume, embeddings):
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

    chunks = split_text(document.page_content)

    documents = [
        Document(
            page_content=chunk,
            metadata=document.metadata,
        )
        for chunk in chunks
    ]

    return FAISS.from_documents(
        documents,
        embeddings,
    )


def create_resume_vector_store(resume):
    embeddings = get_embeddings()

    vector_store = _build_vector_store(resume, embeddings)

    store_path = VECTOR_STORE_DIR / f"resume_{resume.id}"

    store_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    vector_store.save_local(str(store_path))

    _write_signature(
        store_path,
        _embedding_signature(embeddings),
    )

    return store_path


def load_resume_vector_store(resume_id):
    from resumes.models import Resume

    store_path = VECTOR_STORE_DIR / f"resume_{resume_id}"

    embeddings = get_embeddings()
    expected = _embedding_signature(embeddings)

    if store_path.exists():
        signature = _read_signature(store_path)

        if signature == expected:
            try:
                return FAISS.load_local(
                    str(store_path),
                    embeddings,
                    allow_dangerous_deserialization=True,
                )
            except Exception:
                # Corrupt or incompatible index: fall through to rebuild.
                pass

    try:
        resume = Resume.objects.get(id=resume_id)
    except Resume.DoesNotExist:
        raise FileNotFoundError(
            "Vector store for this resume does not exist."
        )

    if not resume.extracted_text.strip():
        raise FileNotFoundError(
            "Vector store for this resume does not exist."
        )

    vector_store = _build_vector_store(resume, embeddings)

    store_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    vector_store.save_local(str(store_path))

    _write_signature(store_path, expected)

    return vector_store

from pathlib import Path
from sentence_transformers import SentenceTransformer

from src.config.logger import StatusLog

CACHE_DIR = Path(__file__).parent.parent.parent / "models/cache" 

class EmbeddingEngine:
    def __init__(self, config: dict):
        model_id = config.get("embedding_model", "nomic-ai/nomic-embed-text-v2-moe")
        self.batch_size = config.get("embedding_batch_size", 512)
        self.task_prefix = "search_document: "

        StatusLog.info(f"Loading embedding model: {model_id}...")
        self.model = SentenceTransformer(
            model_id, 
            trust_remote_code=True, 
            cache_folder=CACHE_DIR
            )
        StatusLog.success("Model loaded.")

    def predict(self, texts: list[str]):
        prefixed_texts = [f"{self.task_prefix}{text}" for text in texts]

        try:
            embeddings = self.model.encode(prefixed_texts, normalize_embeddings=True)
            return embeddings
        except Exception as e:
            StatusLog.fail(f"Encoding failed. Error: {e}")
            raise
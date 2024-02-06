from typing import Dict, Any, List
import numpy.typing as npt
import torch
from chromadb import EmbeddingFunction, Documents, Embeddings


class MemoryEmbeddingFunction(EmbeddingFunction[Documents]):
    # Since we do dynamic imports we have to type this as Any
    models: Dict[str, Any] = {}

    # If you have a beefier machine, try "gtr-t5-large".
    # for a full list of options: https://huggingface.co/sentence-transformers, https://www.sbert.net/docs/pretrained_models.html
    def __init__(
            self,
            model_name: str = "BAAI/bge-m3",
            device: str = "cuda" if torch.cuda.is_available() else "cpu",
            normalize_embeddings: bool = False,
    ):
        if model_name not in self.models:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError:
                raise ValueError(
                    "The sentence_transformers python package is not installed. Please install it with `pip install sentence_transformers`"
                )
            self.models[model_name] = SentenceTransformer(model_name, device=device)
        self._model = self.models[model_name]
        self._normalize_embeddings = normalize_embeddings

    def __call__(self, input: Documents) -> Embeddings:
        return self._model.encode(  # type: ignore
            list(input),
            convert_to_numpy=True,
            normalize_embeddings=self._normalize_embeddings,
        ).tolist()

    def infer_embeddings(self, documents: List[str]) -> npt.NDArray:
        return self._model.encode(  # type: ignore
            list(documents),
            convert_to_numpy=True,
            normalize_embeddings=self._normalize_embeddings,
        )


#
def init_embedding(model_name: str):
    return MemoryEmbeddingFunction(model_name=model_name)

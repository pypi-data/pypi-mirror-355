from .base import AgreementStrategy
from scipy.spatial.distance import cosine

class SemanticAgreement(AgreementStrategy):
    """
    Checks for semantic agreement using the lightweight FastEmbed library locally.
    
    This strategy uses a highly optimized sentence-transformer model (bge-small)
    to generate embeddings and check for semantic similarity. It is designed
    to be fast and efficient, even on CPU.
    """
    _model_cache = {}

    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2", threshold=0.9):
        self.model_name = model_name
        self.threshold = threshold
        self._model = self._get_model()

    def _get_model(self):
        """Lazily loads and caches the FastEmbed model."""
        if self.model_name not in self._model_cache:
            try:
                from fastembed import TextEmbedding
                self._model_cache[self.model_name] = TextEmbedding(model_name=self.model_name)
            except ImportError:
                raise ImportError(
                    "SemanticAgreement requires the 'fastembed' package. "
                    "Please install it with: pip install cascade-inference[semantic]"
                )
        return self._model_cache[self.model_name]

    def check_agreement(self, responses):
        if len(responses) < 2:
            return True
        
        contents = [res.choices[0].message.content for res in responses]
        embeddings = list(self._model.embed(contents))
        
        first_embedding = embeddings[0]
        for other_embedding in embeddings[1:]:
            similarity = 1 - cosine(first_embedding, other_embedding)
            
            if similarity < self.threshold:
                #print(f"Semantic disagreement found (Similarity: {similarity:.4f} < Threshold: {self.threshold})")
                return False
        
        #print(f"Semantic agreement found (All similarities >= {self.threshold})")
        return True 
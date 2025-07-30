import os
from .base import AgreementStrategy

class RemoteSemanticAgreement(AgreementStrategy):
    """
    Checks for semantic agreement by calling the Hugging Face Inference API's
    'sentence-similarity' pipeline. This is the recommended remote strategy.
    """
    def __init__(self, model_name="sentence-transformers/all-mpnet-base-v2", threshold=0.9, api_key=None, api_url=None):
        self.model_name = model_name
        self.threshold = threshold
        self.api_key = api_key or os.getenv("HUGGING_FACE_HUB_TOKEN")
        self.api_url = api_url or f"https://api-inference.huggingface.co/models/{self.model_name}"
        
        if not self.api_key:
            raise ValueError("API key is required. Pass it as 'api_key' or set HUGGING_FACE_HUB_TOKEN.")

    def _get_remote_similarity_scores(self, contents: list[str]):
        """Makes the HTTP request to the sentence-similarity pipeline."""
        try:
            import requests
        except ImportError:
             raise ImportError(
                "RemoteSemanticAgreement requires the 'requests' package. "
                "Please install it with: pip install cascade-inference[remote]"
            )
        
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "inputs": {
                "source_sentence": contents[0],
                "sentences": contents[1:]
            }
        }
        
        response = requests.post(self.api_url, headers=headers, json=payload)
        
        if response.status_code == 200:
            return response.json()
        
        print(f"Error from remote API (Status {response.status_code}): {response.text}")
        return None

    def check_agreement(self, responses):
        if len(responses) < 2:
            return True

        contents = [res.choices[0].message.content for res in responses]
        similarity_scores = self._get_remote_similarity_scores(contents)
        print(similarity_scores)
        
        if not isinstance(similarity_scores, list):
            print("Could not get remote similarity scores. Defaulting to disagreement.")
            return False
            
        for score in similarity_scores:
            if score < self.threshold:
                print(f"Remote semantic disagreement found (Similarity: {score:.4f} < Threshold: {self.threshold})")
                return False
        
        print(f"Remote semantic agreement found (All similarities >= {self.threshold})")
        return True 
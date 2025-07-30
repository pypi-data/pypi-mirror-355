from abc import ABC, abstractmethod

class AgreementStrategy(ABC):
    """
    Abstract base class for all agreement strategies.
    """
    @abstractmethod
    def check_agreement(self, responses):
        """
        Checks for agreement among a list of responses.

        Args:
            responses: A list of response objects from the LLM clients.

        Returns:
            A boolean indicating whether the responses agree.
        """
        pass 
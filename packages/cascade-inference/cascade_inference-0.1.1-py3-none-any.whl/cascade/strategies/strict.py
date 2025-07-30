from .base import AgreementStrategy

class StrictAgreement(AgreementStrategy):
    """
    Checks for strict, character-for-character agreement among responses.
    """
    def check_agreement(self, responses):
        if not responses:
            return False

        first_response_content = responses[0].choices[0].message.content.strip()

        for response in responses[1:]:
            other_response_content = response.choices[0].message.content.strip()
            if other_response_content != first_response_content:
                print(f"Disagreement found:\n  - '{first_response_content}'\n  - '{other_response_content}'")
                return False
        
        print("Strict agreement found.")
        return True 
from typing import List 
from typing import Dict
from typing import Optional

class DeckGen:
    def __init__(self, input_text:Optional[str]=None):
        """
        Initializes the DeckGen class with the input text.
        
        :param input_text: The text input to generate a deck from.
        """
        self.input_text = input_text

    def generate_deck(self)->List[Dict[str, str]]:
        """
        Generates a deck based on the input text.
        :return: List of generated cards. Each card is a dictionary with 'front' and 'back' keys.
        """
        # Placeholder for deck generation logic
        return [
            {"front": "Sample Card Front", "back": "Sample Card Back"}
        ]
"""
Hindi Transliterator
Using the original AI4Bharat model for Roman to Devanagari transliteration
"""

import os
import re
from typing import List, Union
from .hindi_model import XlitPiston


class HindiTransliterator:
    """
    Main interface for Hindi transliteration.
    Handles model loading, configuration, and preprocessing internally.
    """
    def __init__(self):
        # Get the package directory
        package_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Set up paths relative to the package
        self.weight_path = os.path.join(package_dir, "models", "hindi", "hi_111_model.pth")
        self.tglyph_cfg_file = os.path.join(package_dir, "models", "hindi", "hi_scripts.json")
        
        # Initialize the model
        self.model = XlitPiston(
            weight_path=self.weight_path,
            tglyph_cfg_file=self.tglyph_cfg_file
        )

    def transliterate(self, word: str, topk: int = 3) -> Union[str, List[str]]:
        """
        Transliterate a single word from Roman to Devanagari.
        
        Args:
            word (str): The input word in Roman script
            topk (int): Number of transliteration candidates to return (default: 3)
            
        Returns:
            Union[str, List[str]]: If topk=1, returns a single string. Otherwise returns a list of strings.
            
        Raises:
            ValueError: If word is None or not a string
        """
        if word is None:
            raise ValueError("Input word cannot be None")
        if not isinstance(word, str):
            raise ValueError("Input word must be a string")
        if not word:
            return ""
            
        # Check if word contains special characters, digits, or is an email
        if re.search(r'[^a-zA-Z]', word):
            return word
            
        # Pre-process the word
        word = self._pre_process(word)
        
        # Get transliteration candidates
        candidates = self.model.character_model(word, beam_width=topk)
        
        # Post-process the candidates
        candidates = self._post_process(candidates)
        
        # Return single string if topk=1, otherwise return list
        return candidates[0] if topk == 1 else candidates

    def transliterate_batch(self, words: List[str], topk: int = 3) -> List[Union[str, List[str]]]:
        """
        Transliterate a batch of words from Roman to Devanagari.
        
        Args:
            words (List[str]): List of input words in Roman script
            topk (int): Number of transliteration candidates to return per word (default: 3)
            
        Returns:
            List[Union[str, List[str]]]: List of transliterated words. Each word is either a string (if topk=1)
                                        or a list of strings (if topk>1)
                                        
        Raises:
            ValueError: If words is None or not a list
        """
        if words is None:
            raise ValueError("Input words cannot be None")
        if not isinstance(words, list):
            raise ValueError("Input words must be a list")
            
        return [self.transliterate(word, topk) for word in words]

    def _pre_process(self, word: str) -> str:
        """
        Pre-process the input word for word-level transliteration (no language token prefix).
        Args:
            word: Input word to pre-process
        Returns:
            Pre-processed word ready for transliteration
        """
        # Convert to lowercase and strip whitespace
        return word.lower().strip()

    def _post_process(self, results: List[str]) -> List[str]:
        """
        Post-process the transliteration results following AI4Bharat's approach
        Args:
            results: List of transliterated words
        Returns:
            Post-processed list of transliterated words
        """
        processed_results = []
        for result in results:
            # Remove the language token prefix if it exists
            if result.startswith('__hi__'):
                result = result[6:]
            
            # Handle word-final virama (halant) using actual Unicode characters
            result = re.sub(r'([क-हक़-य़])\u094d$', r'\1' + '\u094d\u200c', result)
            
            if result not in processed_results:
                processed_results.append(result)
        return processed_results 
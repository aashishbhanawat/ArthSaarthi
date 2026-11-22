from typing import Dict, List, Optional


class FastEntityMatcher:
    """
    High-performance, pure-Python keyword and entity matching engine
    inspired by FlashText / Aho-Corasick algorithm.

    Operates in O(N) time with respect to document length, avoiding catastrophic
    backtracking of large regex unions. Zero third-party C++ dependencies,
    making it 100% portable across Linux, Docker, Desktop, and Android (Chaquopy).
    """

    _KEYWORD_END = "_KEYWORD_END_"

    def __init__(self, case_sensitive: bool = False):
        self.case_sensitive = case_sensitive
        self.keyword_trie: Dict = {}
        self.total_keywords: int = 0

    def add_keyword(self, keyword: str, clean_name: Optional[str] = None) -> None:
        """
        Adds a keyword or alias to the trie.
        If clean_name is provided, matches will be replaced with clean_name (canonical ticker).
        """
        if not keyword or not keyword.strip():
            return

        keyword = keyword.strip()
        key = keyword if self.case_sensitive else keyword.lower()
        clean = clean_name.strip() if clean_name else keyword

        current_node = self.keyword_trie
        for char in key:
            if char not in current_node:
                current_node[char] = {}
            current_node = current_node[char]

        current_node[self._KEYWORD_END] = clean
        self.total_keywords += 1

    def add_keywords_from_dict(self, keyword_dict: Dict[str, List[str]]) -> None:
        """
        Maps a canonical symbol to a list of alias variations.
        Example: {"TATAMOTORS": ["Tata Motors", "TATA MOTORS LTD", "TATAMOTORS"]}
        """
        for canonical_name, aliases in keyword_dict.items():
            for alias in aliases:
                self.add_keyword(alias, clean_name=canonical_name)

    def extract_keywords(self, text: str) -> List[str]:
        """
        Extracts matched canonical keywords from text with word boundary enforcement.
        Returns unique canonical names preserving encounter order.
        """
        if not text or not self.keyword_trie:
            return []

        processed_text = text if self.case_sensitive else text.lower()
        text_len = len(processed_text)
        matches: List[str] = []
        idx = 0

        # Word boundary characters
        boundary_chars = set(" \t\n\r,.:;!?\"'()[]{}/<>-*&|")

        while idx < text_len:
            # Word boundary check for start of keyword
            if idx > 0 and processed_text[idx - 1] not in boundary_chars:
                idx += 1
                continue

            current_node = self.keyword_trie
            longest_match: Optional[str] = None
            longest_match_end: int = idx

            sub_idx = idx
            while sub_idx < text_len and processed_text[sub_idx] in current_node:
                current_node = current_node[processed_text[sub_idx]]
                sub_idx += 1

                if self._KEYWORD_END in current_node:
                    # Verify trailing word boundary
                    if sub_idx == text_len or processed_text[sub_idx] in boundary_chars:
                        longest_match = current_node[self._KEYWORD_END]
                        longest_match_end = sub_idx

            if longest_match is not None:
                matches.append(longest_match)
                idx = longest_match_end
            else:
                idx += 1

        # Deduplicate while preserving order
        return list(dict.fromkeys(matches))


# Singleton default matcher
entity_matcher = FastEntityMatcher(case_sensitive=False)

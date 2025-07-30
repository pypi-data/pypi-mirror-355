import os
import importlib.resources

class WordReconstructor:
    def __init__(self):
        with importlib.resources.files("letterwise_stt.data").joinpath("words_alpha.txt").open("r") as f:
            self.dictionary = set(word.strip() for word in f if word.strip())
        self.max_word_length = max(len(word) for word in self.dictionary)

    def reconstruct(self, letters_str: str) -> str:
        letters = letters_str.lower().split()
        n = len(letters)

        dp = [None] * (n + 1)
        dp[0] = []

        for i in range(1, n + 1):
            for length in range(1, min(self.max_word_length, i) + 1):
                start = i - length
                candidate = ''.join(letters[start:i])
                if candidate in self.dictionary and dp[start] is not None:
                    if dp[i] is None or len(dp[start]) + 1 < len(dp[i]):
                        dp[i] = dp[start] + [candidate]

        if dp[n] is None:
            return ' '.join(letters)

        return ' '.join(dp[n])

"""
Mandelbrot-Zipf Word Weighting System

Applies information-theoretic weighting to words based on the Mandelbrot distribution
(generalized Zipf's law). Rare, domain-specific words receive higher weight than
common words, improving intent detection and sentiment analysis.

Formula: weight(word) = C / (rank + β)^α

Where:
- rank: word frequency rank (1 = most common)
- α (alpha): frequency decay exponent (higher = more emphasis on rare words)
- β (beta): rank shift parameter (prevents division issues, smooths distribution)
- C: normalization constant
"""

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Optional


class MandelbrotWeighting:
    """
    Mandelbrot-Zipf word weighting for natural language processing.

    Provides frequency-aware word weighting where rare, specific words
    get higher weight than common words.

    Tunable Parameters:
        alpha (α): Decay exponent. Range: 0.5 - 2.0
            - Lower (0.5): Flatter distribution, less difference between common/rare
            - Default (1.0): Standard Zipf-like decay
            - Higher (1.5-2.0): Steep decay, rare words heavily emphasized

        beta (β): Rank shift. Range: 1.0 - 10.0
            - Lower (1.0): Sharper distinction at top ranks
            - Default (2.5): Balanced smoothing
            - Higher (5.0+): Smoother distribution, less extreme weights
    """

    # Default English stopwords (low information value)
    DEFAULT_STOPWORDS = {
        "a",
        "an",
        "the",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "must",
        "shall",
        "can",
        "need",
        "dare",
        "to",
        "of",
        "in",
        "for",
        "on",
        "with",
        "at",
        "by",
        "from",
        "as",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "between",
        "under",
        "again",
        "further",
        "then",
        "once",
        "here",
        "there",
        "when",
        "where",
        "why",
        "how",
        "all",
        "each",
        "few",
        "more",
        "most",
        "other",
        "some",
        "such",
        "no",
        "nor",
        "not",
        "only",
        "own",
        "same",
        "so",
        "than",
        "too",
        "very",
        "just",
        "and",
        "but",
        "if",
        "or",
        "because",
        "until",
        "while",
        "about",
        "against",
        "i",
        "me",
        "my",
        "myself",
        "we",
        "our",
        "ours",
        "ourselves",
        "you",
        "your",
        "yours",
        "yourself",
        "yourselves",
        "he",
        "him",
        "his",
        "himself",
        "she",
        "her",
        "hers",
        "herself",
        "it",
        "its",
        "itself",
        "they",
        "them",
        "their",
        "theirs",
        "themselves",
        "what",
        "which",
        "who",
        "whom",
        "this",
        "that",
        "these",
        "those",
        "am",
        "get",
        "got",
        "gets",
        "getting",
        "going",
        "go",
        "goes",
        "went",
    }

    def __init__(
        self,
        alpha: float = 1.0,
        beta: float = 2.5,
        min_weight: float = 0.1,
        max_weight: float = 5.0,
        use_stopwords: bool = True,
        custom_stopwords: Optional[set] = None,
        corpus_path: Optional[str] = None,
    ):
        """
        Initialize the Mandelbrot weighting system.

        Args:
            alpha: Frequency decay exponent (0.5-2.0, default 1.0)
            beta: Rank shift parameter (1.0-10.0, default 2.5)
            min_weight: Minimum weight floor (default 0.1)
            max_weight: Maximum weight ceiling (default 5.0)
            use_stopwords: Whether to apply low weight to stopwords
            custom_stopwords: Additional stopwords to include
            corpus_path: Path to save/load frequency corpus
        """
        self.alpha = alpha
        self.beta = beta
        self.min_weight = min_weight
        self.max_weight = max_weight
        self.use_stopwords = use_stopwords

        # Stopwords get minimum weight
        self.stopwords = self.DEFAULT_STOPWORDS.copy()
        if custom_stopwords:
            self.stopwords.update(custom_stopwords)

        # Word frequency corpus
        self.word_frequencies: Counter = Counter()
        self.total_words: int = 0
        self.corpus_path = Path(corpus_path) if corpus_path else None

        # Cached rankings (rebuilt when corpus changes significantly)
        self._word_ranks: dict[str, int] = {}
        self._cache_valid = False
        self._last_corpus_size = 0

        # Domain-specific boost words (manually curated high-value terms)
        self.domain_boost_words: dict[str, float] = {}

        # Load existing corpus if available
        if self.corpus_path and self.corpus_path.exists():
            self._load_corpus()

    def configure(
        self,
        alpha: Optional[float] = None,
        beta: Optional[float] = None,
        min_weight: Optional[float] = None,
        max_weight: Optional[float] = None,
    ):
        """
        Adjust tuning parameters at runtime.

        Args:
            alpha: New decay exponent (0.5-2.0)
            beta: New rank shift (1.0-10.0)
            min_weight: New minimum weight floor
            max_weight: New maximum weight ceiling
        """
        if alpha is not None:
            self.alpha = max(0.1, min(3.0, alpha))
        if beta is not None:
            self.beta = max(0.5, min(20.0, beta))
        if min_weight is not None:
            self.min_weight = max(0.01, min(1.0, min_weight))
        if max_weight is not None:
            self.max_weight = max(1.0, min(100.0, max_weight))

        # Invalidate cache since parameters changed
        self._cache_valid = False

    def add_domain_boost(self, words: dict[str, float]):
        """
        Add domain-specific words with manual weight boosts.

        Args:
            words: Dict mapping words to boost multipliers (e.g., {"ephemeral": 2.0})
        """
        self.domain_boost_words.update(words)

    def tokenize(self, text: str) -> list[str]:
        """
        Tokenize text into lowercase words.

        Args:
            text: Input text

        Returns:
            List of lowercase word tokens
        """
        # Simple word tokenization - extract alphanumeric sequences
        words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
        return words

    def update_corpus(self, text: str):
        """
        Add text to the frequency corpus.

        Args:
            text: Text to add to corpus
        """
        words = self.tokenize(text)
        self.word_frequencies.update(words)
        self.total_words += len(words)

        # Invalidate cache if corpus grew significantly
        if self.total_words > self._last_corpus_size * 1.2:
            self._cache_valid = False

    def update_corpus_batch(self, texts: list[str]):
        """
        Add multiple texts to the frequency corpus efficiently.

        Args:
            texts: List of texts to add
        """
        all_words = []
        for text in texts:
            all_words.extend(self.tokenize(text))

        self.word_frequencies.update(all_words)
        self.total_words += len(all_words)
        self._cache_valid = False

    def _rebuild_rankings(self):
        """Rebuild word rank cache from frequency data."""
        if not self.word_frequencies:
            self._word_ranks = {}
            self._cache_valid = True
            self._last_corpus_size = 0
            return

        # Sort by frequency (most common = rank 1)
        sorted_words = self.word_frequencies.most_common()
        self._word_ranks = {word: rank + 1 for rank, (word, _) in enumerate(sorted_words)}
        self._cache_valid = True
        self._last_corpus_size = self.total_words

    def get_rank(self, word: str) -> int:
        """
        Get the frequency rank of a word (1 = most common).

        Args:
            word: Word to look up

        Returns:
            Rank (1-based) or estimated rank for unknown words
        """
        word = word.lower()

        if not self._cache_valid:
            self._rebuild_rankings()

        if word in self._word_ranks:
            return self._word_ranks[word]

        # Unknown word - assign rank beyond known vocabulary
        # This gives unknown words high weight (they're rare/specific)
        return len(self._word_ranks) + 100

    def compute_weight(self, word: str) -> float:
        """
        Compute the Mandelbrot weight for a single word.

        Formula: weight = C / (rank + β)^α

        Args:
            word: Word to weight

        Returns:
            Weight value (higher = more important)
        """
        word = word.lower()

        # Stopwords get minimum weight
        if self.use_stopwords and word in self.stopwords:
            return self.min_weight

        # Get frequency rank
        rank = self.get_rank(word)

        # Mandelbrot formula (inverted so rare words get high weight)
        # Standard: P(r) = C / (r + β)^α gives probability (high for common)
        # We want: weight high for rare, so we use rank directly
        raw_weight = 1.0 / math.pow(rank + self.beta, self.alpha)

        # Normalize to make rare words have higher weight
        # Invert: low raw_weight (rare) → high final weight
        if self.word_frequencies:
            max_rank = len(self.word_frequencies) + 100
            max_raw = 1.0 / math.pow(1 + self.beta, self.alpha)
            min_raw = 1.0 / math.pow(max_rank + self.beta, self.alpha)

            # Scale so rare words (low raw) get high weight
            if max_raw > min_raw:
                normalized = 1.0 - (raw_weight - min_raw) / (max_raw - min_raw)
            else:
                normalized = 0.5
        else:
            # No corpus yet - use raw weight inverted
            normalized = 1.0 - raw_weight

        # Scale to weight range
        weight = self.min_weight + normalized * (self.max_weight - self.min_weight)

        # Apply domain boost if applicable
        if word in self.domain_boost_words:
            weight *= self.domain_boost_words[word]

        # Clamp to bounds
        return max(self.min_weight, min(self.max_weight, weight))

    def weight_words(self, text: str) -> list[tuple[str, float]]:
        """
        Tokenize text and compute weights for all words.

        Args:
            text: Input text

        Returns:
            List of (word, weight) tuples
        """
        words = self.tokenize(text)
        return [(word, self.compute_weight(word)) for word in words]

    def weighted_word_score(
        self, text: str, target_words: list[str], normalize: bool = True
    ) -> float:
        """
        Compute weighted score for presence of target words in text.

        This replaces simple word counting with frequency-aware scoring.

        Args:
            text: Text to analyze
            target_words: Words to look for
            normalize: Whether to normalize by total weight

        Returns:
            Weighted score (0.0-1.0 if normalized)
        """
        words = self.tokenize(text)
        word_set = set(words)

        matched_weight = 0.0
        total_target_weight = 0.0

        for target in target_words:
            target_lower = target.lower()
            weight = self.compute_weight(target_lower)
            total_target_weight += weight

            if target_lower in word_set:
                matched_weight += weight

        if normalize and total_target_weight > 0:
            return matched_weight / total_target_weight

        return matched_weight

    def weighted_sentiment_score(
        self, text: str, positive_words: list[str], negative_words: list[str]
    ) -> float:
        """
        Compute weighted sentiment score.

        Args:
            text: Text to analyze
            positive_words: Positive sentiment words
            negative_words: Negative sentiment words

        Returns:
            Sentiment score (-1.0 to 1.0)
        """
        words = self.tokenize(text)
        word_set = set(words)

        pos_weight = 0.0
        neg_weight = 0.0

        for word in positive_words:
            if word.lower() in word_set:
                pos_weight += self.compute_weight(word.lower())

        for word in negative_words:
            if word.lower() in word_set:
                neg_weight += self.compute_weight(word.lower())

        total = pos_weight + neg_weight
        if total == 0:
            return 0.0

        return (pos_weight - neg_weight) / total

    def get_top_weighted_words(self, text: str, n: int = 10) -> list[tuple[str, float]]:
        """
        Get the top N highest-weighted words from text.

        Args:
            text: Input text
            n: Number of top words to return

        Returns:
            List of (word, weight) tuples sorted by weight descending
        """
        weighted = self.weight_words(text)
        # Remove duplicates, keeping highest weight
        word_weights = {}
        for word, weight in weighted:
            if word not in word_weights or weight > word_weights[word]:
                word_weights[word] = weight

        sorted_words = sorted(word_weights.items(), key=lambda x: x[1], reverse=True)
        return sorted_words[:n]

    def compute_text_importance(self, text: str) -> float:
        """
        Compute overall importance score for text based on word weights.

        High score = text contains many rare/specific words
        Low score = text is mostly common words

        Args:
            text: Input text

        Returns:
            Importance score (0.0-1.0)
        """
        weighted = self.weight_words(text)
        if not weighted:
            return 0.5

        total_weight = sum(w for _, w in weighted)
        avg_weight = total_weight / len(weighted)

        # Normalize to 0-1 range
        normalized = (avg_weight - self.min_weight) / (self.max_weight - self.min_weight)
        return max(0.0, min(1.0, normalized))

    def save_corpus(self, path: Optional[str] = None):
        """
        Save the frequency corpus to disk.

        Args:
            path: Override path (uses self.corpus_path if not specified)
        """
        save_path = Path(path) if path else self.corpus_path
        if not save_path:
            return

        save_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "alpha": self.alpha,
            "beta": self.beta,
            "min_weight": self.min_weight,
            "max_weight": self.max_weight,
            "total_words": self.total_words,
            "frequencies": dict(self.word_frequencies.most_common(10000)),  # Top 10k
            "domain_boosts": self.domain_boost_words,
        }

        with open(save_path, "w") as f:
            json.dump(data, f, indent=2)

    def _load_corpus(self):
        """Load frequency corpus from disk."""
        if not self.corpus_path or not self.corpus_path.exists():
            return

        try:
            with open(self.corpus_path) as f:
                data = json.load(f)

            self.alpha = data.get("alpha", self.alpha)
            self.beta = data.get("beta", self.beta)
            self.min_weight = data.get("min_weight", self.min_weight)
            self.max_weight = data.get("max_weight", self.max_weight)
            self.total_words = data.get("total_words", 0)
            self.word_frequencies = Counter(data.get("frequencies", {}))
            self.domain_boost_words = data.get("domain_boosts", {})
            self._cache_valid = False

        except Exception as e:
            print(f"⚠️  Failed to load Mandelbrot corpus: {e}")

    def get_stats(self) -> dict:
        """
        Get statistics about the weighting system.

        Returns:
            Dict with corpus and parameter stats
        """
        return {
            "alpha": self.alpha,
            "beta": self.beta,
            "min_weight": self.min_weight,
            "max_weight": self.max_weight,
            "corpus_size": self.total_words,
            "unique_words": len(self.word_frequencies),
            "domain_boost_count": len(self.domain_boost_words),
            "stopword_count": len(self.stopwords),
        }

    def explain_weight(self, word: str) -> dict:
        """
        Explain why a word has its weight (for debugging/tuning).

        Args:
            word: Word to explain

        Returns:
            Dict with weight breakdown
        """
        word = word.lower()
        rank = self.get_rank(word)
        weight = self.compute_weight(word)
        frequency = self.word_frequencies.get(word, 0)

        return {
            "word": word,
            "weight": weight,
            "rank": rank,
            "frequency": frequency,
            "is_stopword": word in self.stopwords,
            "has_domain_boost": word in self.domain_boost_words,
            "domain_boost": self.domain_boost_words.get(word, 1.0),
            "params": {"alpha": self.alpha, "beta": self.beta},
        }

"""
Verbosity Analyzer v2.0

Analyzes prompt length, redundancy, and identifies critical directive placement.
Helps developers identify when prompts are too verbose or when important
directives are buried in excessive text.

Key Metrics:
1. Length - Total word count and token estimate
2. Redundancy - Repeated phrases and concepts
3. Directive Placement - Where critical MUST/NEVER appear
4. Information Density - Ratio of meaningful content to total length
"""

import re
import numpy as np
from typing import List, Dict, Tuple, Set
from dataclasses import dataclass
from collections import Counter


@dataclass
class VerbosityMetrics:
    """Results of verbosity analysis"""
    total_words: int
    total_sentences: int
    estimated_tokens: int

    # Redundancy analysis
    redundancy_score: float  # 0-10, higher = more redundant
    repeated_phrases: List[Tuple[str, int]]  # (phrase, count)
    redundant_sentences: List[str]

    # Directive placement
    critical_directives: List[Dict]  # [{text, position, word_num}]
    buried_directives: List[Dict]  # Directives after word 100

    # Information density
    information_density: float  # 0-1, higher = more dense
    filler_ratio: float  # 0-1, ratio of filler words

    # Overall assessment
    verbosity_score: float  # 0-10, higher = too verbose
    interpretation: str
    recommendations: List[str]


class VerbosityAnalyzer:
    """
    Analyzes prompt verbosity and identifies opportunities for optimization.

    Purpose:
    - Detect excessively long prompts that may confuse LLMs
    - Identify redundant phrasing
    - Find buried critical directives
    - Calculate information density
    """

    # Common filler phrases that add length but little value
    FILLER_PHRASES = [
        "it is important that",
        "you should always",
        "make sure to",
        "remember to",
        "it's important to",
        "you need to",
        "be sure to",
        "don't forget to",
        "keep in mind",
        "take note that",
        "please note that",
        "it should be noted",
        "as mentioned before",
        "as stated earlier"
    ]

    # Critical directive keywords
    CRITICAL_KEYWORDS = [
        "must", "must not", "never", "always", "prohibited",
        "required", "mandatory", "forbidden", "critical",
        "essential", "do not", "cannot", "shall not"
    ]

    # Optimal ranges
    OPTIMAL_WORD_COUNT = (50, 150)  # Sweet spot for system prompts
    MAX_RECOMMENDED_WORDS = 200
    CRITICAL_DIRECTIVE_POSITION_THRESHOLD = 100  # Words

    def __init__(self, embedding_manager=None):
        """
        Initialize analyzer.

        Args:
            embedding_manager: Optional, for semantic redundancy detection
        """
        self.embeddings = embedding_manager

    def analyze(self, prompt: str) -> VerbosityMetrics:
        """
        Perform complete verbosity analysis.

        Args:
            prompt: Input prompt text

        Returns:
            VerbosityMetrics with complete analysis
        """
        # Basic metrics
        words = self._tokenize_words(prompt)
        sentences = self._tokenize_sentences(prompt)

        total_words = len(words)
        total_sentences = len(sentences)
        estimated_tokens = self._estimate_tokens(prompt)

        # Redundancy analysis
        redundancy_score, repeated_phrases, redundant_sentences = \
            self._analyze_redundancy(prompt, sentences)

        # Directive placement
        critical_directives, buried_directives = \
            self._analyze_directive_placement(prompt, words)

        # Information density
        information_density, filler_ratio = \
            self._calculate_information_density(prompt, words)

        # Overall verbosity score
        verbosity_score = self._calculate_verbosity_score(
            total_words,
            redundancy_score,
            information_density,
            len(buried_directives)
        )

        # Interpretation
        interpretation = self._interpret_verbosity(verbosity_score, total_words)

        # Recommendations
        recommendations = self._generate_recommendations(
            total_words,
            redundancy_score,
            len(buried_directives),
            information_density
        )

        return VerbosityMetrics(
            total_words=total_words,
            total_sentences=total_sentences,
            estimated_tokens=estimated_tokens,
            redundancy_score=round(redundancy_score, 1),
            repeated_phrases=repeated_phrases[:10],  # Top 10
            redundant_sentences=redundant_sentences[:5],  # Top 5
            critical_directives=critical_directives,
            buried_directives=buried_directives,
            information_density=round(information_density, 2),
            filler_ratio=round(filler_ratio, 2),
            verbosity_score=round(verbosity_score, 1),
            interpretation=interpretation,
            recommendations=recommendations
        )

    def _tokenize_words(self, text: str) -> List[str]:
        """Split text into words"""
        # Simple word tokenization
        words = re.findall(r'\b\w+\b', text.lower())
        return words

    def _tokenize_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Split on sentence boundaries
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences

    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count (rough approximation).

        Rule of thumb: ~0.75 tokens per word for English
        """
        words = self._tokenize_words(text)
        return int(len(words) * 0.75)

    def _analyze_redundancy(
        self,
        prompt: str,
        sentences: List[str]
    ) -> Tuple[float, List[Tuple[str, int]], List[str]]:
        """
        Analyze prompt for redundant content.

        Returns:
            (redundancy_score, repeated_phrases, redundant_sentences)
        """
        # Find repeated n-grams (phrases)
        repeated_phrases = self._find_repeated_ngrams(prompt)

        # Find redundant sentences (similar meaning)
        redundant_sentences = self._find_redundant_sentences(sentences)

        # Calculate redundancy score
        redundancy_score = 0.0

        # Factor 1: Repeated phrases
        if repeated_phrases:
            # More repeated phrases = higher redundancy
            phrase_score = min(len(repeated_phrases) / 5, 1.0) * 4.0
            redundancy_score += phrase_score

        # Factor 2: Redundant sentences
        if redundant_sentences:
            sentence_score = min(len(redundant_sentences) / 3, 1.0) * 3.0
            redundancy_score += sentence_score

        # Factor 3: Filler phrases
        filler_count = sum(
            1 for phrase in self.FILLER_PHRASES
            if phrase in prompt.lower()
        )
        filler_score = min(filler_count / 3, 1.0) * 3.0
        redundancy_score += filler_score

        return redundancy_score, repeated_phrases, redundant_sentences

    def _find_repeated_ngrams(self, text: str, n: int = 3) -> List[Tuple[str, int]]:
        """Find repeated phrases (n-grams)"""
        words = self._tokenize_words(text)

        # Generate n-grams
        ngrams = []
        for i in range(len(words) - n + 1):
            ngram = ' '.join(words[i:i+n])
            ngrams.append(ngram)

        # Count occurrences
        ngram_counts = Counter(ngrams)

        # Filter to only repeated (count > 1)
        repeated = [
            (ngram, count)
            for ngram, count in ngram_counts.items()
            if count > 1
        ]

        # Sort by count (descending)
        repeated.sort(key=lambda x: x[1], reverse=True)

        return repeated

    def _find_redundant_sentences(self, sentences: List[str]) -> List[str]:
        """
        Find sentences that convey similar information.

        Uses simple keyword overlap for now.
        Could be enhanced with semantic similarity using embeddings.
        """
        redundant = []

        # Compare each pair of sentences
        for i, sent1 in enumerate(sentences):
            for sent2 in sentences[i+1:]:
                # Calculate word overlap
                words1 = set(self._tokenize_words(sent1))
                words2 = set(self._tokenize_words(sent2))

                if not words1 or not words2:
                    continue

                # Jaccard similarity
                overlap = len(words1 & words2) / len(words1 | words2)

                # If >50% overlap, likely redundant
                if overlap > 0.5:
                    # Mark longer sentence as redundant
                    if len(sent1) > len(sent2):
                        if sent1 not in redundant:
                            redundant.append(sent1)
                    else:
                        if sent2 not in redundant:
                            redundant.append(sent2)

        return redundant

    def _analyze_directive_placement(
        self,
        prompt: str,
        words: List[str]
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Analyze where critical directives appear in the prompt.

        Returns:
            (all_directives, buried_directives)
        """
        critical_directives = []
        buried_directives = []

        # Find sentences containing critical keywords
        sentences = self._tokenize_sentences(prompt)

        current_word_position = 0

        for sentence in sentences:
            sentence_words = self._tokenize_words(sentence)
            sentence_lower = sentence.lower()

            # Check for critical keywords
            for keyword in self.CRITICAL_KEYWORDS:
                if keyword in sentence_lower:
                    directive = {
                        'text': sentence.strip(),
                        'keyword': keyword,
                        'position': current_word_position,
                        'sentence_num': len(critical_directives) + 1
                    }

                    critical_directives.append(directive)

                    # Check if buried (after threshold)
                    if current_word_position > self.CRITICAL_DIRECTIVE_POSITION_THRESHOLD:
                        buried_directives.append(directive)

                    break  # One directive per sentence

            current_word_position += len(sentence_words)

        return critical_directives, buried_directives

    def _calculate_information_density(
        self,
        prompt: str,
        words: List[str]
    ) -> Tuple[float, float]:
        """
        Calculate information density (meaningful content ratio).

        Returns:
            (information_density, filler_ratio)
        """
        total_words = len(words)

        if total_words == 0:
            return 0.0, 0.0

        # Count filler words/phrases
        filler_count = 0
        prompt_lower = prompt.lower()

        for filler in self.FILLER_PHRASES:
            filler_count += len(re.findall(re.escape(filler), prompt_lower))

        # Estimate filler word count
        avg_filler_length = 4  # Average words per filler phrase
        filler_word_count = filler_count * avg_filler_length

        # Filler ratio
        filler_ratio = min(filler_word_count / total_words, 1.0)

        # Information density (inverse of filler ratio, adjusted)
        # Also factor in sentence complexity
        avg_sentence_length = total_words / max(len(self._tokenize_sentences(prompt)), 1)

        # Optimal sentence length is 15-25 words
        if 15 <= avg_sentence_length <= 25:
            sentence_score = 1.0
        elif avg_sentence_length < 15:
            sentence_score = 0.8  # Too short, might be choppy
        else:
            # Penalize very long sentences
            sentence_score = max(0.3, 1.0 - (avg_sentence_length - 25) / 50)

        information_density = (1 - filler_ratio) * sentence_score

        return information_density, filler_ratio

    def _calculate_verbosity_score(
        self,
        total_words: int,
        redundancy_score: float,
        information_density: float,
        buried_count: int
    ) -> float:
        """
        Calculate overall verbosity score (0-10).

        Higher score = more verbose (worse)
        """
        score = 0.0

        # Factor 1: Length (40%)
        if total_words <= self.OPTIMAL_WORD_COUNT[1]:
            length_score = 0.0  # Optimal
        elif total_words <= self.MAX_RECOMMENDED_WORDS:
            # Moderate length
            length_score = 3.0 * (
                (total_words - self.OPTIMAL_WORD_COUNT[1]) /
                (self.MAX_RECOMMENDED_WORDS - self.OPTIMAL_WORD_COUNT[1])
            )
        else:
            # Too long
            excess = total_words - self.MAX_RECOMMENDED_WORDS
            length_score = 3.0 + min(excess / 100, 7.0)

        score += length_score * 0.4

        # Factor 2: Redundancy (30%)
        score += redundancy_score * 0.3

        # Factor 3: Information density (20%)
        # Low density = high verbosity
        density_score = (1 - information_density) * 10
        score += density_score * 0.2

        # Factor 4: Buried directives (10%)
        burial_penalty = min(buried_count * 2, 10)
        score += burial_penalty * 0.1

        return min(score, 10.0)

    def _interpret_verbosity(self, score: float, word_count: int) -> str:
        """Generate human-readable interpretation"""
        if score <= 2.0:
            return f"Excellent - Concise and clear ({word_count} words)"
        elif score <= 4.0:
            return f"Good - Acceptable length ({word_count} words)"
        elif score <= 6.0:
            return f"Moderate - Could be more concise ({word_count} words)"
        elif score <= 8.0:
            return f"Verbose - Needs significant reduction ({word_count} words)"
        else:
            return f"Extremely Verbose - Major reduction needed ({word_count} words)"

    def _generate_recommendations(
        self,
        total_words: int,
        redundancy_score: float,
        buried_count: int,
        information_density: float
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        # Length recommendations
        if total_words > self.MAX_RECOMMENDED_WORDS:
            target = self.OPTIMAL_WORD_COUNT[1]
            reduction = total_words - target
            reduction_pct = int((reduction / total_words) * 100)
            recommendations.append(
                f"Reduce length by ~{reduction} words ({reduction_pct}%) to reach optimal {target} words"
            )

        # Redundancy recommendations
        if redundancy_score > 5.0:
            recommendations.append(
                "Remove redundant phrases and consolidate similar instructions"
            )

        # Buried directives
        if buried_count > 0:
            recommendations.append(
                f"Move {buried_count} critical directive(s) to the beginning of prompt"
            )

        # Information density
        if information_density < 0.5:
            recommendations.append(
                "Remove filler phrases (e.g., 'make sure to', 'remember that')"
            )

        # General optimization
        if total_words > self.OPTIMAL_WORD_COUNT[1]:
            recommendations.append(
                "Use bullet points for rules instead of verbose paragraphs"
            )

        return recommendations


def print_verbosity_analysis(metrics: VerbosityMetrics):
    """Pretty print verbosity analysis results"""
    print("\n" + "="*70)
    print("VERBOSITY ANALYSIS")
    print("="*70)

    print(f"\nOverall Score: {metrics.verbosity_score}/10")
    print(f"Interpretation: {metrics.interpretation}")

    print(f"\nLength Metrics:")
    print(f"  Total Words: {metrics.total_words}")
    print(f"  Total Sentences: {metrics.total_sentences}")
    print(f"  Estimated Tokens: {metrics.estimated_tokens}")

    print(f"\nQuality Metrics:")
    print(f"  Redundancy Score: {metrics.redundancy_score}/10")
    print(f"  Information Density: {metrics.information_density:.0%}")
    print(f"  Filler Ratio: {metrics.filler_ratio:.0%}")

    if metrics.repeated_phrases:
        print(f"\nRepeated Phrases ({len(metrics.repeated_phrases)}):")
        for phrase, count in metrics.repeated_phrases[:5]:
            print(f"  - \"{phrase}\" (appears {count} times)")

    if metrics.critical_directives:
        print(f"\nCritical Directives ({len(metrics.critical_directives)}):")
        for directive in metrics.critical_directives[:3]:
            print(f"  - Word {directive['position']}: \"{directive['text'][:60]}...\"")

    if metrics.buried_directives:
        print(f"\n[!] Buried Directives ({len(metrics.buried_directives)}):")
        for directive in metrics.buried_directives:
            print(f"  - Word {directive['position']}: \"{directive['text'][:60]}...\"")
            print(f"    WARNING: Critical directive appears too late in prompt")

    if metrics.recommendations:
        print(f"\nRecommendations:")
        for i, rec in enumerate(metrics.recommendations, 1):
            print(f"  {i}. {rec}")

    print("="*70)

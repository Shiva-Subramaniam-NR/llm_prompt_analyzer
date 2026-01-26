"""
High Weightage Word Extractor v2.0
Pattern-based and NLP-based extraction (no exhaustive word lists)

Key Improvements:
- Uses spaCy NER for automatic entity recognition
- Pattern-based detection for structural elements
- Only ~60 words in functional keyword lists
- Scales to any domain without adding word lists
"""

import re
import spacy
from typing import List, Dict
from dataclasses import dataclass


@dataclass
class WeightageWord:
    """Represents a high-weightage word/phrase"""
    text: str
    weightage: float
    word_type: str
    specificity: float
    constraint_power: float
    replaceability: float
    extraction_method: str  # 'spacy_ner', 'pattern', 'keyword'


class WeightageExtractorV2:
    """
    Extract high-weightage words using NLP and patterns
    No exhaustive word lists needed!
    """
    
    # Small functional word lists (only ~60 words total)
    HARD_CONSTRAINTS = [
        'must', 'must not', 'should not', 'cannot', 'won\'t',
        'not more than', 'not less than', 'not later than', 'not earlier than',
        'before', 'after', 'by', 'within', 'exactly', 'only',
        'maximum', 'minimum', 'at most', 'at least', 'no more than'
    ]
    
    SOFT_CONSTRAINTS = [
        'prefer', 'preferably', 'ideally', 'would like', 'like to',
        'hoping', 'if possible', 'try to', 'better if', 'wish to',
        'want to', 'hoping for'
    ]
    
    VAGUE_QUALIFIERS = [
        # Temporal
        'morning', 'afternoon', 'evening', 'night', 'early', 'late',
        'soon', 'later', 'sometime', 'eventually',
        # Quantifiers
        'some', 'few', 'many', 'several', 'around', 'approximately',
        'roughly', 'about', 'couple',
        # Quality
        'good', 'nice', 'comfortable', 'decent', 'reasonable',
        'cheap', 'expensive', 'better', 'best',
        # Indefinite
        'any', 'either', 'whatever', 'anything', 'flexible'
    ]
    
    FILLER_WORDS = [
        'please', 'kindly', 'thanks', 'thank you', 'could you',
        'would you', 'can you', 'may i'
    ]
    
    def __init__(self, domain_config=None):
        """
        Initialize extractor
        
        Args:
            domain_config: Optional domain configuration (for future extension)
        """
        self.domain_config = domain_config
        
        # Load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
            print("[OK] spaCy model loaded successfully")
        except OSError:
            print("[WARNING] spaCy model not found. Please install:")
            print("          python -m spacy download en_core_web_sm")
            self.nlp = None
    
    def extract(self, prompt: str) -> List[WeightageWord]:
        """
        Extract high-weightage words from prompt
        
        Args:
            prompt: Input prompt text
            
        Returns:
            List of WeightageWord objects with scores >= 0.6
        """
        if not self.nlp:
            raise RuntimeError("spaCy model not loaded. Cannot extract entities.")
        
        all_candidates = []
        
        # Method 1: Extract named entities using spaCy NER
        entity_words = self._extract_named_entities(prompt)
        all_candidates.extend(entity_words)
        
        # Method 2: Extract constraint phrases using patterns
        constraint_words = self._extract_constraints(prompt)
        all_candidates.extend(constraint_words)
        
        # Method 3: Extract important tokens using POS tags
        important_tokens = self._extract_important_tokens(prompt)
        all_candidates.extend(important_tokens)
        
        # Calculate final scores for all candidates
        scored_words = self._calculate_scores(all_candidates)
        
        # Filter to high-weightage only (>= 0.6)
        high_weightage = [w for w in scored_words if w.weightage >= 0.6]
        
        # Deduplicate and sort
        high_weightage = self._deduplicate(high_weightage)
        high_weightage.sort(key=lambda x: x.weightage, reverse=True)
        
        return high_weightage
    
    def _extract_named_entities(self, prompt: str) -> List[WeightageWord]:
        """
        Extract named entities using spaCy NER
        No word lists needed - spaCy recognizes entities automatically!
        
        Entity types spaCy recognizes:
        - GPE: Geopolitical entities (cities, countries)
        - DATE: Dates in any format
        - TIME: Times
        - MONEY: Monetary values
        - CARDINAL: Numbers
        - PERSON: People names
        - ORG: Organizations
        """
        doc = self.nlp(prompt)
        entities = []
        
        for ent in doc.ents:
            # Map spaCy entity type to our category
            category = self._map_entity_type(ent.label_)
            
            if category:  # Only process relevant entity types
                entities.append(WeightageWord(
                    text=ent.text,
                    weightage=0.0,  # Will be calculated later
                    word_type=category,
                    specificity=0.0,
                    constraint_power=0.0,
                    replaceability=0.0,
                    extraction_method='spacy_ner'
                ))
        
        return entities
    
    def _map_entity_type(self, spacy_label: str) -> str:
        """
        Map spaCy entity labels to our semantic categories
        """
        mapping = {
            'GPE': 'location',           # Geopolitical entity (city, country)
            'LOC': 'location',           # Non-GPE locations
            'FAC': 'location',           # Facilities
            'DATE': 'date',              # Dates
            'TIME': 'time',              # Times
            'MONEY': 'amount',           # Monetary values
            'CARDINAL': 'number',        # Numbers
            'QUANTITY': 'number',        # Quantities
            'ORDINAL': 'ordinal',        # 1st, 2nd, etc.
            'PERSON': 'person',          # People
            'ORG': 'organization',       # Organizations
            'PRODUCT': 'product',        # Products
        }
        
        return mapping.get(spacy_label, None)
    
    def _extract_constraints(self, prompt: str) -> List[WeightageWord]:
        """
        Extract constraint phrases using pattern matching
        Uses small keyword lists (~20 words) to find constraint indicators
        """
        constraints = []
        
        # Extract hard constraints
        for keyword in self.HARD_CONSTRAINTS:
            # Pattern: keyword + next 2-5 words (constraint phrase)
            pattern = rf'\b{re.escape(keyword)}\b\s+(?:\w+\s+){{0,5}}\w+'
            matches = re.finditer(pattern, prompt, re.IGNORECASE)
            
            for match in matches:
                constraints.append(WeightageWord(
                    text=match.group(0).strip(),
                    weightage=0.0,
                    word_type='hard_constraint',
                    specificity=0.0,
                    constraint_power=0.0,
                    replaceability=0.0,
                    extraction_method='pattern'
                ))
        
        # Extract soft constraints
        for keyword in self.SOFT_CONSTRAINTS:
            pattern = rf'\b{re.escape(keyword)}\b\s+(?:\w+\s+){{0,5}}\w+'
            matches = re.finditer(pattern, prompt, re.IGNORECASE)
            
            for match in matches:
                constraints.append(WeightageWord(
                    text=match.group(0).strip(),
                    weightage=0.0,
                    word_type='soft_constraint',
                    specificity=0.0,
                    constraint_power=0.0,
                    replaceability=0.0,
                    extraction_method='pattern'
                ))
        
        return constraints
    
    def _extract_important_tokens(self, prompt: str) -> List[WeightageWord]:
        """
        Extract important tokens using POS (Part of Speech) tags
        Focuses on content words: nouns, verbs, adjectives with numeric values
        """
        doc = self.nlp(prompt)
        important = []
        
        for token in doc:
            # Skip stopwords and punctuation
            if token.is_stop or token.is_punct or token.is_space:
                continue
            
            # Skip filler words
            if token.text.lower() in self.FILLER_WORDS:
                continue
            
            # Extract tokens with numbers (prices, times, dates)
            if token.like_num or token.pos_ == 'NUM':
                # Get the full numeric phrase (e.g., "10k", "10:30am")
                phrase = self._get_numeric_phrase(token, doc)
                important.append(WeightageWord(
                    text=phrase,
                    weightage=0.0,
                    word_type='numeric_value',
                    specificity=0.0,
                    constraint_power=0.0,
                    replaceability=0.0,
                    extraction_method='pos_tag'
                ))
        
        return important
    
    def _get_numeric_phrase(self, token, doc) -> str:
        """
        Extract complete numeric phrase (e.g., "10k", "10:30am", "15th Jan")
        """
        # Get surrounding tokens to form complete phrase
        start = token.i
        end = token.i + 1
        
        # Expand right to capture units, am/pm, etc.
        while end < len(doc) and (
            doc[end].text.lower() in ['k', 'am', 'pm', 'rs', 'inr', 'rupees'] or
            doc[end].pos_ in ['NOUN', 'PROPN']
        ):
            end += 1
        
        # Expand left to capture modifiers
        while start > 0 and doc[start - 1].pos_ in ['ADJ', 'DET']:
            start -= 1
        
        phrase = doc[start:end].text
        return phrase
    
    def _calculate_scores(self, candidates: List[WeightageWord]) -> List[WeightageWord]:
        """
        Calculate specificity, constraint_power, and replaceability scores
        Then compute final weightage
        """
        for word in candidates:
            word.specificity = self._calculate_specificity(word)
            word.constraint_power = self._calculate_constraint_power(word)
            word.replaceability = self._calculate_replaceability(word)
            
            # Final weightage formula
            word.weightage = (
                0.4 * word.specificity +
                0.4 * word.constraint_power +
                0.2 * (1 - word.replaceability)
            )
        
        return candidates
    
    def _calculate_specificity(self, word: WeightageWord) -> float:
        """
        Calculate specificity based on word type and extraction method
        
        Logic:
        - Named entities (cities, dates, amounts) = Very specific (0.90-1.0)
        - Numeric values = Specific (0.85)
        - Constraints = Moderately specific (0.70-0.80)
        - Vague qualifiers = Low specificity (0.30)
        """
        text_lower = word.text.lower()
        
        # Named entities are highly specific
        if word.extraction_method == 'spacy_ner':
            entity_specificity = {
                'location': 0.95,      # Cities, countries
                'date': 1.00,          # Specific dates
                'time': 1.00,          # Specific times
                'amount': 0.95,        # Money amounts
                'number': 0.90,        # Numbers
                'person': 0.95,        # Person names
                'organization': 0.90,  # Org names
                'product': 0.85        # Products
            }
            return entity_specificity.get(word.word_type, 0.80)
        
        # Constraints have moderate specificity
        if word.word_type in ['hard_constraint', 'soft_constraint']:
            # Check if constraint contains specific values
            if re.search(r'\d+', word.text):
                return 0.80  # "not more than 10k" is specific
            return 0.70  # "preferably morning" is less specific
        
        # Numeric values are specific
        if word.word_type == 'numeric_value':
            return 0.85
        
        # Check if it contains vague terms
        if any(vague in text_lower for vague in self.VAGUE_QUALIFIERS):
            return 0.30
        
        # Default
        return 0.50
    
    def _calculate_constraint_power(self, word: WeightageWord) -> float:
        """
        Calculate how much the word constrains the solution space
        
        Logic:
        - Named entities = High constraint (you must use this specific thing)
        - Hard constraints = Maximum constraint
        - Soft constraints = Moderate constraint
        - Vague terms = Low constraint
        """
        text_lower = word.text.lower()
        
        # Hard constraints have maximum power
        if word.word_type == 'hard_constraint':
            return 1.0
        
        # Soft constraints have moderate power
        if word.word_type == 'soft_constraint':
            return 0.5
        
        # Named entities constrain strongly
        if word.extraction_method == 'spacy_ner':
            entity_power = {
                'location': 0.90,      # Must be this city
                'date': 0.95,          # Must be this date
                'time': 0.95,          # Must be this time
                'amount': 0.85,        # Must be this price
                'number': 0.80,        # Must be this quantity
                'person': 0.85,        # Must be this person
            }
            return entity_power.get(word.word_type, 0.70)
        
        # Numeric values constrain
        if word.word_type == 'numeric_value':
            return 0.80
        
        # Vague terms don't constrain much
        if any(vague in text_lower for vague in self.VAGUE_QUALIFIERS):
            return 0.20
        
        # Default
        return 0.50
    
    def _calculate_replaceability(self, word: WeightageWord) -> float:
        """
        Calculate if word can be removed without breaking the task
        
        Logic (NO WORD LISTS NEEDED):
        - Task-critical entities (from NER) = Irreplaceable (0.1)
        - Hard constraints = Very important (0.2)
        - Soft constraints = Moderately important (0.6)
        - Vague qualifiers = Replaceable (0.7)
        - Filler words = Highly replaceable (0.9)
        """
        text_lower = word.text.lower()
        
        # Rule 1: Named entities are task-critical (can't remove cities, dates)
        if word.extraction_method == 'spacy_ner':
            critical_entities = ['location', 'date', 'time', 'amount', 'number']
            if word.word_type in critical_entities:
                return 0.1  # Very low replaceability = very important
            return 0.3  # Other entities moderately important
        
        # Rule 2: Hard constraints are very important
        if word.word_type == 'hard_constraint':
            return 0.2
        
        # Rule 3: Soft constraints are moderately important
        if word.word_type == 'soft_constraint':
            return 0.6
        
        # Rule 4: Numeric values are important
        if word.word_type == 'numeric_value':
            return 0.3
        
        # Rule 5: Vague qualifiers are somewhat replaceable
        if any(vague in text_lower for vague in self.VAGUE_QUALIFIERS):
            return 0.7
        
        # Rule 6: Filler words are highly replaceable
        if any(filler in text_lower for filler in self.FILLER_WORDS):
            return 0.95
        
        # Default: moderate replaceability
        return 0.5
    
    def _deduplicate(self, words: List[WeightageWord]) -> List[WeightageWord]:
        """
        Remove duplicate/overlapping words
        Keep the one with higher weightage
        """
        seen = {}
        unique = []
        
        for word in words:
            # Normalize for comparison
            key = word.text.lower().strip()
            
            # Skip very short words (likely fragments)
            if len(key) <= 2:
                continue
            
            # If we've seen this before, keep the higher weightage version
            if key in seen:
                if word.weightage > seen[key].weightage:
                    # Replace with higher weightage version
                    unique = [w for w in unique if w.text.lower().strip() != key]
                    unique.append(word)
                    seen[key] = word
            else:
                unique.append(word)
                seen[key] = word
        
        return unique
    
    def get_statistics(self) -> Dict:
        """
        Return statistics about word lists used
        """
        return {
            'hard_constraints': len(self.HARD_CONSTRAINTS),
            'soft_constraints': len(self.SOFT_CONSTRAINTS),
            'vague_qualifiers': len(self.VAGUE_QUALIFIERS),
            'filler_words': len(self.FILLER_WORDS),
            'total_words_in_lists': (
                len(self.HARD_CONSTRAINTS) +
                len(self.SOFT_CONSTRAINTS) +
                len(self.VAGUE_QUALIFIERS) +
                len(self.FILLER_WORDS)
            ),
            'uses_spacy_ner': True,
            'scalable_to_new_domains': True
        }
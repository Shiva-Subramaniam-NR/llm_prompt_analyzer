"""
Vagueness Calculator v2.0

Calculates how vague/ambiguous a prompt is based on:
1. Missing mandatory parameters (with exponential penalty)
2. Ambiguous/vague terms used
3. Critical parameter penalties

Key Improvements:
- Exponential penalty for missing parameters (67% missing = 8.3, not 6.7)
- Validation to avoid false positives (reject "need to" as location)
- Critical parameter bonuses (missing origin+destination = extra penalty)
- Stricter interpretation thresholds
"""

import re
from typing import List, Tuple, Dict
from dataclasses import dataclass


@dataclass
class VaguenessAnalysis:
    """Complete vagueness analysis results"""
    vagueness_score: float
    interpretation: str
    missing_params: List[str]
    ambiguous_terms: List[str]
    missing_params_score: float
    ambiguity_score: float
    breakdown: Dict[str, str]
    suggested_followups: List[str]


class VaguenessCalculator:
    """Calculate vagueness score for prompts"""
    
    # Common verbs that are NOT locations
    COMMON_VERBS = [
        'need', 'want', 'travel', 'book', 'fly', 'go', 'come', 
        'like', 'wish', 'hope', 'plan', 'looking', 'trying'
    ]
    
    def __init__(self, domain_config):
        """
        Initialize calculator with domain configuration
        
        Args:
            domain_config: Domain-specific configuration object
        """
        self.domain = domain_config
    
    def calculate(self, prompt: str, high_weightage_words: List) -> VaguenessAnalysis:
        """
        Calculate complete vagueness analysis
        
        Args:
            prompt: Input prompt text
            high_weightage_words: List of WeightageWord objects
            
        Returns:
            VaguenessAnalysis object with scores and details
        """
        # Component 1: Missing parameters (with exponential penalty)
        missing_params, breakdown = self._check_missing_params(prompt)
        missing_params_score = self._calculate_missing_params_score(
            len(missing_params), 
            self.domain.get_param_count()
        )
        
        # Component 2: Ambiguity in terms
        ambiguous_terms = self._identify_ambiguous_terms(prompt, high_weightage_words)
        ambiguity_score = self._calculate_ambiguity_score(ambiguous_terms, high_weightage_words)
        
        # Base vagueness score (weighted combination)
        vagueness_score = 0.6 * missing_params_score + 0.4 * ambiguity_score
        
        # Apply critical parameter penalty
        vagueness_score = self._apply_critical_param_penalty(missing_params, vagueness_score)
        
        # Generate interpretation
        interpretation = self._interpret_vagueness(vagueness_score)
        
        # Generate follow-up questions
        followups = self._generate_followups(missing_params, ambiguous_terms, breakdown)
        
        return VaguenessAnalysis(
            vagueness_score=round(vagueness_score, 1),
            interpretation=interpretation,
            missing_params=missing_params,
            ambiguous_terms=ambiguous_terms,
            missing_params_score=round(missing_params_score, 1),
            ambiguity_score=round(ambiguity_score, 1),
            breakdown=breakdown,
            suggested_followups=followups
        )
    
    def _calculate_missing_params_score(self, missing_count: int, total_count: int) -> float:
        """
        Calculate missing parameters score with EXPONENTIAL penalty
        
        Linear scaling is too forgiving. Missing 67% should be catastrophic.
        
        Formula: 10 × (missing_ratio)^0.7
        
        Results:
        - Missing 0/6 (0%)   → 0.0
        - Missing 1/6 (17%)  → 2.9
        - Missing 2/6 (33%)  → 5.1
        - Missing 3/6 (50%)  → 6.9
        - Missing 4/6 (67%)  → 8.3  ← Much better than old 6.7!
        - Missing 5/6 (83%)  → 9.4
        - Missing 6/6 (100%) → 10.0
        
        Args:
            missing_count: Number of missing parameters
            total_count: Total number of mandatory parameters
            
        Returns:
            Score from 0-10
        """
        if missing_count == 0:
            return 0.0
        
        missing_ratio = missing_count / total_count
        
        # Exponential penalty - gets steeper as more params are missing
        score = 10 * (missing_ratio ** 0.7)
        
        return min(score, 10.0)
    
    def _check_missing_params(self, prompt: str) -> Tuple[List[str], Dict[str, str]]:
        """
        Check which mandatory parameters are missing or vague
        WITH VALIDATION to avoid false positives
        
        Returns:
            Tuple of (missing_params_list, parameter_breakdown_dict)
        """
        missing = []
        breakdown = {}
        
        for param_name, param_config in self.domain.MANDATORY_PARAMS.items():
            found = False
            status = "missing"
            
            # Check all patterns for this parameter
            for pattern in param_config['patterns']:
                if found:
                    break  # Already found a valid match

                # Use finditer to check ALL matches of this pattern (not just first)
                # This handles cases like "to fly from" appearing before "to Hyderabad"
                matches = re.finditer(pattern, prompt, re.IGNORECASE)

                for match in matches:
                    # Extract the captured value
                    extracted = match.group(1) if match.groups() else match.group(0)
                    extracted = extracted.strip()

                    # VALIDATION: Check if this is actually valid
                    if param_name in ['origin', 'destination']:
                        if not self._is_valid_location(extracted, prompt):
                            continue  # Skip false positives, try next match

                    found = True
                    match_text = match.group(0).lower()

                    # Check if the match is vague
                    is_vague = any(
                        vague_term in match_text
                        for terms in self.domain.VAGUE_TERMS.values()
                        for vague_term in terms
                    )

                    if is_vague:
                        status = f"present but vague ({extracted})"
                    else:
                        status = f"present ({extracted})"
                    break  # Found valid match, stop checking this pattern
            
            breakdown[param_name] = status
            
            if not found:
                missing.append(param_name)
        
        return missing, breakdown
    
    # Common non-location words that might be falsely captured
    FALSE_POSITIVE_WORDS = [
        'need', 'want', 'travel', 'book', 'fly', 'go', 'come',
        'like', 'wish', 'hope', 'plan', 'looking', 'trying',
        'please', 'something', 'somewhere', 'anything', 'nothing',
        'soon', 'later', 'today', 'tomorrow', 'comfortable', 'comfort',
        'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
        'morning', 'afternoon', 'evening', 'night', 'early', 'late',
        'economy', 'business', 'first', 'class', 'ticket', 'tickets',
        'budget', 'cost', 'price', 'rupees', 'inr'
    ]

    def _is_valid_location(self, text: str, original_prompt: str) -> bool:
        """
        Validate if extracted text is actually a location

        Rejects:
        - Common verbs and non-location words
        - Non-capitalized words in original prompt
        - Empty/whitespace
        - Words that appear lowercase in the original prompt

        Args:
            text: Extracted text to validate
            original_prompt: The original prompt to check capitalization

        Returns:
            True if valid location, False otherwise
        """
        if not text:
            return False

        text_clean = text.strip()
        text_lower = text_clean.lower()

        # Reject common non-location words
        if text_lower in self.COMMON_VERBS:
            return False

        if text_lower in self.FALSE_POSITIVE_WORDS:
            return False

        # Reject very short words (likely fragments)
        if len(text_clean) <= 2:
            return False

        # CRITICAL: Check if the word appears CAPITALIZED in the original prompt
        # This catches cases where regex with IGNORECASE matches lowercase words
        # Look for the word with proper capitalization (first letter uppercase)
        capitalized_form = text_clean[0].upper() + text_clean[1:].lower()

        # Check if the capitalized form exists in original prompt
        # OR if the extracted text itself is capitalized and exists
        if capitalized_form not in original_prompt and not text_clean[0].isupper():
            return False

        # Additional check: the word should appear with capital letter in prompt
        # Find the actual occurrence in original prompt
        word_pattern = r'\b' + re.escape(text_lower) + r'\b'
        matches = list(re.finditer(word_pattern, original_prompt, re.IGNORECASE))

        if not matches:
            return False

        # Check if at least one occurrence is capitalized
        is_capitalized = False
        for m in matches:
            actual_text = original_prompt[m.start():m.end()]
            if actual_text[0].isupper():
                is_capitalized = True
                break

        if not is_capitalized:
            return False

        return True
    
    def _apply_critical_param_penalty(self, missing_params: List[str], 
                                      base_score: float) -> float:
        """
        Add extra penalty if CRITICAL parameters are missing
        
        Logic:
        - Origin + Destination both missing: +2.0 (can't book flight without knowing route)
        - Either origin OR destination missing: +1.0 (serious issue)
        - Date missing: +0.5 (important but not as critical as route)
        
        Args:
            missing_params: List of missing parameter names
            base_score: Base vagueness score before penalty
            
        Returns:
            Adjusted score (capped at 10.0)
        """
        penalty = 0.0
        
        # Missing both origin AND destination = catastrophic
        if 'origin' in missing_params and 'destination' in missing_params:
            penalty += 2.0  # Massive penalty - can't execute task
        
        # Missing either origin OR destination = serious
        elif 'origin' in missing_params or 'destination' in missing_params:
            penalty += 1.0  # Serious penalty - task incomplete
        
        # Missing date = important
        if 'date' in missing_params:
            penalty += 0.5  # Moderate penalty
        
        # Cap at maximum 10.0
        return min(base_score + penalty, 10.0)
    
    def _identify_ambiguous_terms(self, prompt: str, high_weightage_words: List) -> List[str]:
        """Identify vague/ambiguous terms in the prompt"""
        ambiguous = []
        prompt_lower = prompt.lower()
        
        # Check all vague term categories from domain config
        for category, terms in self.domain.VAGUE_TERMS.items():
            for term in terms:
                if term in prompt_lower and term not in ambiguous:
                    ambiguous.append(term)
        
        # Also check high-weightage words for low specificity
        for word in high_weightage_words:
            if word.specificity < 0.5:
                if word.text.lower() not in ambiguous:
                    ambiguous.append(word.text)
        
        return ambiguous
    
    def _calculate_ambiguity_score(self, ambiguous_terms: List[str], 
                                   high_weightage_words: List) -> float:
        """
        Calculate ambiguity contribution to vagueness
        
        Returns score from 0-10 based on ratio of ambiguous terms
        """
        if not high_weightage_words:
            return 5.0  # No weightage words = moderately ambiguous
        
        # Count ambiguous terms
        ambiguity_count = len(ambiguous_terms)
        
        # Normalize by total high-weightage words
        ambiguity_ratio = ambiguity_count / max(len(high_weightage_words), 1)
        
        # Scale to 0-10
        return min(ambiguity_ratio * 10, 10)
    
    def _interpret_vagueness(self, score: float) -> str:
        """
        Provide human-readable interpretation of vagueness score
        
        STRICTER thresholds than v1:
        - Moved thresholds down to be more aggressive
        - 7.5+ is now "Extremely Vague" (was 8.0+)
        """
        if score <= 1.5:
            return "Very Specific - Ready for strict execution"
        elif score <= 3.5:
            return "Mostly Specific - Minor clarifications may help"
        elif score <= 5.5:
            return "Moderate Vagueness - Follow-ups recommended"
        elif score <= 7.5:
            return "High Vagueness - Significant clarification needed"
        else:  # > 7.5
            return "Extremely Vague - Cannot execute without clarification"
    
    def _generate_followups(self, missing_params: List[str], 
                           ambiguous_terms: List[str],
                           breakdown: Dict[str, str]) -> List[str]:
        """Generate suggested follow-up questions"""
        followups = []
        
        # Questions for completely missing parameters
        param_questions = {
            'origin': "Where are you departing from?",
            'destination': "Where do you want to go?",
            'date': "What date would you like to travel?",
            'time_preference': "What time of day do you prefer?",
            'class': "Which class would you prefer? (Economy/Business/First)",
            'budget': "What is your maximum budget?"
        }
        
        for param in missing_params:
            if param in param_questions:
                followups.append(param_questions[param])
        
        # Questions for vague parameters
        for param, status in breakdown.items():
            if "vague" in status.lower():
                if param == 'time_preference':
                    followups.append("Can you specify an exact time or time range? (e.g., 8am-10am)")
                elif param == 'budget':
                    followups.append("Can you specify a maximum amount in rupees?")
                elif param == 'class':
                    followups.append("Which specific class? (Economy/Business/First)")
                elif param == 'date':
                    followups.append("Can you provide a specific date?")
                elif param in ['origin', 'destination']:
                    followups.append(f"Can you specify the exact {param}?")
        
        return followups
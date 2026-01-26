"""
Complete Prompt Analyzer

Combines weightage extraction and vagueness calculation
to provide comprehensive prompt analysis.
"""

from typing import Dict
from config.domain_config import FlightBookingDomain
from weightage import WeightageExtractorV2 as WeightageExtractor
from vagueness import VaguenessCalculator


class PromptAnalyzer:
    """Main analyzer combining all components"""
    
    def __init__(self, domain_name: str = "flight_booking"):
        """
        Initialize analyzer with specified domain
        
        Args:
            domain_name: Name of domain to analyze (currently only 'flight_booking')
        """
        if domain_name == "flight_booking":
            self.domain = FlightBookingDomain()
        else:
            raise ValueError(f"Domain '{domain_name}' not supported yet. Available: 'flight_booking'")
        
        self.weightage_extractor = WeightageExtractor(self.domain)
        self.vagueness_calculator = VaguenessCalculator(self.domain)
    
    def analyze(self, prompt: str) -> Dict:
        """
        Perform complete prompt analysis
        
        Args:
            prompt: Input prompt text
            
        Returns:
            Dictionary containing analysis results:
            - high_weightage_words: List of important words with scores
            - vagueness_analysis: Complete vagueness breakdown
        """
        # Extract high-weightage words
        high_weightage_words = self.weightage_extractor.extract(prompt)
        
        # Calculate vagueness
        vagueness_analysis = self.vagueness_calculator.calculate(prompt, high_weightage_words)
        
        # Compile results
        result = {
            "prompt": prompt,
            "high_weightage_words": [
                {
                    "text": w.text,
                    "weightage": round(w.weightage, 2),
                    "type": w.word_type,
                    "specificity": round(w.specificity, 2),
                    "constraint_power": round(w.constraint_power, 2)
                }
                for w in high_weightage_words
            ],
            "vagueness_analysis": {
                "vagueness_score": vagueness_analysis.vagueness_score,
                "interpretation": vagueness_analysis.interpretation,
                "missing_params": vagueness_analysis.missing_params,
                "ambiguous_terms": vagueness_analysis.ambiguous_terms,
                "missing_params_score": vagueness_analysis.missing_params_score,
                "ambiguity_score": vagueness_analysis.ambiguity_score,
                "parameter_breakdown": vagueness_analysis.breakdown,
                "suggested_followups": vagueness_analysis.suggested_followups
            }
        }
        
        return result
    
    def analyze_and_print(self, prompt: str) -> Dict:
        """
        Analyze and print results in readable format
        
        Args:
            prompt: Input prompt text
            
        Returns:
            Analysis results dictionary
        """
        result = self.analyze(prompt)
        
        print("="*80)
        print("PROMPT ANALYSIS RESULTS")
        print("="*80)
        print(f"\nPrompt: {prompt}\n")
        
        print("-" * 80)
        print("HIGH WEIGHTAGE WORDS:")
        print("-" * 80)
        if result['high_weightage_words']:
            for word in result['high_weightage_words']:
                print(f"  * {word['text']:30} | Weightage: {word['weightage']:.2f} | Type: {word['type']}")
                print(f"    -> Specificity: {word['specificity']:.2f}, Constraint Power: {word['constraint_power']:.2f}")
        else:
            print("  (No high-weightage words detected)")
        
        print("\n" + "-" * 80)
        print("VAGUENESS ANALYSIS:")
        print("-" * 80)
        va = result['vagueness_analysis']
        print(f"  Overall Vagueness Score: {va['vagueness_score']}/10")
        print(f"  Interpretation: {va['interpretation']}")
        print(f"\n  Components:")
        print(f"    - Missing Parameters Score: {va['missing_params_score']}/10")
        print(f"    - Ambiguity Score: {va['ambiguity_score']}/10")
        
        print(f"\n  Parameter Breakdown:")
        for param, status in va['parameter_breakdown'].items():
            print(f"    * {param:20} -> {status}")
        
        if va['ambiguous_terms']:
            print(f"\n  Ambiguous Terms Found: {', '.join(va['ambiguous_terms'])}")
        
        if va['suggested_followups']:
            print(f"\n  Suggested Follow-up Questions:")
            for i, q in enumerate(va['suggested_followups'], 1):
                print(f"    {i}. {q}")
        
        print("="*80)
        
        return result
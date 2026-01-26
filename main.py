"""
Prompt Analysis Framework v1.0
Main Entry Point

Domain: Flight Booking
Author: Shiva & Claude Research Partnership

This framework analyzes prompts to extract:
1. High Weightage Words - Terms that influence LLM behavior
2. Vagueness Score - Measures completeness and specificity
"""

import json
import os
from dataclasses import dataclass
from typing import Dict, List

# Import our modules
from config.domain_config import FlightBookingDomain
from weightage import WeightageExtractorV2 as WeightageExtractor, WeightageWord
from vagueness import VaguenessCalculator, VaguenessAnalysis
from prompt_analyzer import PromptAnalyzer
from unit_tests import run_all_tests


def print_banner():
    """Print welcome banner"""
    print("""
    +============================================================================+
    |                    PROMPT ANALYSIS FRAMEWORK v1.0                          |
    |                  Flight Booking Domain Analyzer                            |
    |                                                                            |
    |                  Research Partnership: Shiva & Claude                      |
    +============================================================================+
    """)


def ensure_output_directory():
    """Create output directory if it doesn't exist"""
    os.makedirs('outputs', exist_ok=True)


def save_results(results: List[Dict], filename: str = 'prompt_analysis_results.json'):
    """Save analysis results to JSON file"""
    output_path = os.path.join('outputs', filename)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n[OK] Results exported to '{output_path}'")


def analyze_custom_prompt():
    """Interactive mode for analyzing custom prompts"""
    analyzer = PromptAnalyzer("flight_booking")
    
    print("\n" + "="*80)
    print("CUSTOM PROMPT ANALYSIS MODE")
    print("="*80)
    print("Enter your prompt (or 'quit' to exit):\n")
    
    while True:
        prompt = input("Prompt: ").strip()
        
        if prompt.lower() in ['quit', 'exit', 'q']:
            break
        
        if not prompt:
            print("Please enter a valid prompt.\n")
            continue
        
        print()
        result = analyzer.analyze_and_print(prompt)
        print("\n" + "="*80 + "\n")


def main():
    """Main execution function"""
    print_banner()
    ensure_output_directory()
    
    print("\nChoose an option:")
    print("1. Run test suite (recommended for first run)")
    print("2. Analyze custom prompt")
    print("3. Run both")
    
    choice = input("\nYour choice (1/2/3): ").strip()
    
    if choice in ['1', '3']:
        print("\n" + " RUNNING TEST SUITE ".center(80, "="))
        results = run_all_tests()
        save_results(results)
    
    if choice in ['2', '3']:
        analyze_custom_prompt()
    
    print("\n[DONE] Analysis complete! Thank you for using the framework.\n")


if __name__ == "__main__":
    main()
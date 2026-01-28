"""
Interactive Prompt Quality Analyzer - CLI Application

Allows users to input their own prompts and choose which analyses to run.
"""

import sys
from v2.prompt_quality_analyzer import PromptQualityAnalyzer, print_quality_report
from v2.system_prompt_parser import SystemPromptParser, print_system_prompt_analysis
from v2.alignment_checker import AlignmentChecker, print_alignment_analysis
from v2.contradiction_detector import ContradictionDetector, print_contradiction_analysis
from v2.verbosity_analyzer import VerbosityAnalyzer
from v2.embedding_manager import EmbeddingManager, EmbeddingConfig


def print_header():
    """Print application header"""
    print("\n" + "="*70)
    print("   PROMPT QUALITY ANALYZER - Interactive Mode")
    print("="*70)
    print("Analyze your LLM prompts for quality, alignment, and consistency")
    print("="*70 + "\n")


def get_multiline_input(prompt_text):
    """Get multiline input from user"""
    print(prompt_text)
    print("(Type your prompt below. Press Ctrl+Z then Enter on Windows, or Ctrl+D on Mac/Linux when done)")
    print("-" * 70)

    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass

    return "\n".join(lines).strip()


def get_system_prompt():
    """Get system prompt from user (mandatory)"""
    while True:
        print("\n[STEP 1] SYSTEM PROMPT (Mandatory)")
        system_prompt = get_multiline_input("Enter your system prompt:")

        if not system_prompt or len(system_prompt) < 10:
            print("\n[ERROR] System prompt is too short or empty. Please try again.\n")
            retry = input("Try again? (y/n): ").lower()
            if retry != 'y':
                return None
            continue

        print(f"\n[OK] System prompt received ({len(system_prompt)} characters, {len(system_prompt.split())} words)")
        return system_prompt


def get_user_prompt():
    """Get user prompt from user (optional)"""
    print("\n[STEP 2] USER PROMPT (Optional)")
    print("Do you want to provide a user prompt for alignment checking?")
    choice = input("Enter user prompt? (y/n): ").lower()

    if choice != 'y':
        print("[INFO] Skipping user prompt. Only system prompt will be analyzed.")
        return None

    user_prompt = get_multiline_input("\nEnter your user prompt:")

    if not user_prompt or len(user_prompt) < 3:
        print("[INFO] User prompt is empty. Only system prompt will be analyzed.")
        return None

    print(f"\n[OK] User prompt received ({len(user_prompt)} characters, {len(user_prompt.split())} words)")
    return user_prompt


def get_artifacts():
    """Get artifact file paths from user (optional)"""
    print("\n[STEP 2.5] ARTIFACTS (Optional)")
    print("Do you want to provide artifact files (PDFs, images, documents)?")
    print("This is useful when your prompts reference external documents or images.")
    choice = input("Provide artifacts? (y/n): ").lower()

    if choice != 'y':
        print("[INFO] Skipping artifacts.")
        return None

    artifacts = {}
    print("\nEnter artifact file paths (press Enter with empty name to finish):")
    print("Example:")
    print("  Name: research_document")
    print("  Path: C:\\path\\to\\document.pdf")
    print()

    while True:
        name = input("Artifact name (or press Enter to finish): ").strip()
        if not name:
            break

        path = input(f"File path for '{name}': ").strip()
        if not path:
            print("[WARNING] Empty path, skipping this artifact.")
            continue

        artifacts[name] = path
        print(f"[OK] Added artifact: {name} -> {path}")

    if artifacts:
        print(f"\n[OK] {len(artifacts)} artifact(s) added")
        return artifacts
    else:
        print("[INFO] No artifacts provided.")
        return None


def select_analyses():
    """Let user choose which analyses to run"""
    print("\n[STEP 3] SELECT ANALYSES TO RUN")
    print("=" * 70)
    print("\nAvailable Analyses:")
    print("  1. [Comprehensive] Run ALL analyses (recommended)")
    print("  2. [System Parser] Extract requirements from system prompt")
    print("  3. [Contradiction] Detect internal conflicts in system prompt")
    print("  4. [Verbosity] Analyze prompt length and structure")
    print("  5. [Alignment] Check system-user prompt compatibility (requires user prompt)")
    print("  6. [Custom] Select specific analyses")
    print("=" * 70)

    while True:
        choice = input("\nEnter your choice (1-6): ").strip()

        if choice == '1':
            return {
                'all': True,
                'parser': True,
                'contradiction': True,
                'verbosity': True,
                'alignment': True
            }
        elif choice == '2':
            return {'all': False, 'parser': True, 'contradiction': False, 'verbosity': False, 'alignment': False}
        elif choice == '3':
            return {'all': False, 'parser': False, 'contradiction': True, 'verbosity': False, 'alignment': False}
        elif choice == '4':
            return {'all': False, 'parser': False, 'contradiction': False, 'verbosity': True, 'alignment': False}
        elif choice == '5':
            return {'all': False, 'parser': False, 'contradiction': False, 'verbosity': False, 'alignment': True}
        elif choice == '6':
            return select_custom_analyses()
        else:
            print("[ERROR] Invalid choice. Please enter 1-6.")


def select_custom_analyses():
    """Let user select multiple specific analyses"""
    print("\n[CUSTOM SELECTION]")
    print("Select which analyses to run (y/n for each):\n")

    selections = {}

    selections['parser'] = input("  System Parser (extract requirements)? (y/n): ").lower() == 'y'
    selections['contradiction'] = input("  Contradiction Detector? (y/n): ").lower() == 'y'
    selections['verbosity'] = input("  Verbosity Analyzer? (y/n): ").lower() == 'y'
    selections['alignment'] = input("  Alignment Checker (requires user prompt)? (y/n): ").lower() == 'y'

    selections['all'] = False

    if not any(selections.values()):
        print("\n[WARNING] No analyses selected. Defaulting to comprehensive analysis.")
        return {
            'all': True,
            'parser': True,
            'contradiction': True,
            'verbosity': True,
            'alignment': True
        }

    return selections


def run_comprehensive_analysis(system_prompt, user_prompt, artifacts=None):
    """Run complete analysis using PromptQualityAnalyzer"""
    print("\n" + "="*70)
    print("RUNNING COMPREHENSIVE ANALYSIS")
    print("="*70)

    analyzer = PromptQualityAnalyzer(verbose=True)
    report = analyzer.analyze(system_prompt, user_prompt, artifacts=artifacts)

    print_quality_report(report)

    # Offer to save
    save = input("\nSave report to JSON? (y/n): ").lower()
    if save == 'y':
        filename = input("Enter filename (default: quality_report.json): ").strip()
        if not filename:
            filename = "quality_report.json"
        if not filename.endswith('.json'):
            filename += '.json'

        filepath = f"outputs/{filename}"
        report.save_to_file(filepath)
        print(f"\n[SAVED] Report saved to {filepath}")


def run_selected_analyses(system_prompt, user_prompt, selections):
    """Run only selected analyses"""
    print("\n" + "="*70)
    print("RUNNING SELECTED ANALYSES")
    print("="*70)

    # Initialize components
    print("\n[INFO] Initializing components...")
    config = EmbeddingConfig(model_name="all-MiniLM-L6-v2")
    embedding_manager = EmbeddingManager(config)

    # Run System Parser
    if selections['parser']:
        print("\n\n" + "="*70)
        print("[1/4] SYSTEM PROMPT PARSER")
        print("="*70)
        parser = SystemPromptParser(embedding_manager)
        system_analysis = parser.parse(system_prompt)
        print_system_prompt_analysis(system_analysis)

    # Run Contradiction Detector
    if selections['contradiction']:
        print("\n\n" + "="*70)
        print("[2/4] CONTRADICTION DETECTOR")
        print("="*70)
        detector = ContradictionDetector(embedding_manager)
        contradiction_analysis = detector.detect(system_prompt)
        print_contradiction_analysis(contradiction_analysis)

    # Run Verbosity Analyzer
    if selections['verbosity']:
        print("\n\n" + "="*70)
        print("[3/4] VERBOSITY ANALYZER")
        print("="*70)
        verbosity_analyzer = VerbosityAnalyzer(embedding_manager)
        verbosity_metrics = verbosity_analyzer.analyze(system_prompt)

        print(f"\nTotal Words: {verbosity_metrics.total_words}")
        print(f"Total Sentences: {verbosity_metrics.total_sentences}")
        print(f"Verbosity Score: {verbosity_metrics.verbosity_score:.1f}/10")
        print(f"Redundancy Score: {verbosity_metrics.redundancy_score:.1f}/10")
        print(f"Information Density: {verbosity_metrics.information_density:.2%}")

        if verbosity_metrics.buried_directives:
            print(f"\n[WARNING] Found {len(verbosity_metrics.buried_directives)} buried directives:")
            for directive in verbosity_metrics.buried_directives[:3]:
                print(f"  - Position {directive['position']}: \"{directive['directive'][:60]}...\"")

        if verbosity_metrics.recommendations:
            print("\nRecommendations:")
            for rec in verbosity_metrics.recommendations[:3]:
                print(f"  - {rec}")

    # Run Alignment Checker
    if selections['alignment']:
        print("\n\n" + "="*70)
        print("[4/4] ALIGNMENT CHECKER")
        print("="*70)

        if not user_prompt:
            print("\n[ERROR] Alignment checking requires a user prompt!")
            print("Skipping alignment analysis.")
        else:
            parser = SystemPromptParser(embedding_manager)
            checker = AlignmentChecker(embedding_manager, parser)
            alignment_analysis = checker.check_alignment(system_prompt, user_prompt)
            print_alignment_analysis(alignment_analysis)

    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)


def main():
    """Main application loop"""
    print_header()

    try:
        # Step 1: Get system prompt (mandatory)
        system_prompt = get_system_prompt()
        if not system_prompt:
            print("\n[EXIT] No system prompt provided. Exiting.")
            return

        # Step 2: Get user prompt (optional)
        user_prompt = get_user_prompt()

        # Step 3: Select analyses
        selections = select_analyses()

        # Step 4: Run analyses
        print("\n" + "="*70)
        print("STARTING ANALYSIS...")
        print("="*70)

        if selections['all']:
            run_comprehensive_analysis(system_prompt, user_prompt)
        else:
            run_selected_analyses(system_prompt, user_prompt, selections)

        # Ask if user wants to analyze another prompt
        print("\n" + "="*70)
        again = input("\nAnalyze another prompt? (y/n): ").lower()
        if again == 'y':
            main()  # Restart
        else:
            print("\n[EXIT] Thank you for using Prompt Quality Analyzer!")
            print("="*70 + "\n")

    except KeyboardInterrupt:
        print("\n\n[EXIT] Analysis interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

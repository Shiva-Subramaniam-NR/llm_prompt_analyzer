"""
Simple Interactive Prompt Analyzer
Easy-to-use CLI for analyzing prompts
"""

from interactive_analyzer import (
    print_header,
    get_system_prompt,
    get_user_prompt,
    get_artifacts,
    select_analyses,
    run_comprehensive_analysis,
    run_selected_analyses
)


def main():
    """Simple main entry point"""
    print_header()

    print("Welcome! This tool analyzes your LLM prompts for quality and issues.\n")
    print("You'll need to provide:")
    print("  1. System Prompt (MANDATORY) - The instructions for your AI")
    print("  2. User Prompt (OPTIONAL) - A sample user input to test against")
    print("  3. Artifacts (OPTIONAL) - Files referenced in prompts (PDFs, images)\n")

    input("Press Enter to continue...")

    # Get prompts
    system_prompt = get_system_prompt()
    if not system_prompt:
        print("\nExiting - no system prompt provided.")
        return

    user_prompt = get_user_prompt()
    artifacts = get_artifacts()

    # Select analyses
    selections = select_analyses()

    # Run
    print("\nStarting analysis...\n")

    if selections['all']:
        run_comprehensive_analysis(system_prompt, user_prompt, artifacts)
    else:
        run_selected_analyses(system_prompt, user_prompt, selections)

    print("\n✅ Analysis complete!")


if __name__ == "__main__":
    main()

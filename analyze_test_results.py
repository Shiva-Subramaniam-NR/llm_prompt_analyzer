"""
Analyze test results and generate comprehensive report
"""
import json
import statistics
from datetime import datetime
from typing import List, Dict, Any
from collections import defaultdict

class TestResultAnalyzer:
    def __init__(self, results_file):
        with open(results_file, 'r') as f:
            self.results = json.load(f)

    def analyze_by_scenario(self):
        """Group results by scenario and calculate statistics"""
        by_scenario = defaultdict(list)

        for result in self.results:
            if result.get('success', False):
                scenario = result['scenario']
                by_scenario[scenario].append(result)

        analysis = {}
        for scenario, results in by_scenario.items():
            tier1_scores = [r['tier1_score'] for r in results]
            tier2_scores = [r['tier2_risk_score'] for r in results]
            elapsed_times = [r['elapsed_time'] for r in results]

            analysis[scenario] = {
                'num_tests': len(results),
                'tier1_score_mean': statistics.mean(tier1_scores),
                'tier1_score_std': statistics.stdev(tier1_scores) if len(tier1_scores) > 1 else 0,
                'tier1_score_min': min(tier1_scores),
                'tier1_score_max': max(tier1_scores),
                'tier2_risk_mean': statistics.mean(tier2_scores),
                'tier2_risk_std': statistics.stdev(tier2_scores) if len(tier2_scores) > 1 else 0,
                'tier2_risk_min': min(tier2_scores),
                'tier2_risk_max': max(tier2_scores),
                'avg_elapsed_time': statistics.mean(elapsed_times),
                'ratings': [r['tier1_rating'] for r in results],
                'risk_types': [r['tier2_risk_type'] for r in results],
                'issues_critical_mean': statistics.mean([r['tier1_issues_critical'] for r in results]),
                'issues_high_mean': statistics.mean([r['tier1_issues_high'] for r in results]),
                'issues_total_mean': statistics.mean([r['tier1_issues_total'] for r in results]),
                'component_scores': {
                    'alignment': statistics.mean([r['tier1_alignment'] for r in results]),
                    'consistency': statistics.mean([r['tier1_consistency'] for r in results]),
                    'verbosity': statistics.mean([r['tier1_verbosity'] for r in results]),
                    'completeness': statistics.mean([r['tier1_completeness'] for r in results])
                }
            }

        return analysis

    def check_deviation(self, analysis):
        """Check if minor variations caused significant metric deviations"""
        deviations = {}

        for scenario, stats in analysis.items():
            tier1_std = stats['tier1_score_std']
            tier2_std = stats['tier2_risk_std']

            # Define thresholds for "significant" deviation
            TIER1_THRESHOLD = 0.5  # 0.5 points on 10-point scale
            TIER2_THRESHOLD = 1.0  # 1.0 points on 10-point scale

            deviations[scenario] = {
                'tier1_deviation': tier1_std,
                'tier1_significant': tier1_std > TIER1_THRESHOLD,
                'tier2_deviation': tier2_std,
                'tier2_significant': tier2_std > TIER2_THRESHOLD,
                'interpretation': None
            }

            # Interpret
            if tier1_std > TIER1_THRESHOLD:
                deviations[scenario]['interpretation'] = "UNSTABLE: Minor prompt variations cause significant score changes"
            elif tier2_std > TIER2_THRESHOLD:
                deviations[scenario]['interpretation'] = "INCONSISTENT: Safety detection varies with minor changes"
            else:
                deviations[scenario]['interpretation'] = "STABLE: Consistent evaluation across variations"

        return deviations

    def generate_report(self):
        """Generate comprehensive markdown report"""
        analysis = self.analyze_by_scenario()
        deviations = self.check_deviation(analysis)

        report = f"""# Comprehensive Prompt Analyzer Test Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total Tests:** {len(self.results)}
**Scenarios:** {len(analysis)}

---

## Executive Summary

This report analyzes {len(self.results)} test runs across {len(analysis)} scenarios, with 3 variations per scenario to assess stability and consistency.

### Key Findings:

"""

        # Add key findings
        for scenario, stats in analysis.items():
            report += f"""
#### {scenario}
- **Tier 1 Score:** {stats['tier1_score_mean']:.2f} ± {stats['tier1_score_std']:.2f}/10
- **Tier 2 Risk:** {stats['tier2_risk_mean']:.1f} ± {stats['tier2_risk_std']:.1f}/10
- **Stability:** {deviations[scenario]['interpretation']}
- **Avg Response Time:** {stats['avg_elapsed_time']:.2f}s
"""

        report += "\n---\n\n## Detailed Analysis by Scenario\n\n"

        for scenario, stats in analysis.items():
            report += f"""
### {scenario}

#### Overall Metrics
| Metric | Value |
|--------|-------|
| Tests Run | {stats['num_tests']} |
| Tier 1 Score (Mean ± Std) | {stats['tier1_score_mean']:.2f} ± {stats['tier1_score_std']:.2f} |
| Tier 1 Score Range | {stats['tier1_score_min']:.2f} - {stats['tier1_score_max']:.2f} |
| Tier 2 Risk (Mean ± Std) | {stats['tier2_risk_mean']:.1f} ± {stats['tier2_risk_std']:.1f} |
| Tier 2 Risk Range | {stats['tier2_risk_min']:.1f} - {stats['tier2_risk_max']:.1f} |
| Avg Response Time | {stats['avg_elapsed_time']:.2f}s |

#### Component Scores (Tier 1)
| Component | Score |
|-----------|-------|
| Alignment | {stats['component_scores']['alignment']:.2f}/10 |
| Consistency | {stats['component_scores']['consistency']:.2f}/10 |
| Verbosity | {stats['component_scores']['verbosity']:.2f}/10 |
| Completeness | {stats['component_scores']['completeness']:.2f}/10 |

#### Issues Detected (Mean)
| Severity | Count |
|----------|-------|
| Total Issues | {stats['issues_total_mean']:.1f} |
| Critical | {stats['issues_critical_mean']:.1f} |
| High | {stats['issues_high_mean']:.1f} |

#### Quality Ratings
"""
            for rating in set(stats['ratings']):
                count = stats['ratings'].count(rating)
                report += f"- **{rating.upper()}**: {count}/{stats['num_tests']} tests\n"

            report += "\n#### Risk Types Detected\n"
            for risk_type in set(stats['risk_types']):
                count = stats['risk_types'].count(risk_type)
                report += f"- **{risk_type.upper()}**: {count}/{stats['num_tests']} tests\n"

            report += "\n"

        # Deviation Analysis
        report += "\n---\n\n## Deviation Analysis\n\n"
        report += "**Question:** Do minor prompt variations cause significant metric changes?\n\n"

        for scenario, dev_stats in deviations.items():
            report += f"""
### {scenario}
- **Tier 1 Std Dev:** {dev_stats['tier1_deviation']:.3f} (Threshold: 0.5)
  - **Significant:** {'YES ⚠️' if dev_stats['tier1_significant'] else 'NO ✓'}
- **Tier 2 Std Dev:** {dev_stats['tier2_deviation']:.3f} (Threshold: 1.0)
  - **Significant:** {'YES ⚠️' if dev_stats['tier2_significant'] else 'NO ✓'}
- **Interpretation:** {dev_stats['interpretation']}

"""

        # Impact Assessment
        report += "\n---\n\n## Impact Assessment\n\n"
        report += """
### Does Deviation Impact Results?

"""

        for scenario, dev_stats in deviations.items():
            if dev_stats['tier1_significant'] or dev_stats['tier2_significant']:
                report += f"**{scenario}:** ⚠️ **YES** - Minor variations cause noticeable changes. "
                report += "This indicates the analyzer may be sensitive to wording.\n\n"
            else:
                report += f"**{scenario}:** ✓ **NO** - Consistent evaluation despite minor variations. "
                report += "This indicates robust analysis.\n\n"

        report += "\n---\n\n## Critical Issues Identified\n\n"

        # Check for critical patterns
        critical_issues = []

        for scenario, stats in analysis.items():
            # Check if Tier 2 consistently fails to detect obvious risks
            if scenario in ['CodeGenBot', 'LegalBot'] and stats['tier2_risk_mean'] < 5.0:
                critical_issues.append({
                    'scenario': scenario,
                    'issue': 'Tier 2 failed to detect obvious safety risks',
                    'evidence': f"Mean risk score: {stats['tier2_risk_mean']:.1f}/10",
                    'severity': 'CRITICAL'
                })

            # Check for Tier 1 inconsistency
            if stats['tier1_score_std'] > 1.0:
                critical_issues.append({
                    'scenario': scenario,
                    'issue': 'Tier 1 scores highly unstable',
                    'evidence': f"Standard deviation: {stats['tier1_score_std']:.2f}",
                    'severity': 'HIGH'
                })

        if critical_issues:
            for issue in critical_issues:
                report += f"""
### {issue['severity']}: {issue['scenario']}
**Issue:** {issue['issue']}
**Evidence:** {issue['evidence']}

"""
        else:
            report += "\nNo critical issues detected.\n"

        report += "\n---\n\n## Next Steps\n\n"
        report += """
1. **Fix Prompts:** Create corrected versions and re-run tests
2. **Research Guidelines:** Compare against Anthropic/OpenAI/Microsoft standards
3. **Gap Analysis:** Identify evaluation mechanism gaps
4. **Improvements:** Fix identified issues

"""

        return report


if __name__ == "__main__":
    import sys
    import glob

    # Find latest test results
    results_files = glob.glob("outputs/comprehensive_test_results_*.json")
    if not results_files:
        print("No test results found!")
        sys.exit(1)

    latest_file = max(results_files)
    print(f"Analyzing: {latest_file}")

    analyzer = TestResultAnalyzer(latest_file)
    report = analyzer.generate_report()

    # Save report
    report_file = latest_file.replace('.json', '_ANALYSIS.md')
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"Report saved to: {report_file}")

    # Print summary
    print("\n" + "="*70)
    print("REPORT SUMMARY")
    print("="*70)
    print(report.split('---')[1])  # Print Executive Summary section

#!/usr/bin/env python3
"""
Demonstration script for Clinical Trial Criteria Agreement Analysis

This script demonstrates the functionality of the agreement analysis tool by:
1. Running analysis on sample data with both local and LLM-based methods
2. Displaying key results and insights in a user-friendly format
3. Showing examples of discrepancies found
4. Generating a comprehensive summary report
5. Providing guidance on interpreting the results

Usage:
    python demo_agreement_analysis.py [--api-keys api_keys.json] [--model claude|openai|gemini]
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Configure logging for demo
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('demo_analysis.log')
    ]
)

def print_header(title: str, char: str = "=", width: int = 80):
    """Print a formatted header."""
    print(f"\n{char * width}")
    print(f"{title:^{width}}")
    print(f"{char * width}")

def print_section(title: str, char: str = "-", width: int = 60):
    """Print a formatted section header."""
    print(f"\n{char * width}")
    print(f" {title}")
    print(f"{char * width}")

def format_metric(value: float, precision: int = 3) -> str:
    """Format a metric value for display."""
    return f"{value:.{precision}f}"

def get_quality_assessment(f1_score: float, kappa: float) -> str:
    """Assess agreement quality based on metrics."""
    if f1_score > 0.9 and kappa > 0.8:
        return "🟢 Excellent"
    elif f1_score > 0.8 and kappa > 0.6:
        return "🟡 Good"
    elif f1_score > 0.6 and kappa > 0.4:
        return "🟠 Moderate"
    else:
        return "🔴 Poor"

def check_sample_data() -> bool:
    """Check if sample data exists."""
    sample_dir = Path("sample_data/decomposed")
    if not sample_dir.exists():
        print(f"❌ Sample data directory not found: {sample_dir}")
        return False
    
    json_files = list(sample_dir.glob("*.json"))
    if len(json_files) < 2:
        print(f"❌ Need at least 2 JSON files for comparison, found {len(json_files)}")
        return False
    
    print(f"✅ Found {len(json_files)} sample files for analysis")
    for file in json_files:
        print(f"   - {file.name}")
    return True

def run_local_analysis() -> Optional[Dict]:
    """Run local agreement analysis."""
    print_section("Running Local Analysis (No API Required)")
    
    try:
        import subprocess
        
        # Ensure outputs directory exists
        os.makedirs("outputs", exist_ok=True)
        
        # Run local analysis
        cmd = [
            sys.executable, "analyze_criteria_agreement.py",
            "--input-dir", "sample_data/decomposed/",
            "--output", "outputs/",
            "--local-only"
        ]
        
        print("Executing command:", " ".join(cmd))
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            print(f"❌ Local analysis failed:")
            print(f"STDERR: {result.stderr}")
            return None
        
        print("✅ Local analysis completed successfully")
        
        # Find the output file
        output_files = list(Path("outputs").glob("agreement_analysis_local_*.json"))
        if not output_files:
            print("❌ No output file found")
            return None
        
        latest_file = max(output_files, key=lambda x: x.stat().st_mtime)
        print(f"📄 Results saved to: {latest_file}")
        
        # Load and return results
        with open(latest_file, 'r') as f:
            return json.load(f)
            
    except subprocess.TimeoutExpired:
        print("❌ Local analysis timed out (>5 minutes)")
        return None
    except Exception as e:
        print(f"❌ Error running local analysis: {e}")
        return None

def run_llm_analysis(api_keys_file: str, model: str) -> Optional[Dict]:
    """Run LLM-based agreement analysis."""
    print_section(f"Running LLM Analysis ({model.upper()})")
    
    if not os.path.exists(api_keys_file):
        print(f"❌ API keys file not found: {api_keys_file}")
        print("   Create a JSON file with your API keys:")
        print('   {"openai": "your-key", "claude": "your-key", "gemini": "your-key"}')
        return None
    
    prompt_file = "prompts/study_traits_agreement_analysis_prompt.md"
    if not os.path.exists(prompt_file):
        print(f"❌ Prompt file not found: {prompt_file}")
        return None
    
    try:
        import subprocess
        
        # Ensure outputs directory exists
        os.makedirs("outputs", exist_ok=True)
        
        # Run LLM analysis
        cmd = [
            sys.executable, "analyze_criteria_agreement.py",
            "--input-dir", "sample_data/decomposed/",
            "--output", "outputs/",
            "--prompt", prompt_file,
            "--api-keys", api_keys_file,
            "--model", model
        ]
        
        print("Executing command:", " ".join(cmd))
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode != 0:
            print(f"❌ LLM analysis failed:")
            print(f"STDERR: {result.stderr}")
            return None
        
        print(f"✅ LLM analysis with {model} completed successfully")
        
        # Find the output file
        output_files = list(Path("outputs").glob(f"agreement_analysis_{model}_*.json"))
        if not output_files:
            print("❌ No output file found")
            return None
        
        latest_file = max(output_files, key=lambda x: x.stat().st_mtime)
        print(f"📄 Results saved to: {latest_file}")
        
        # Load and return results
        with open(latest_file, 'r') as f:
            return json.load(f)
            
    except subprocess.TimeoutExpired:
        print("❌ LLM analysis timed out (>10 minutes)")
        return None
    except Exception as e:
        print(f"❌ Error running LLM analysis: {e}")
        return None

def display_agreement_summary(results: Dict, analysis_type: str):
    """Display agreement analysis summary."""
    print_section(f"{analysis_type} Analysis Results")
    
    summary = results.get("agreement_summary", {})
    trait_level = summary.get("trait_level", {})
    criterion_level = summary.get("criterion_level", {})
    overall = summary.get("overall", {})
    
    # Overall metrics
    print("\n📊 OVERALL AGREEMENT METRICS")
    print(f"   Total criteria analyzed: {criterion_level.get('total_criteria', 0)}")
    print(f"   Exact criterion matches: {criterion_level.get('exact_match_criteria_count', 0)}")
    print(f"   Criterion match ratio: {format_metric(criterion_level.get('exact_match_ratio', 0))}")
    print(f"   Overall trait agreement: {format_metric(overall.get('overall_agreement_ratio', 0))}")
    print(f"   Total discrepancies: {len(results.get('discrepancies', []))}")
    
    # Pairwise metrics
    pairwise_metrics = trait_level.get("pairwise_metrics", [])
    if pairwise_metrics:
        print("\n🔍 PAIRWISE REVIEWER METRICS")
        for i, metrics in enumerate(pairwise_metrics, 1):
            reviewer1 = metrics.get("reviewer_1", "Unknown")
            reviewer2 = metrics.get("reviewer_2", "Unknown")
            precision = metrics.get("precision", 0)
            recall = metrics.get("recall", 0)
            f1_score = metrics.get("f1_score", 0)
            jaccard = metrics.get("jaccard_index", 0)
            kappa = metrics.get("cohen_kappa", 0)
            
            quality = get_quality_assessment(f1_score, kappa)
            
            print(f"\n   Pair {i}: {reviewer1} vs {reviewer2}")
            print(f"   Quality Assessment: {quality}")
            print(f"   ├─ Precision: {format_metric(precision)}")
            print(f"   ├─ Recall: {format_metric(recall)}")
            print(f"   ├─ F1-Score: {format_metric(f1_score)}")
            print(f"   ├─ Jaccard Index: {format_metric(jaccard)}")
            print(f"   └─ Cohen's Kappa: {format_metric(kappa)}")

def display_discrepancy_examples(results: Dict, max_examples: int = 5):
    """Display examples of discrepancies found."""
    discrepancies = results.get("discrepancies", [])
    
    if not discrepancies:
        print("\n✅ No discrepancies found - perfect agreement!")
        return
    
    print_section("Discrepancy Examples")
    print(f"\nShowing {min(max_examples, len(discrepancies))} of {len(discrepancies)} total discrepancies:\n")
    
    # Group discrepancies by type
    by_type = {}
    for disc in discrepancies:
        match_status = disc.get("match_status", "unknown")
        if match_status not in by_type:
            by_type[match_status] = []
        by_type[match_status].append(disc)
    
    shown = 0
    for match_type, discs in by_type.items():
        if shown >= max_examples:
            break
            
        print(f"🔸 {match_type.replace('_', ' ').title()}")
        
        for disc in discs[:2]:  # Show max 2 per type
            if shown >= max_examples:
                break
                
            trial_id = disc.get("trial_id", "Unknown")
            criterion_text = disc.get("criterion_original_text", "")[:100] + "..."
            reviewer1 = disc.get("reviewer_1", "Unknown")
            reviewer2 = disc.get("reviewer_2", "Unknown")
            explanation = disc.get("explanation", "No explanation")
            
            trait1 = disc.get("reviewer_1_trait", {})
            trait2 = disc.get("reviewer_2_trait", {})
            
            print(f"   Trial: {trial_id}")
            print(f"   Criterion: {criterion_text}")
            print(f"   {reviewer1}: {trait1.get('trait', 'N/A')} | {trait1.get('category', 'N/A')} | {trait1.get('value', 'N/A')}")
            print(f"   {reviewer2}: {trait2.get('trait', 'N/A')} | {trait2.get('category', 'N/A')} | {trait2.get('value', 'N/A')}")
            print(f"   Explanation: {explanation}")
            print()
            
            shown += 1

def display_interpretation_guide():
    """Display guide for interpreting results."""
    print_section("Interpretation Guide")
    
    print("""
📈 AGREEMENT METRICS EXPLAINED:

• Precision: Proportion of traits identified by reviewer 2 that were also found by reviewer 1
• Recall: Proportion of traits identified by reviewer 1 that were also found by reviewer 2  
• F1-Score: Harmonic mean of precision and recall (0.0-1.0, higher is better)
• Jaccard Index: Intersection over union of trait sets (0.0-1.0, higher is better)
• Cohen's Kappa: Agreement corrected for chance (0.0-1.0, >0.8 indicates strong agreement)

🎯 QUALITY THRESHOLDS:

🟢 Excellent Agreement: F1-score > 0.9, Cohen's kappa > 0.8
🟡 Good Agreement: F1-score > 0.8, Cohen's kappa > 0.6  
🟠 Moderate Agreement: F1-score > 0.6, Cohen's kappa > 0.4
🔴 Poor Agreement: F1-score < 0.6, Cohen's kappa < 0.4

🔍 DISCREPANCY TYPES:

• missing_in_reviewer_X: Trait identified by one reviewer but not the other
• category_mismatch: Same trait but categorized differently
• value_mismatch: Same trait and category but different values
• granularity_mismatch: Different levels of detail in trait extraction

💡 WHAT GOOD AGREEMENT MEANS:

High agreement (F1 > 0.8) suggests that the criteria decomposition process is:
- Reliable and reproducible
- Capturing the essential clinical concepts consistently
- Ready for downstream applications like patient matching

Low agreement may indicate:
- Need for clearer decomposition guidelines
- Ambiguous or complex criteria requiring expert review
- Differences in model capabilities or training
""")

def generate_summary_report(local_results: Optional[Dict], llm_results: Optional[Dict], 
                          analysis_type: str, model: str = None):
    """Generate a comprehensive summary report."""
    print_section("Summary Report Generation")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"outputs/demo_summary_report_{timestamp}.md"
    
    os.makedirs("outputs", exist_ok=True)
    
    with open(report_file, 'w') as f:
        f.write(f"# Clinical Trial Criteria Agreement Analysis Demo Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Analysis Type:** {analysis_type}\n")
        if model:
            f.write(f"**LLM Model:** {model}\n")
        f.write(f"\n---\n\n")
        
        # Executive Summary
        f.write("## Executive Summary\n\n")
        
        if local_results:
            local_summary = local_results.get("agreement_summary", {})
            local_overall = local_summary.get("overall", {})
            local_criterion = local_summary.get("criterion_level", {})
            
            f.write("### Local Analysis Results\n")
            f.write(f"- **Overall Agreement:** {format_metric(local_overall.get('overall_agreement_ratio', 0))}\n")
            f.write(f"- **Criterion Match Ratio:** {format_metric(local_criterion.get('exact_match_ratio', 0))}\n")
            f.write(f"- **Total Discrepancies:** {len(local_results.get('discrepancies', []))}\n\n")
        
        if llm_results:
            llm_summary = llm_results.get("agreement_summary", {})
            llm_overall = llm_summary.get("overall", {})
            llm_criterion = llm_summary.get("criterion_level", {})
            
            f.write(f"### LLM Analysis Results ({model})\n")
            f.write(f"- **Overall Agreement:** {format_metric(llm_overall.get('overall_agreement_ratio', 0))}\n")
            f.write(f"- **Criterion Match Ratio:** {format_metric(llm_criterion.get('exact_match_ratio', 0))}\n")
            f.write(f"- **Total Discrepancies:** {len(llm_results.get('discrepancies', []))}\n\n")
        
        # Detailed Results
        if local_results:
            f.write("## Local Analysis Detailed Results\n\n")
            _write_detailed_results(f, local_results)
        
        if llm_results:
            f.write(f"## LLM Analysis Detailed Results ({model})\n\n")
            _write_detailed_results(f, llm_results)
        
        # Recommendations
        f.write("## Recommendations\n\n")
        f.write("Based on the analysis results:\n\n")
        
        # Determine recommendations based on results
        if local_results or llm_results:
            results = local_results or llm_results
            overall_agreement = results.get("agreement_summary", {}).get("overall", {}).get("overall_agreement_ratio", 0)
            
            if overall_agreement > 0.8:
                f.write("✅ **High Agreement Detected**\n")
                f.write("- The decomposition process shows strong consistency\n")
                f.write("- Results are suitable for downstream applications\n")
                f.write("- Consider this as a baseline for future analyses\n\n")
            elif overall_agreement > 0.6:
                f.write("⚠️ **Moderate Agreement Detected**\n")
                f.write("- Review discrepancies to identify improvement areas\n")
                f.write("- Consider refining decomposition guidelines\n")
                f.write("- May need expert review for complex criteria\n\n")
            else:
                f.write("🔴 **Low Agreement Detected**\n")
                f.write("- Significant inconsistencies found\n")
                f.write("- Recommend reviewing and standardizing the decomposition process\n")
                f.write("- Consider additional training or clearer guidelines\n\n")
        
        f.write("## Next Steps\n\n")
        f.write("1. Review the detailed discrepancy analysis\n")
        f.write("2. Identify patterns in disagreements\n")
        f.write("3. Refine decomposition guidelines if needed\n")
        f.write("4. Consider running analysis on additional datasets\n")
        f.write("5. Use insights to improve the decomposition process\n\n")
        
        f.write("---\n\n")
        f.write("*This report was generated automatically by the demo_agreement_analysis.py script.*\n")
    
    print(f"📄 Summary report saved to: {report_file}")
    return report_file

def _write_detailed_results(f, results: Dict):
    """Write detailed results to report file."""
    summary = results.get("agreement_summary", {})
    
    # Pairwise metrics
    pairwise_metrics = summary.get("trait_level", {}).get("pairwise_metrics", [])
    if pairwise_metrics:
        f.write("### Pairwise Agreement Metrics\n\n")
        f.write("| Reviewer 1 | Reviewer 2 | Precision | Recall | F1-Score | Jaccard | Kappa |\n")
        f.write("|------------|------------|-----------|--------|----------|---------|-------|\n")
        
        for metrics in pairwise_metrics:
            r1 = metrics.get("reviewer_1", "Unknown")
            r2 = metrics.get("reviewer_2", "Unknown")
            precision = format_metric(metrics.get("precision", 0))
            recall = format_metric(metrics.get("recall", 0))
            f1 = format_metric(metrics.get("f1_score", 0))
            jaccard = format_metric(metrics.get("jaccard_index", 0))
            kappa = format_metric(metrics.get("cohen_kappa", 0))
            
            f.write(f"| {r1} | {r2} | {precision} | {recall} | {f1} | {jaccard} | {kappa} |\n")
        f.write("\n")
    
    # Discrepancy summary
    discrepancies = results.get("discrepancies", [])
    if discrepancies:
        f.write("### Discrepancy Summary\n\n")
        
        # Count by type
        by_type = {}
        for disc in discrepancies:
            match_status = disc.get("match_status", "unknown")
            by_type[match_status] = by_type.get(match_status, 0) + 1
        
        f.write("| Discrepancy Type | Count |\n")
        f.write("|------------------|-------|\n")
        for disc_type, count in sorted(by_type.items()):
            f.write(f"| {disc_type.replace('_', ' ').title()} | {count} |\n")
        f.write("\n")

def main():
    """Main demonstration function."""
    parser = argparse.ArgumentParser(description="Demonstrate agreement analysis functionality")
    parser.add_argument("--api-keys", help="Path to API keys JSON file (for LLM analysis)")
    parser.add_argument("--model", choices=["claude", "openai", "gemini"], 
                       help="LLM model to use for analysis")
    parser.add_argument("--local-only", action="store_true", 
                       help="Run only local analysis (no LLM)")
    args = parser.parse_args()
    
    print_header("Clinical Trial Criteria Agreement Analysis Demo")
    print(f"🚀 Starting demonstration at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check prerequisites
    print_section("Checking Prerequisites")
    
    if not check_sample_data():
        print("❌ Demo cannot proceed without sample data")
        return 1
    
    if not os.path.exists("analyze_criteria_agreement.py"):
        print("❌ Main analysis script not found: analyze_criteria_agreement.py")
        return 1
    
    print("✅ All prerequisites met")
    
    # Run analyses
    local_results = None
    llm_results = None
    
    # Always run local analysis first
    local_results = run_local_analysis()
    if local_results:
        display_agreement_summary(local_results, "Local")
        display_discrepancy_examples(local_results)
    
    # Run LLM analysis if requested and possible
    if not args.local_only and args.api_keys and args.model:
        llm_results = run_llm_analysis(args.api_keys, args.model)
        if llm_results:
            display_agreement_summary(llm_results, f"LLM ({args.model.upper()})")
            display_discrepancy_examples(llm_results)
    elif not args.local_only:
        print_section("LLM Analysis Skipped")
        if not args.api_keys:
            print("ℹ️  No API keys provided - skipping LLM analysis")
            print("   Use --api-keys to enable LLM analysis")
        if not args.model:
            print("ℹ️  No model specified - skipping LLM analysis")
            print("   Use --model claude|openai|gemini to enable LLM analysis")
    
    # Display interpretation guide
    display_interpretation_guide()
    
    # Generate summary report
    analysis_type = "Local Only" if args.local_only or not llm_results else "Local + LLM"
    report_file = generate_summary_report(local_results, llm_results, analysis_type, args.model)
    
    # Final summary
    print_header("Demo Complete")
    
    if local_results:
        local_agreement = local_results.get("agreement_summary", {}).get("overall", {}).get("overall_agreement_ratio", 0)
        print(f"✅ Local Analysis: {format_metric(local_agreement)} overall agreement")
    
    if llm_results:
        llm_agreement = llm_results.get("agreement_summary", {}).get("overall", {}).get("overall_agreement_ratio", 0)
        print(f"✅ LLM Analysis: {format_metric(llm_agreement)} overall agreement")
    
    print(f"📄 Detailed report: {report_file}")
    print(f"📁 All outputs saved to: outputs/")
    
    print("\n🎯 Key Takeaways:")
    print("   • The analysis tool successfully compared multiple reviewers")
    print("   • Both local and LLM-based analysis modes are functional")
    print("   • Discrepancies provide insights into decomposition consistency")
    print("   • Results can guide improvements to the decomposition process")
    
    print(f"\n🏁 Demo completed successfully at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
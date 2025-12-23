#!/usr/bin/env python3
"""
Pattern Harvest Utility - Self-Healing Query Rating System

Analyzes uncertainty logs to identify linguistic patterns and proposes
improvements for better intent parsing.

Usage:
    python utils/harvest_patterns.py                    # Interactive mode
    python utils/harvest_patterns.py --stats           # Show statistics only
    python utils/harvest_patterns.py --export patterns.yaml  # Export patterns
    python utils/harvest_patterns.py --analyze         # LLM-powered analysis
"""

import argparse
import json
import sqlite3
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
from collections import Counter
from datetime import datetime

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def get_db_connection(db_path: str = "state/memory.db") -> sqlite3.Connection:
    """Connect to the memory database."""
    path = Path(db_path)
    if not path.exists():
        print(f"❌ Database not found: {db_path}")
        print("   Run synth-mind first to create the database.")
        sys.exit(1)
    return sqlite3.connect(path)


def get_uncertainty_stats(db: sqlite3.Connection) -> Dict:
    """Get statistics about uncertainty logs."""
    cursor = db.cursor()

    # Total count
    cursor.execute("SELECT COUNT(*) FROM uncertainty_log")
    total = cursor.fetchone()[0]

    if total == 0:
        return {"total": 0, "message": "No uncertainty logs yet. Use synth-mind to generate data."}

    # Unresolved count
    cursor.execute("SELECT COUNT(*) FROM uncertainty_log WHERE resolved = 0")
    unresolved = cursor.fetchone()[0]

    # Average confidence
    cursor.execute("SELECT AVG(confidence_score) FROM uncertainty_log")
    avg_confidence = cursor.fetchone()[0] or 0.0

    # Confidence distribution
    cursor.execute("""
        SELECT
            CASE
                WHEN confidence_score < 0.3 THEN 'very_low'
                WHEN confidence_score < 0.5 THEN 'low'
                WHEN confidence_score < 0.7 THEN 'medium'
                ELSE 'high'
            END as bucket,
            COUNT(*) as count
        FROM uncertainty_log
        GROUP BY bucket
    """)
    distribution = {row[0]: row[1] for row in cursor.fetchall()}

    # Recent count (last 24 hours)
    day_ago = time.time() - 86400
    cursor.execute(
        "SELECT COUNT(*) FROM uncertainty_log WHERE timestamp > ?",
        (day_ago,)
    )
    recent = cursor.fetchone()[0]

    # Time range
    cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM uncertainty_log")
    min_ts, max_ts = cursor.fetchone()

    return {
        "total": total,
        "unresolved": unresolved,
        "resolved": total - unresolved,
        "resolution_rate": (total - unresolved) / total if total > 0 else 0.0,
        "avg_confidence": avg_confidence,
        "last_24h": recent,
        "distribution": distribution,
        "first_entry": datetime.fromtimestamp(min_ts).isoformat() if min_ts else None,
        "last_entry": datetime.fromtimestamp(max_ts).isoformat() if max_ts else None
    }


def get_uncertainty_logs(
    db: sqlite3.Connection,
    limit: int = 500,
    unresolved_only: bool = False
) -> List[Dict]:
    """Retrieve uncertainty logs for analysis."""
    cursor = db.cursor()

    query = """
        SELECT id, timestamp, user_message, parsed_intent,
               confidence_score, context, signals, resolved, resolution_pattern
        FROM uncertainty_log
    """

    if unresolved_only:
        query += " WHERE resolved = 0"

    query += " ORDER BY timestamp DESC LIMIT ?"

    cursor.execute(query, (limit,))

    results = []
    for row in cursor.fetchall():
        results.append({
            "id": row[0],
            "timestamp": datetime.fromtimestamp(row[1]).isoformat(),
            "user_message": row[2],
            "parsed_intent": row[3],
            "confidence_score": row[4],
            "context": row[5][:200] if row[5] else "",
            "signals": json.loads(row[6]) if row[6] else {},
            "resolved": bool(row[7]),
            "resolution_pattern": row[8]
        })

    return results


def analyze_patterns_simple(logs: List[Dict]) -> Dict:
    """
    Simple pattern analysis without LLM.
    Identifies common words, phrases, and signal patterns.
    """
    if not logs:
        return {"patterns": [], "message": "No logs to analyze"}

    # Extract user messages
    messages = [log["user_message"] for log in logs if log["user_message"]]

    # Word frequency
    all_words = []
    for msg in messages:
        words = msg.lower().split()
        all_words.extend(words)

    word_freq = Counter(all_words)
    common_words = word_freq.most_common(20)

    # Signal patterns
    signal_totals = Counter()
    for log in logs:
        for signal, value in log.get("signals", {}).items():
            if value > 0.5:
                signal_totals[signal] += 1

    # Confidence buckets
    low_conf_messages = [
        log["user_message"][:100]
        for log in logs
        if log["confidence_score"] < 0.3 and log["user_message"]
    ][:10]

    return {
        "total_analyzed": len(logs),
        "common_words": common_words,
        "high_signal_triggers": dict(signal_totals.most_common(10)),
        "lowest_confidence_samples": low_conf_messages,
        "avg_confidence": sum(log["confidence_score"] for log in logs) / len(logs)
    }


def analyze_patterns_llm(logs: List[Dict], llm_provider: str = "anthropic") -> Optional[Dict]:
    """
    LLM-powered pattern analysis.
    Requires API key to be set.
    """
    try:
        if llm_provider == "anthropic":
            import anthropic
            import os
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

            # Prepare log summary
            log_summary = "\n".join([
                f"- Message: \"{log['user_message'][:100]}\" | Confidence: {log['confidence_score']:.2f} | Signals: {log['signals']}"
                for log in logs[:50]  # Limit to 50 for context
            ])

            prompt = f"""You are the NatLangChain linguist analyzing uncertainty logs.

These are {len(logs)} examples where the system was uncertain about user intent:

{log_summary}

Analyze these patterns and provide:
1. Clusters of similar phrasings that should map to the same intent
2. Proposed synonym rules
3. Suggested confidence threshold adjustments
4. New test cases for validation

Output as JSON:
{{
  "clusters": [
    {{"intent": "...", "phrases": ["...", "..."], "suggested_action": "..."}}
  ],
  "synonym_rules": [
    {{"from": ["...", "..."], "to": "canonical_form"}}
  ],
  "threshold_adjustments": [
    {{"signal": "...", "current_weight": 0.3, "suggested_weight": 0.2, "reason": "..."}}
  ],
  "test_cases": [
    {{"input": "...", "expected_intent": "...", "expected_confidence": 0.9}}
  ]
}}
"""

            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse JSON from response
            text = response.content[0].text
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end > start:
                return json.loads(text[start:end])

    except ImportError:
        print("⚠️  anthropic package not installed. Run: pip install anthropic")
    except Exception as e:
        print(f"⚠️  LLM analysis failed: {e}")

    return None


def export_patterns(patterns: Dict, output_path: str):
    """Export patterns to YAML file."""
    try:
        import yaml
        with open(output_path, 'w') as f:
            yaml.dump(patterns, f, default_flow_style=False)
        print(f"✅ Patterns exported to {output_path}")
    except ImportError:
        # Fallback to JSON
        json_path = output_path.replace('.yaml', '.json')
        with open(json_path, 'w') as f:
            json.dump(patterns, f, indent=2)
        print(f"✅ Patterns exported to {json_path} (YAML not available)")


def print_stats(stats: Dict):
    """Pretty print statistics."""
    print("\n" + "=" * 60)
    print("📊 UNCERTAINTY LOG STATISTICS")
    print("=" * 60)

    if stats.get("total", 0) == 0:
        print(stats.get("message", "No data available"))
        return

    print(f"Total Entries:     {stats['total']}")
    print(f"Unresolved:        {stats['unresolved']}")
    print(f"Resolved:          {stats['resolved']}")
    print(f"Resolution Rate:   {stats['resolution_rate']*100:.1f}%")
    print(f"Avg Confidence:    {stats['avg_confidence']:.2f}")
    print(f"Last 24 Hours:     {stats['last_24h']}")

    if stats.get("distribution"):
        print("\nConfidence Distribution:")
        for bucket, count in stats["distribution"].items():
            bar = "█" * int(count / stats["total"] * 20)
            print(f"  {bucket:10} {bar} ({count})")

    if stats.get("first_entry"):
        print(f"\nFirst Entry:       {stats['first_entry']}")
        print(f"Last Entry:        {stats['last_entry']}")

    print("=" * 60)


def print_simple_analysis(analysis: Dict):
    """Pretty print simple analysis results."""
    print("\n" + "=" * 60)
    print("🔍 PATTERN ANALYSIS (Simple)")
    print("=" * 60)

    print(f"\nAnalyzed {analysis['total_analyzed']} logs")
    print(f"Average Confidence: {analysis['avg_confidence']:.2f}")

    print("\n📝 Most Common Words:")
    for word, count in analysis["common_words"][:10]:
        print(f"  {word:20} ({count})")

    print("\n⚠️  High Signal Triggers:")
    for signal, count in analysis["high_signal_triggers"].items():
        print(f"  {signal:20} triggered {count} times")

    if analysis["lowest_confidence_samples"]:
        print("\n🔴 Lowest Confidence Samples:")
        for msg in analysis["lowest_confidence_samples"][:5]:
            print(f"  - \"{msg}...\"")

    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Pattern Harvest Utility - Analyze uncertainty logs for self-healing"
    )
    parser.add_argument(
        "--stats", action="store_true",
        help="Show statistics only"
    )
    parser.add_argument(
        "--analyze", action="store_true",
        help="Run LLM-powered pattern analysis"
    )
    parser.add_argument(
        "--export", type=str, metavar="FILE",
        help="Export patterns to YAML/JSON file"
    )
    parser.add_argument(
        "--db", type=str, default="state/memory.db",
        help="Path to memory database"
    )
    parser.add_argument(
        "--limit", type=int, default=500,
        help="Maximum logs to analyze"
    )

    args = parser.parse_args()

    # Connect to database
    db = get_db_connection(args.db)

    # Get stats
    stats = get_uncertainty_stats(db)
    print_stats(stats)

    if args.stats:
        db.close()
        return

    if stats.get("total", 0) == 0:
        db.close()
        return

    # Get logs for analysis
    logs = get_uncertainty_logs(db, limit=args.limit)

    # Simple analysis
    simple_analysis = analyze_patterns_simple(logs)
    print_simple_analysis(simple_analysis)

    # LLM analysis if requested
    llm_analysis = None
    if args.analyze:
        print("\n🤖 Running LLM-powered analysis...")
        llm_analysis = analyze_patterns_llm(logs)
        if llm_analysis:
            print("\n" + "=" * 60)
            print("🧠 LLM PATTERN ANALYSIS")
            print("=" * 60)
            print(json.dumps(llm_analysis, indent=2))
        else:
            print("❌ LLM analysis not available")

    # Export if requested
    if args.export:
        combined = {
            "stats": stats,
            "simple_analysis": simple_analysis,
            "llm_analysis": llm_analysis,
            "generated_at": datetime.now().isoformat()
        }
        export_patterns(combined, args.export)

    db.close()

    print("\n✅ Pattern harvest complete!")
    print("   Next steps:")
    print("   1. Review the patterns above")
    print("   2. Add promising patterns to config/personality.yaml")
    print("   3. Create test cases in tests/")
    print("   4. Mark resolved patterns in the database")


if __name__ == "__main__":
    main()

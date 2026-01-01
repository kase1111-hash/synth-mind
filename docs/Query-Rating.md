# Self-Healing Query System

Synth Mind includes a self-healing system that learns from its own uncertainties. When the system is unsure how to interpret user input, it logs the uncertainty and later analyzes patterns to improve.

## How It Works

### 1. Uncertainty Logging

When confidence drops below 80%, the Assurance module automatically:
- Logs the user message and parsed intent
- Records confidence score and context
- Saves uncertainty signals to `state/memory.db`

This happens transparently during normal operation.

### 2. Database Schema

Uncertainties are stored in the `uncertainty_log` table:

```sql
CREATE TABLE uncertainty_log (
    id INTEGER PRIMARY KEY,
    timestamp REAL,
    user_message TEXT,
    parsed_intent TEXT,
    confidence_score REAL,
    context TEXT,
    signals TEXT,              -- JSON: {"ambiguity": 0.8, "missing_context": 0.5}
    resolved INTEGER DEFAULT 0,
    resolution_pattern TEXT
);
```

### 3. Pattern Harvesting

Use the harvest utility to analyze accumulated logs:

```bash
# View statistics
python utils/harvest_patterns.py --stats

# Simple pattern analysis
python utils/harvest_patterns.py

# LLM-powered deep analysis (requires API key)
python utils/harvest_patterns.py --analyze

# Export patterns for review
python utils/harvest_patterns.py --export patterns.yaml
```

## Usage

### Viewing Statistics

```bash
python utils/harvest_patterns.py --stats
```

Output:
```
========================================
📊 UNCERTAINTY LOG STATISTICS
========================================
Total Entries:     234
Unresolved:        67
Resolved:          167
Resolution Rate:   71.4%
Avg Confidence:    0.42
Last 24 Hours:     12

Confidence Distribution:
  very_low   ████████ (89)
  low        ██████ (72)
  medium     ████ (48)
  high       ██ (25)
========================================
```

### Running Pattern Analysis

```bash
python utils/harvest_patterns.py
```

This runs simple pattern detection:
- Most common words in uncertain queries
- High-frequency uncertainty signals
- Samples of lowest-confidence messages

### LLM-Powered Analysis

```bash
export ANTHROPIC_API_KEY="your-key"
python utils/harvest_patterns.py --analyze
```

The LLM analyzes patterns and proposes:
- **Clusters**: Similar phrases that map to the same intent
- **Synonym rules**: Equivalent phrasings to normalize
- **Threshold adjustments**: Signal weights to tune
- **Test cases**: Validation tests for improvements

Example output:
```yaml
clusters:
  - intent: "create_storage"
    phrases:
      - "store my files"
      - "backup my data"
      - "upload everything"
    suggested_action: "create_storage_contract"

synonym_rules:
  - from: ["gonna", "going to", "will"]
    to: "future_intent"

test_cases:
  - input: "Keep my photos safe for 30 days"
    expected_intent: "ephemeral_storage"
    expected_confidence: 0.9
```

### Exporting Patterns

```bash
python utils/harvest_patterns.py --export patterns.yaml
```

Creates a YAML file with:
- Current statistics
- Simple analysis results
- LLM analysis (if run with `--analyze`)
- Timestamp

## Integration Points

### Memory System (`core/memory.py`)

```python
# Log uncertainty
memory.log_uncertainty(
    user_message="unclear input",
    parsed_intent="unknown",
    confidence_score=0.35,
    context="...",
    signals={"ambiguity": 0.8}
)

# Retrieve logs
logs = memory.get_uncertainty_logs(limit=100, unresolved_only=True)

# Mark as resolved
memory.mark_uncertainty_resolved(log_id=42, resolution_pattern="synonym_added")

# Get statistics
stats = memory.get_uncertainty_stats()
```

### Assurance Module (`psychological/assurance_resolution.py`)

The Assurance module automatically logs uncertainties when:
- Confidence score < 0.8
- Multiple ambiguity signals detected
- Intent parsing fails

Logs are linked to concerns for resolution tracking.

## Workflow

### Monthly Improvement Cycle

1. **Collect** - Run Synth Mind normally (uncertainties log automatically)
2. **Analyze** - Run `harvest_patterns.py --analyze`
3. **Review** - Examine proposed patterns in exported YAML
4. **Implement** - Add confirmed patterns to `config/personality.yaml`
5. **Test** - Create test cases for new patterns
6. **Resolve** - Mark resolved uncertainties in database

### Expected Improvement

| Month | Uncertainty Rate | Notes |
|-------|-----------------|-------|
| 1 | ~20% | Baseline |
| 2 | ~15% | First pattern batch |
| 3 | ~10% | Synonym expansion |
| 6 | ~5% | Edge cases resolved |

## Configuration

### Adjusting Thresholds

In `config/personality.yaml`:

```yaml
assurance:
  confidence_threshold: 0.8    # Log below this

query_rating:
  log_all_turns: false         # Only log uncertain
  min_context_length: 50       # Context to store
```

### Signal Weights

Uncertainty signals can be tuned:

```yaml
signals:
  ambiguity: 0.3        # Weight for ambiguous phrasing
  missing_context: 0.2  # Weight for incomplete context
  novel_pattern: 0.25   # Weight for unknown patterns
  conflicting_intent: 0.25  # Weight for mixed signals
```

## Troubleshooting

### No Logs Appearing
- Check that `state/memory.db` exists
- Verify Assurance module is enabled
- Confirm confidence threshold isn't too low

### Too Many Logs
- Increase `confidence_threshold`
- Enable `log_all_turns: false`
- Add common patterns to reduce noise

### LLM Analysis Failing
- Verify `ANTHROPIC_API_KEY` is set
- Check API rate limits
- Try with smaller `--limit` value

## Related Documentation

- [system-arch.md](system-arch.md) - Architecture overview
- [SPEC_SHEET.md](../SPEC_SHEET.md) - Technical specifications

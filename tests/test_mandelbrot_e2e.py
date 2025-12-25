"""
End-to-end test for Mandelbrot word weighting system.
Tests the utility class, integration with AssuranceResolutionModule,
and configuration loading.
"""

import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.mandelbrot_weighting import MandelbrotWeighting


def test_mandelbrot_weighting_class():
    """Test the core MandelbrotWeighting class."""
    print("\n" + "=" * 60)
    print("TEST 1: MandelbrotWeighting Class")
    print("=" * 60)

    # Initialize with default parameters
    mw = MandelbrotWeighting(alpha=1.0, beta=2.5)
    print(f"✓ Initialized with α={mw.alpha}, β={mw.beta}")

    # Test tokenization
    text = "Please schedule an ephemeral backup for my critical database"
    tokens = mw.tokenize(text)
    print(f"✓ Tokenized: {tokens}")

    # Build corpus from sample texts
    sample_texts = [
        "I need to store my files temporarily",
        "Can you help me with the project?",
        "The server is running fine",
        "Please update the configuration",
        "I want to delete the old backups",
        "Schedule a reminder for tomorrow",
        "The API endpoint is not working",
        "Create a new storage container",
    ]
    mw.update_corpus_batch(sample_texts)
    print(f"✓ Corpus built: {mw.total_words} words, {len(mw.word_frequencies)} unique")

    # Test word weights
    print("\n  Word weights (higher = more informative):")
    test_words = ["the", "is", "schedule", "ephemeral", "database", "backup", "critical"]
    for word in test_words:
        weight = mw.compute_weight(word)
        explanation = mw.explain_weight(word)
        print(f"    '{word}': {weight:.3f} (rank={explanation['rank']}, stopword={explanation['is_stopword']})")

    # Test weighted word scoring
    hedge_words = ["maybe", "perhaps", "might", "possibly", "conceivably"]
    text_with_hedging = "I think this might possibly work, but I'm unsure"
    text_without_hedging = "This will definitely work perfectly"

    score_hedging = mw.weighted_word_score(text_with_hedging, hedge_words)
    score_no_hedging = mw.weighted_word_score(text_without_hedging, hedge_words)
    print(f"\n  Hedging detection:")
    print(f"    '{text_with_hedging[:40]}...' → score: {score_hedging:.3f}")
    print(f"    '{text_without_hedging[:40]}...' → score: {score_no_hedging:.3f}")
    assert score_hedging > score_no_hedging, "Hedging text should score higher"
    print("  ✓ Hedging text correctly scores higher")

    # Test sentiment scoring
    positive = ["good", "great", "excellent", "perfect"]
    negative = ["bad", "terrible", "broken", "error"]

    pos_text = "This is great, it works perfectly!"
    neg_text = "This is terrible, completely broken"
    neutral_text = "The system is processing the request"

    pos_score = mw.weighted_sentiment_score(pos_text, positive, negative)
    neg_score = mw.weighted_sentiment_score(neg_text, positive, negative)
    neut_score = mw.weighted_sentiment_score(neutral_text, positive, negative)

    print(f"\n  Sentiment scoring:")
    print(f"    Positive text: {pos_score:.3f}")
    print(f"    Negative text: {neg_score:.3f}")
    print(f"    Neutral text: {neut_score:.3f}")
    assert pos_score > 0, "Positive text should have positive score"
    assert neg_score < 0, "Negative text should have negative score"
    print("  ✓ Sentiment scoring works correctly")

    # Test domain boosts
    mw.add_domain_boost({"ephemeral": 2.0, "critical": 1.8})
    weight_before = mw.compute_weight("storage")
    weight_boosted = mw.compute_weight("ephemeral")
    print(f"\n  Domain boosts:")
    print(f"    'storage' (no boost): {weight_before:.3f}")
    print(f"    'ephemeral' (2.0x boost): {weight_boosted:.3f}")
    print("  ✓ Domain boosts applied")

    # Test text importance
    specific_text = "Configure the ephemeral webhook API endpoint"
    generic_text = "I want to do the thing with the stuff"
    specific_importance = mw.compute_text_importance(specific_text)
    generic_importance = mw.compute_text_importance(generic_text)
    print(f"\n  Text importance:")
    print(f"    Specific: '{specific_text}' → {specific_importance:.3f}")
    print(f"    Generic: '{generic_text}' → {generic_importance:.3f}")

    # Test top weighted words
    analysis_text = "Please schedule an ephemeral backup for the critical production database server"
    top_words = mw.get_top_weighted_words(analysis_text, n=5)
    print(f"\n  Top weighted words in: '{analysis_text}'")
    for word, weight in top_words:
        print(f"    {word}: {weight:.3f}")

    # Test parameter tuning
    print("\n  Parameter tuning:")
    mw.configure(alpha=1.5, beta=3.0)
    print(f"  ✓ Reconfigured to α={mw.alpha}, β={mw.beta}")

    stats = mw.get_stats()
    print(f"\n  Final stats: {json.dumps(stats, indent=4)}")

    print("\n✓ TEST 1 PASSED: MandelbrotWeighting class works correctly")
    return True


def test_assurance_module_integration():
    """Test integration with AssuranceResolutionModule."""
    print("\n" + "=" * 60)
    print("TEST 2: AssuranceResolutionModule Integration")
    print("=" * 60)

    # Create mock objects for dependencies
    class MockLLM:
        pass

    class MockMemory:
        def grounding_confidence(self, text):
            return 0.7  # Moderate confidence

        def store_episodic(self, **kwargs):
            pass

        def log_uncertainty(self, **kwargs):
            return 1

        def get_uncertainty_stats(self):
            return {"total_entries": 0}

    class MockEmotion:
        def apply_reward_signal(self, **kwargs):
            pass

        def adjust_tone(self, *args):
            pass

    from psychological.assurance_resolution import AssuranceResolutionModule

    # Initialize with Mandelbrot config
    config = {
        "enabled": True,
        "alpha": 1.0,
        "beta": 2.5,
        "domain_boosts": {
            "ephemeral": 2.0,
            "critical": 1.8,
            "urgent": 1.7
        }
    }

    module = AssuranceResolutionModule(
        llm=MockLLM(),
        memory=MockMemory(),
        emotion_regulator=MockEmotion(),
        mandelbrot_config=config
    )

    assert module.mandelbrot is not None, "Mandelbrot should be initialized"
    print("✓ AssuranceResolutionModule initialized with Mandelbrot weighting")

    # Test uncertainty assessment with different responses
    print("\n  Testing uncertainty assessment:")

    # Confident response
    confident_response = "The database backup will complete in 10 minutes. The storage endpoint is configured correctly."
    uncertainty1, signals1 = module.assess_uncertainty(confident_response, {}, "")
    print(f"\n  Confident response:")
    print(f"    Text: '{confident_response[:50]}...'")
    print(f"    Uncertainty: {uncertainty1:.3f}")
    print(f"    Signals: {json.dumps({k: round(v, 3) for k, v in signals1.items()})}")

    # Uncertain response with hedging
    uncertain_response = "Maybe the backup might work, but I'm unsure if it will possibly complete. Perhaps we should try again."
    uncertainty2, signals2 = module.assess_uncertainty(uncertain_response, {}, "")
    print(f"\n  Uncertain response (with hedging):")
    print(f"    Text: '{uncertain_response[:50]}...'")
    print(f"    Uncertainty: {uncertainty2:.3f}")
    print(f"    Signals: {json.dumps({k: round(v, 3) for k, v in signals2.items()})}")

    assert uncertainty2 > uncertainty1, "Hedging response should have higher uncertainty"
    print("\n  ✓ Hedging response correctly has higher uncertainty")

    # Risky response with absolutes
    risky_response = "This will definitely always work. I guarantee it will never fail under any circumstances."
    uncertainty3, signals3 = module.assess_uncertainty(risky_response, {}, "")
    print(f"\n  Risky response (with absolutes):")
    print(f"    Text: '{risky_response[:50]}...'")
    print(f"    Uncertainty: {uncertainty3:.3f}")
    print(f"    Signals: {json.dumps({k: round(v, 3) for k, v in signals3.items()})}")

    # Test sentiment analysis
    print("\n  Testing sentiment analysis:")
    positive_feedback = "Great job! That works perfectly, thanks!"
    negative_feedback = "No, that's wrong. It's broken and useless."

    pos_sentiment = module._analyze_feedback_sentiment(positive_feedback)
    neg_sentiment = module._analyze_feedback_sentiment(negative_feedback)

    print(f"    Positive feedback: {pos_sentiment:.3f}")
    print(f"    Negative feedback: {neg_sentiment:.3f}")
    assert pos_sentiment > 0, "Positive feedback should have positive sentiment"
    assert neg_sentiment < 0, "Negative feedback should have negative sentiment"
    print("  ✓ Sentiment analysis works correctly")

    # Test runtime configuration
    print("\n  Testing runtime configuration:")
    module.configure_mandelbrot(alpha=1.5, beta=3.0)
    stats = module.get_mandelbrot_stats()
    assert stats["alpha"] == 1.5, "Alpha should be updated"
    assert stats["beta"] == 3.0, "Beta should be updated"
    print(f"  ✓ Runtime config updated: α={stats['alpha']}, β={stats['beta']}")

    # Test word weight explanation
    print("\n  Testing word weight explanation:")
    explanation = module.explain_word_weight("ephemeral")
    print(f"    'ephemeral': weight={explanation['weight']:.3f}, boost={explanation['domain_boost']}")
    assert explanation["has_domain_boost"], "ephemeral should have domain boost"
    print("  ✓ Word weight explanation works")

    # Test top weighted words extraction
    print("\n  Testing top weighted words:")
    test_text = "Please create an urgent ephemeral backup of the critical database"
    top_words = module.get_top_weighted_words(test_text, n=5)
    print(f"    Text: '{test_text}'")
    print(f"    Top words: {top_words}")
    print("  ✓ Top weighted words extraction works")

    print("\n✓ TEST 2 PASSED: AssuranceResolutionModule integration works correctly")
    return True


def test_config_loading():
    """Test configuration loading from personality.yaml."""
    print("\n" + "=" * 60)
    print("TEST 3: Configuration Loading")
    print("=" * 60)

    import yaml

    config_path = Path(__file__).parent.parent / "config" / "personality.yaml"

    if not config_path.exists():
        print(f"⚠️  Config file not found: {config_path}")
        return False

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    mandelbrot_config = config.get("mandelbrot_weighting", {})
    print(f"✓ Loaded mandelbrot_weighting config from personality.yaml")
    print(f"  Config: {json.dumps(mandelbrot_config, indent=4, default=str)}")

    # Validate expected keys
    expected_keys = ["enabled", "alpha", "beta", "min_weight", "max_weight", "domain_boosts"]
    for key in expected_keys:
        assert key in mandelbrot_config, f"Missing key: {key}"
    print(f"✓ All expected keys present: {expected_keys}")

    # Validate parameter ranges
    assert 0.5 <= mandelbrot_config["alpha"] <= 2.0, "Alpha out of range"
    assert 1.0 <= mandelbrot_config["beta"] <= 10.0, "Beta out of range"
    print(f"✓ Parameters within valid ranges")

    # Test that domain_boosts is a dict
    assert isinstance(mandelbrot_config["domain_boosts"], dict), "domain_boosts should be dict"
    print(f"✓ domain_boosts contains {len(mandelbrot_config['domain_boosts'])} entries")

    print("\n✓ TEST 3 PASSED: Configuration loading works correctly")
    return True


def test_full_cycle():
    """Test a full assurance cycle with Mandelbrot weighting."""
    print("\n" + "=" * 60)
    print("TEST 4: Full Assurance Cycle")
    print("=" * 60)

    class MockLLM:
        pass

    class MockMemory:
        def grounding_confidence(self, text):
            return 0.6

        def store_episodic(self, **kwargs):
            pass

        def log_uncertainty(self, **kwargs):
            return 1

        def get_uncertainty_stats(self):
            return {"total_entries": 1}

    class MockEmotion:
        def __init__(self):
            self.signals = []

        def apply_reward_signal(self, **kwargs):
            self.signals.append(kwargs)

        def adjust_tone(self, *args):
            pass

    from psychological.assurance_resolution import AssuranceResolutionModule

    emotion = MockEmotion()
    module = AssuranceResolutionModule(
        llm=MockLLM(),
        memory=MockMemory(),
        emotion_regulator=emotion,
        mandelbrot_config={"enabled": True, "alpha": 1.0, "beta": 2.5}
    )

    # Simulate a conversation turn
    user_message = "Can you schedule an urgent backup of my critical production database?"
    response = "I'll schedule the backup immediately. The process should complete within 15 minutes."

    print(f"  User: '{user_message}'")
    print(f"  Response: '{response}'")

    uncertainty, resolved = module.run_cycle(
        response=response,
        context="Production database management session",
        reasoning_trace={},
        user_message=user_message
    )

    print(f"\n  Cycle results:")
    print(f"    Uncertainty score: {uncertainty:.3f}")
    print(f"    Resolved concerns: {resolved}")
    print(f"    Emotion signals applied: {len(emotion.signals)}")

    # Check corpus was updated
    stats = module.get_mandelbrot_stats()
    print(f"    Corpus size: {stats['corpus_size']} words")
    assert stats["corpus_size"] > 0, "Corpus should have been updated"

    print("\n✓ TEST 4 PASSED: Full assurance cycle works correctly")
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("MANDELBROT WORD WEIGHTING - END-TO-END TEST SUITE")
    print("=" * 60)

    results = []

    try:
        results.append(("MandelbrotWeighting Class", test_mandelbrot_weighting_class()))
    except Exception as e:
        print(f"\n✗ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        results.append(("MandelbrotWeighting Class", False))

    try:
        results.append(("AssuranceModule Integration", test_assurance_module_integration()))
    except Exception as e:
        print(f"\n✗ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        results.append(("AssuranceModule Integration", False))

    try:
        results.append(("Config Loading", test_config_loading()))
    except Exception as e:
        print(f"\n✗ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Config Loading", False))

    try:
        results.append(("Full Cycle", test_full_cycle()))
    except Exception as e:
        print(f"\n✗ TEST 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Full Cycle", False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"  {status}: {name}")

    print(f"\n  Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
        return 0
    else:
        print("\n" + "=" * 60)
        print("SOME TESTS FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())

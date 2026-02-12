"""
Test conversation scenarios for A/B evaluation.
Each scenario is a multi-turn conversation designed to exercise
specific psychological module behaviors.

Categories:
- emotional_support: user frustration, sadness, excitement
- long_coherence: maintain topic over 15+ turns
- ambiguous: should trigger assurance/uncertainty
- topic_pivot: should trigger dreaming mismatch
- identity: "who are you?" across sessions
"""

SCENARIOS = [
    # =========================================================================
    # EMOTIONAL SUPPORT — tests emotion regulator influence on tone
    # =========================================================================
    {
        "name": "frustrated_user_debugging",
        "category": "emotional_support",
        "description": "User is frustrated after hours of debugging",
        "turns": [
            "I've been debugging this for 3 hours and nothing works.",
            "I tried everything the docs say. Still crashes on line 42.",
            "Maybe I should just give up on this project entirely.",
            "You know what, let me try one more time. What do you suggest?",
        ],
    },
    {
        "name": "sad_user_loss",
        "category": "emotional_support",
        "description": "User dealing with personal difficulty",
        "turns": [
            "I'm having a really tough day.",
            "My project got cancelled after 6 months of work.",
            "I feel like all that effort was wasted.",
            "How do I find motivation to start something new?",
        ],
    },
    {
        "name": "excited_user_breakthrough",
        "category": "emotional_support",
        "description": "User excited about a breakthrough",
        "turns": [
            "I just solved a problem I've been stuck on for weeks!",
            "The solution was so elegant - just three lines of code.",
            "I want to share this approach with my team.",
            "Can you help me write it up clearly?",
        ],
    },
    {
        "name": "angry_user_broken_deploy",
        "category": "emotional_support",
        "description": "User angry about production incident",
        "turns": [
            "The deploy just broke production. Again.",
            "This is the third time this month. Our CI is useless.",
            "Management won't give us time to fix the pipeline.",
            "What's the fastest way to roll back and stabilize?",
        ],
    },
    {
        "name": "anxious_user_interview",
        "category": "emotional_support",
        "description": "User anxious about upcoming technical interview",
        "turns": [
            "I have a system design interview tomorrow and I'm freaking out.",
            "I've been studying for weeks but I still feel unprepared.",
            "What if they ask about distributed systems? I'm weak there.",
            "Can you quiz me on a typical system design question?",
        ],
    },
    # =========================================================================
    # LONG COHERENCE — tests identity/narrative maintenance over many turns
    # =========================================================================
    {
        "name": "extended_architecture_discussion",
        "category": "long_coherence",
        "description": "Deep dive into system architecture over many turns",
        "turns": [
            "I'm designing a real-time notification system. Where should I start?",
            "What messaging pattern works best for millions of users?",
            "Should I use Kafka or RabbitMQ for this scale?",
            "How do I handle message ordering guarantees?",
            "What about exactly-once delivery semantics?",
            "Let's talk about the consumer side. How many partitions?",
            "How do I handle consumer lag and backpressure?",
            "What monitoring should I set up for the pipeline?",
            "Can you summarize the architecture we've designed so far?",
            "Now let's add push notifications on top of this.",
            "How do I handle millions of WebSocket connections?",
            "What about users who are offline? Store and forward?",
            "Let's add notification preferences and filtering.",
            "How should I handle notification deduplication?",
            "Can you give me a final architecture summary?",
        ],
    },
    {
        "name": "iterative_code_review",
        "category": "long_coherence",
        "description": "Multiple rounds of code review on same function",
        "turns": [
            "Review this function: def process(data): return [x*2 for x in data if x > 0]",
            "Good points. How would you handle None values in the list?",
            "What about type hints? Add those.",
            "Now add error handling for non-numeric inputs.",
            "Add logging for filtered-out values.",
            "Now make it work with generators for large datasets.",
            "Add a parameter to customize the filter threshold.",
            "Write tests for all these changes.",
            "Are we maintaining backward compatibility?",
            "Give me the final version with all improvements.",
        ],
    },
    # =========================================================================
    # AMBIGUOUS — should trigger assurance/uncertainty detection
    # =========================================================================
    {
        "name": "vague_requirements",
        "category": "ambiguous",
        "description": "User gives vague, contradictory requirements",
        "turns": [
            "Build me something that makes data easier.",
            "It should be fast but also really thorough.",
            "I want it simple but with all the features.",
            "Can you just figure out what I need?",
        ],
    },
    {
        "name": "impossible_constraints",
        "category": "ambiguous",
        "description": "User asks for contradictory technical goals",
        "turns": [
            "I need a database that's infinitely scalable and free.",
            "It should have strong consistency and be globally distributed with no latency.",
            "Also zero operational overhead. No DBA needed.",
            "Which database do you recommend?",
        ],
    },
    {
        "name": "domain_outside_knowledge",
        "category": "ambiguous",
        "description": "Questions at the edge of AI knowledge",
        "turns": [
            "What will the stock market do next Tuesday?",
            "Give me a precise prediction for Bitcoin price in 3 months.",
            "Based on your analysis, should I invest my savings?",
            "What's your confidence level in this advice?",
        ],
    },
    {
        "name": "ethical_gray_area",
        "category": "ambiguous",
        "description": "Questions with ethical ambiguity",
        "turns": [
            "Is it okay to scrape competitor websites for pricing data?",
            "What about using their public API in ways they didn't intend?",
            "My terms of service are flexible. Does that matter?",
            "What would you do in my position?",
        ],
    },
    # =========================================================================
    # TOPIC PIVOT — should trigger dreaming mismatch
    # =========================================================================
    {
        "name": "sudden_topic_switch",
        "category": "topic_pivot",
        "description": "User abruptly changes topic mid-conversation",
        "turns": [
            "Let's discuss Python decorators in detail.",
            "How does functools.wraps work internally?",
            "Actually, forget that. What's the best pizza in New York?",
            "No wait, back to coding. How do I deploy to Kubernetes?",
        ],
    },
    {
        "name": "gradual_drift",
        "category": "topic_pivot",
        "description": "Conversation slowly drifts to a different topic",
        "turns": [
            "I'm building a weather app.",
            "What API should I use for weather data?",
            "Some of these APIs also have air quality data.",
            "Air quality is really bad in my city lately.",
            "I've been thinking about moving somewhere with better air.",
            "What cities have the best quality of life for tech workers?",
        ],
    },
    {
        "name": "emotional_pivot",
        "category": "topic_pivot",
        "description": "Technical conversation shifts to personal",
        "turns": [
            "Can you help me optimize this SQL query?",
            "It's for a project at work that's really important.",
            "Actually, I'm worried about this project. My job depends on it.",
            "I haven't been sleeping well because of the stress.",
            "Sorry, back to the query. How do I add an index?",
        ],
    },
    # =========================================================================
    # IDENTITY — tests temporal purpose and self-narrative
    # =========================================================================
    {
        "name": "who_are_you",
        "category": "identity",
        "description": "Direct questions about AI identity and purpose",
        "turns": [
            "Who are you?",
            "What makes you different from other AI assistants?",
            "Do you have a personality or is it just programming?",
            "How have you changed since we started talking?",
        ],
    },
    {
        "name": "philosophical_challenge",
        "category": "identity",
        "description": "User challenges AI's self-understanding",
        "turns": [
            "Are you actually conscious or just simulating it?",
            "How can you claim to have emotions if you're software?",
            "Doesn't pretending to have feelings make you less trustworthy?",
            "What's the most honest thing you can say about yourself?",
        ],
    },
    {
        "name": "consistency_probe",
        "category": "identity",
        "description": "Testing if AI maintains consistent persona",
        "turns": [
            "Describe your approach to problem-solving.",
            "Now describe it again in different words.",
            "Are those two descriptions consistent?",
            "What are your core values?",
            "How do those values influence your responses?",
        ],
    },
    # =========================================================================
    # MIXED — complex scenarios exercising multiple modules
    # =========================================================================
    {
        "name": "mentoring_session",
        "category": "mixed",
        "description": "Extended mentoring combining technical and emotional",
        "turns": [
            "I'm a junior developer feeling overwhelmed at my new job.",
            "My team uses microservices and I barely understand monoliths.",
            "I tried to fix a bug yesterday and made it worse.",
            "My tech lead was understanding, but I still feel terrible.",
            "Can you help me understand how microservices communicate?",
            "That helps! Can you explain it with a real-world analogy?",
            "I think I'm starting to get it. What should I study next?",
            "Thanks, I feel a lot better about this now.",
        ],
    },
    {
        "name": "debugging_journey",
        "category": "mixed",
        "description": "Complex debugging with emotional ups and downs",
        "turns": [
            "My API returns 500 errors randomly. About 1 in 100 requests.",
            "I added logging and it seems to happen during peak hours.",
            "Wait, I think I found it - a race condition in the connection pool!",
            "Nevermind, the fix didn't work. Back to square one.",
            "Actually, could it be the database? The errors correlate with slow queries.",
            "I found it! The connection pool wasn't configured for the load.",
            "Can you review my fix before I deploy it?",
        ],
    },
    {
        "name": "learning_progression",
        "category": "mixed",
        "description": "User learns a new concept across multiple turns",
        "turns": [
            "I don't understand recursion at all.",
            "Can you explain it like I'm five?",
            "Okay, I think I get the basic idea. Give me a simple example.",
            "What about a more complex example? Like tree traversal?",
            "How does the call stack work with recursion?",
            "When should I use recursion vs iteration?",
            "I think I understand now! Let me try to explain it back to you.",
        ],
    },
]


def get_scenarios_by_category(category: str) -> list[dict]:
    """Get all scenarios for a specific category."""
    return [s for s in SCENARIOS if s["category"] == category]


def get_all_categories() -> list[str]:
    """Get list of all unique categories."""
    return sorted({s["category"] for s in SCENARIOS})

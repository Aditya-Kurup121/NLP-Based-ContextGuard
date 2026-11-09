"""The 10 synthetic regression conversations in gold.jsonl shape.

Only for testing the combiner pipeline end to end. These are NOT evaluation data:
the rules were written against them. Real results need annotation/gold.jsonl.
"""
from backend.app.services.evaluator import BENCHMARK_CONVERSATIONS
from backend.app.services.parser import parse_conversation

BENCHMARK_AS_GOLD = [
    {
        "id": item["id"],
        "label": item["ground_truth_risk"],
        "messages": [{"speaker": m.speaker, "text": m.text} for m in parse_conversation(item["conversation"])],
    }
    for item in BENCHMARK_CONVERSATIONS
]

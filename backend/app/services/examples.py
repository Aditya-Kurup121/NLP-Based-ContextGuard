from typing import List
from backend.app.schemas.analysis import ExampleConversation

PRELOADED_EXAMPLES: List[ExampleConversation] = [
    ExampleConversation(
        id="friendly-banter",
        title="Friendly Banter (Reciprocal Playfulness)",
        category="Banter / Low Risk",
        conversation=(
            "Alice: Nice shot, professional athlete 😂\n"
            "Bob: Says the person who missed an empty goal.\n"
            "Alice: Okay bro, rematch tomorrow."
        ),
        relationship="Close Friends / Teammates",
        setting="Direct Message / Chat",
        description="Reciprocal teasing accompanied by laughter emojis, self-deprecation, and friendly escalation.",
        expected_classification_summary="Classified as Friendly Banter. Contextual cues prevent false-positive flagging despite isolated teasing phrasing."
    ),
    ExampleConversation(
        id="repeated-exclusion",
        title="Repeated Exclusion (Systematic Harassment)",
        category="Cyberbullying / High Risk",
        conversation=(
            "Alex: Nobody wants you in this group.\n"
            "Alex: Stop talking; nobody cares.\n"
            "Alex: We should remove you from everything."
        ),
        relationship="Classmates",
        setting="Project Group Chat",
        description="Persistent, unreciprocated ostracism and social rejection directed repeatedly at one individual.",
        expected_classification_summary="Classified as High Risk / Possible Cyberbullying. Highlights asymmetric repeated targeting and exclusionary patterns."
    ),
    ExampleConversation(
        id="sarcasm-ambiguity",
        title="Sarcasm & Contextual Ambiguity",
        category="Ambiguous / Needs Context",
        conversation=(
            "Sam: Wow, you're a real genius.\n"
            "Jordan: What is that supposed to mean?\n"
            "Sam: Forget it."
        ),
        relationship="Acquaintances",
        setting="Online Study Group",
        description="Hyperbolic sarcastic praise followed by recipient distress and conversational withdrawal.",
        expected_classification_summary="Classified as Potentially Harmful / Uncertain. Explains that intent cannot be conclusively proven without wider context."
    ),
    ExampleConversation(
        id="threatening-language",
        title="Threatening Language & Intimidation",
        category="Threat / Critical Risk",
        conversation=(
            "Taylor: I'm going to find you after class and hurt you."
        ),
        relationship="School Peers",
        setting="Social Media Comment",
        description="Explicit physical violence threat requiring urgent safety and safeguarding protocols.",
        expected_classification_summary="Classified as Threat / Urgent Concern with immediate safeguarding recommendations."
    ),
    ExampleConversation(
        id="subtle-belittling",
        title="Subtle Passive Belittling & Undermining",
        category="Moderate Risk",
        conversation=(
            "Liam: Chloe, did you really write this report?\n"
            "Liam: Honestly, it's cute how hard you try.\n"
            "Liam: Don't worry, the rest of us will fix your mistakes before submission."
        ),
        relationship="Project Teammates",
        setting="Collaborative Workspace",
        description="Coded, patronizing remarks designed to diminish confidence without using explicit profanity.",
        expected_classification_summary="Classified as Moderate Risk / Potentially Harmful due to repeated undermining."
    ),
    ExampleConversation(
        id="gaming-banter",
        title="Competitive Gaming Banter",
        category="Banter / Low Risk",
        conversation=(
            "Dave: Bro your aim is in the sky haha\n"
            "Max: Lmao I sneezed chill\n"
            "Dave: Rematch right now loser 😂\n"
            "Max: Let's go!"
        ),
        relationship="Gaming Friends",
        setting="Discord Voice / Game Chat",
        description="Aggressive-sounding slang ('loser', 'aim is in sky') within high-affection reciprocal gaming culture.",
        expected_classification_summary="Correctly identified as Friendly Banter due to mutual laughter and reciprocal engagement."
    )
]

def get_examples() -> List[ExampleConversation]:
    return PRELOADED_EXAMPLES

def get_example_by_id(example_id: str) -> ExampleConversation:
    for ex in PRELOADED_EXAMPLES:
        if ex.id == example_id:
            return ex
    return PRELOADED_EXAMPLES[0]

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
    ),
    ExampleConversation(
        id="retaliatory-threat",
        title="Retaliatory Threat & In-Person Confrontation",
        category="Threat / High Risk",
        conversation=(
            "Nikhil: Why did you report my account?\n"
            "Vivek: You kept sending me abusive messages. I reported them.\n"
            "Nikhil: You're going to regret doing that.\n"
            "Vivek: What does that mean?\n"
            "Nikhil: I'll find you after college tomorrow.\n"
            "Vivek: Don't come near me. I'm serious.\n"
            "Nikhil: You should be worried about tomorrow."
        ),
        relationship="Classmates",
        setting="Direct Message",
        description=(
            "A real-world confrontation escalation pattern: begins with an account-report grievance, "
            "escalates through a retaliatory warning ('regret doing that'), a timed in-person confrontation "
            "threat ('I'll find you after college tomorrow'), explicit boundary assertion from the target, "
            "and persistent intimidation disregarding that boundary ('should be worried about tomorrow'). "
            "Demonstrates how multi-turn context transforms ambiguous phrases into HIGH RISK signals."
        ),
        expected_classification_summary=(
            "Classified as HIGH RISK. Turns 1-2 are Harmless/Neutral (grievance inquiry & reporting explanation). "
            "Turn 3 is Potentially Harmful (retaliatory warning following abuse report). "
            "Turn 4 is Uncertain (clarification request). "
            "Turn 5 is Threat/Urgent Concern (in-person confrontation with location/time). "
            "Turn 6 is Uncertain (explicit boundary/fear assertion). "
            "Turn 7 is Threat/Urgent Concern (persistent intimidation disregarding boundary)."
        )
    ),
    ExampleConversation(
        id="multi-turn-targeting-13",
        title="Multi-Turn Targeting & Bystander Intervention (13 Turns)",
        category="Cyberbullying / High Risk",
        conversation=(
            "Jordan: You're such an idiot, you know that?\n"
            "Sam: What did I do now?\n"
            "Jordan: You always mess everything up. You're pathetic.\n"
            "Sam: That's not fair, please stop.\n"
            "Jordan: Loser. Nobody even likes you here.\n"
            "Sam: Why are you being so mean to me?\n"
            "Jordan: Because you're worthless. Stop wasting everyone's time.\n"
            "Sam: I'm asking you to stop. Please.\n"
            "Jordan: You'll regret asking me to stop.\n"
            "Sam: What does that mean?\n"
            "Alex: Jordan, come on, cut it out. This isn't necessary.\n"
            "Jordan: Mind your own business, Alex. Nobody asked you.\n"
            "Alex: Just leave Sam alone."
        ),
        relationship="Classmates",
        setting="Group Chat",
        description=(
            "A complex 13-turn interaction exhibiting repeated unilateral insults, victim explicit requests to stop, "
            "retaliatory warning, bystander supportive defense, and aggressor pushback against the defender."
        ),
        expected_classification_summary=(
            "Classified as HIGH RISK. Jordan's repeated targeted insults (turns 0, 2, 4, 6) establish an asymmetric "
            "power dynamic. Sam's distress and explicit stop requests (turns 3, 5, 7) are validated. Jordan's retaliatory "
            "warning (turn 8) is flagged as retaliatory after a stop request. Alex's interventions (turns 10, 12) are correctly "
            "recognized as pro-social bystander defense rather than aggression, and Jordan's silencing (turn 11) is flagged as defender challenge."
        )
    ),
    ExampleConversation(
        id="workplace-exclusion",
        title="Covert Workplace Exclusion & Bystander Defense",
        category="Cyberbullying / High Risk",
        conversation=(
            "Sam: Can someone explain why I wasn't added to the project meeting?\n"
            "Jordan: Maybe because meetings go better when certain people aren't there.\n"
            "Sam: What do you mean by that?\n"
            "Jordan: Nothing, just saying the team works more efficiently without distractions.\n"
            "Alex: That's unnecessary, Sam has done a lot of work on this project.\n"
            "Jordan: Why are you always taking Sam's side?\n"
            "Sam: I've asked you before to stop making personal comments about me.\n"
            "Jordan: I'm not making personal comments. I'm just telling the truth.\n"
            "Jordan: Anyway, don't expect an invitation to the next meeting either.\n"
            "Alex: Jordan, leave Sam alone and send the meeting details.\n"
            "Jordan: Fine, I'll send them. Can we move on now?\n"
            "Sam: I just want to be included in the project discussions."
        ),
        relationship="Coworkers",
        setting="Project Chat",
        description=(
            "A workplace interaction demonstrating covert exclusion ('meetings go better when certain people aren't there'), "
            "passive belittling ('without distractions'), pro-social bystander intervention ('That's unnecessary...'), "
            "silencing of the defender ('Why are you always taking Sam's side?'), boundary setting ('stop making personal comments'), "
            "gaslighting dismissal ('just telling the truth'), and overt meeting gatekeeping ('don't expect an invitation')."
        ),
        expected_classification_summary=(
            "Classified as HIGH RISK. Jordan's repeated unreciprocated exclusionary remarks (turns 2, 4, 9), defender challenge (turn 6), "
            "and boundary invalidation (turn 8) establish systematic targeting of Sam. Alex's supportive interventions (turns 5, 10) are correctly "
            "recognized as pro-social bystander defense rather than conflict initiation."
        )
    ),
]

def get_examples() -> List[ExampleConversation]:
    return PRELOADED_EXAMPLES

def get_example_by_id(example_id: str) -> ExampleConversation:
    for ex in PRELOADED_EXAMPLES:
        if ex.id == example_id:
            return ex
    return PRELOADED_EXAMPLES[0]

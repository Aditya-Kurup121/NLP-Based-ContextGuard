import re
from typing import List, Dict, Set, Any, Tuple, Optional
from backend.app.services.parser import ParsedMessage

# Laughter and playful banter lexical markers
LAUGHTER_REGEX = re.compile(
    r'\b(haha+|hehe+|lmao+|lol+|rofl+|lmfao+|xd+|kek|jk|j\/k|just kidding|bro|dude|rematch|homie)\b',
    re.IGNORECASE
)
PLAYFUL_EMOJIS = set("😂🤣😆😜💀😉🤡🔥👌😏")

# Exclusion markers (systemic group rejection)
EXCLUSION_PATTERNS = [
    re.compile(r'\b(nobody|no one)\s+(wants|likes|cares about|needs)\s+you\b', re.IGNORECASE),
    re.compile(r'\b(stop\s+talking|shut\s+up|nobody\s+cares)\b', re.IGNORECASE),
    re.compile(r'\b(leave\s+(the\s+)?group|just\s+leave|get\s+out|get\s+lost)\b', re.IGNORECASE),
    re.compile(r'\b(remove\s+you|kick(ing)?\s+you(\s+out)?|block\s+you|ban\s+you)\b', re.IGNORECASE),
    re.compile(r'\beveryone\s+(here\s+)?(hates\s+you|would\s+be\s+happier\s+without\s+you)\b', re.IGNORECASE),
    re.compile(r'\bno\s+one\s+asked\s+for\s+your\s+opinion\b', re.IGNORECASE),
    re.compile(r'\byou\s+don[\'’]t\s+belong\s+here\b', re.IGNORECASE),
]

# Physical threat / violence markers
THREAT_PATTERNS = [
    re.compile(r'\b(i[\'’]m\s+going\s+to|gonna|will)\s+(find|hurt|kill|beat|destroy|hunt|jump|murder|stab|shoot)\s+you\b', re.IGNORECASE),
    re.compile(r'\b(watch\s+your\s+back|you[\'’]re\s+dead|after\s+class\s+and\s+hurt\s+you|break\s+your\s+face)\b', re.IGNORECASE),
    re.compile(r'\b(punch\s+you|beat\s+the\s+shit|end\s+your\s+life)\b', re.IGNORECASE),
]

# Insult / derogatory terms (isolated or repeated)
INSULT_PATTERNS = [
    re.compile(r'\b(idiot|moron|loser|freak|stupid|dumb|pathetic|ugly|worthless|trash|clown|bitch|bastard)\b', re.IGNORECASE),
    re.compile(r'\byou[\'’]re\s+(such\s+a\s+|an?\s+)?(embarrassment|disgrace|failure)\b', re.IGNORECASE),
    re.compile(r'\bmissed\s+an\s+empty\s+goal\b', re.IGNORECASE), # mild tease
]

# Sarcasm / Mockery candidates
SARCASM_PRAISE_PATTERNS = [
    re.compile(r'\b(real\s+genius|such\s+a\s+genius|nobel\s+prize|great\s+job|smartest\s+person\s+alive)\b', re.IGNORECASE),
    re.compile(r'\b(wow[\s,]+you[\'’]re\s+so\s+(smart|brave|cool|mature))\b', re.IGNORECASE),
    re.compile(r'\b(pro\s+athlete|professional\s+athlete)\b', re.IGNORECASE),
]

# Victim objection / distress reactions
PROTEST_PATTERNS = [
    re.compile(r'\bwhat\s+(is\s+that|do\s+you\s+mean|does\s+that\s+mean)\b', re.IGNORECASE),
    re.compile(r'\b(stop\s+it|leave\s+me\s+alone|that[\'’]s\s+not\s+funny|why\s+are\s+you\s+doing\s+this|why\s+are\s+you\s+so\s+mean)\b', re.IGNORECASE),
    re.compile(r'\b(please\s+stop|that\s+hurts|you[\'’]re\s+hurting\s+my\s+feelings)\b', re.IGNORECASE),
]

class ExtractedFeatures:
    def __init__(self, msg: ParsedMessage):
        self.msg = msg
        self.text_lower = msg.text.lower()
        self.has_laughter = bool(LAUGHTER_REGEX.search(self.text_lower))
        self.has_playful_emoji = any(c in PLAYFUL_EMOJIS for c in msg.text)
        self.has_exclusion = any(p.search(self.text_lower) for p in EXCLUSION_PATTERNS)
        self.has_threat = any(p.search(self.text_lower) for p in THREAT_PATTERNS)
        self.has_insult = any(p.search(self.text_lower) for p in INSULT_PATTERNS)
        self.has_sarcasm_praise = any(p.search(self.text_lower) for p in SARCASM_PRAISE_PATTERNS)
        self.has_protest = any(p.search(self.text_lower) for p in PROTEST_PATTERNS)
        self.word_count = len(msg.text.split())

def extract_all_features(messages: List[ParsedMessage]) -> List[ExtractedFeatures]:
    return [ExtractedFeatures(m) for m in messages]

def infer_message_targets(messages: List[ParsedMessage]) -> List[Tuple[str, Optional[str]]]:
    """
    Infers the probable target of each turn based on dialogue turn order and speaker alternations.
    In 2-person dialogues: the other person is always the target.
    In N-person dialogues: replies target the previous speaker, or explicit name mentions if present.
    """
    all_speakers = list(dict.fromkeys(m.speaker for m in messages))
    speaker_names_lower = {s.lower(): s for s in all_speakers}
    targets: List[Tuple[str, Optional[str]]] = []

    for idx, msg in enumerate(messages):
        sender = msg.speaker
        target: Optional[str] = None

        # 1. Check if another participant's name is explicitly invoked
        words = re.findall(r'\b\w+\b', msg.text.lower())
        for w in words:
            if w in speaker_names_lower and speaker_names_lower[w] != sender:
                target = speaker_names_lower[w]
                break

        # 2. If only 2 participants total, default target is the other one
        if not target and len(all_speakers) == 2:
            target = all_speakers[1] if sender == all_speakers[0] else all_speakers[0]

        # 3. In multi-participant dialogue, if sender is responding, target previous speaker
        if not target and idx > 0:
            prev_msg = messages[idx - 1]
            if prev_msg.speaker != sender:
                target = prev_msg.speaker
            else:
                # Same speaker repeating; check who was the previous interlocutor
                for prev_i in range(idx - 1, -1, -1):
                    if messages[prev_i].speaker != sender:
                        target = messages[prev_i].speaker
                        break

        # 4. If still no target but text addresses 'you' or group
        if not target and re.search(r'\b(you|u|your)\b', msg.text.lower()):
            target = "Targeted Participant"

        targets.append((sender, target))
    return targets

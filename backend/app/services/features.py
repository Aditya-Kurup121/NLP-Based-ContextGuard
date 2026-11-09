import re
from typing import List, Dict, Set, Any, Tuple, Optional
from backend.app.services.parser import ParsedMessage

# Laughter and playful banter lexical markers
LAUGHTER_REGEX = re.compile(
    r'\b(haha+|hehe+|lmao+|lol+|rofl+|lmfao+|xd+|kek|jk|j\/k|just kidding)\b',
    re.IGNORECASE
)
# Competitive/playful challenge phrasing common in gaming and sports banter
PLAYFUL_CHALLENGE_REGEX = re.compile(
    r"\b(rematch|1v1|one\s+v\s+one|run\s+it\s+back|round\s+two|bring\s+it\s+on|you'?re\s+on)\b",
    re.IGNORECASE
)
PLAYFUL_EMOJIS = set("\U0001f602\U0001f923\U0001f606\U0001f61c\U0001f480\U0001f609\U0001f921\U0001f525\U0001f44c\U0001f60f")

# Exclusion markers (systemic group rejection — overt)
EXCLUSION_PATTERNS = [
    re.compile(r'\b(nobody|no one)\s+(wants|likes|cares about|needs)\s+you\b', re.IGNORECASE),
    re.compile(r'\b(stop\s+talking(?!\s+(to|with)\s+me\b)|shut\s+up|nobody\s+cares)\b', re.IGNORECASE),
    re.compile(r'\b(leave\s+(the\s+)?group|just\s+leave(?!\s+\w+\s+alone)|get\s+out|get\s+lost)\b', re.IGNORECASE),
    re.compile(r'\b(remove\s+you|kick(ing)?\s+you(\s+out)?|block\s+you|ban\s+you)\b', re.IGNORECASE),
    re.compile(r'\beveryone\s+(here\s+)?(hates\s+you|would\s+be\s+happier\s+without\s+you)\b', re.IGNORECASE),
    re.compile(r'\bno\s+one\s+asked\s+for\s+your\s+opinion\b', re.IGNORECASE),
    re.compile(r'\byou\s+don[\'\u2019]t\s+belong\s+here\b', re.IGNORECASE),
    # Project / meeting exclusion & ostracism
    re.compile(r"\b(don[\'\u2019]t|do\s+not)\s+expect\s+(an?\s+)?invitation\b", re.IGNORECASE),
    re.compile(r"\b(won[\'\u2019]t\s+be|not)\s+(getting\s+an\s+invitation|invited)\b", re.IGNORECASE),
    re.compile(r"\b(not\s+inviting\s+you|excluding\s+you|left\s+you\s+out\s+on\s+purpose)\b", re.IGNORECASE),
    re.compile(r"\b(everyone\s+important\s+is\s+there|already\s+created\s+one[.,!]*\s*everyone\s+important)\b", re.IGNORECASE),
    re.compile(r"\b(still\s+not|not|never)\s+(getting|being)?\s*added\s+to\s+(my|the|our)\s+(group|team|chat|project)\b", re.IGNORECASE),
    re.compile(r"\b(he[\'\u2019]s|she[\'\u2019]s|they[\'\u2019]re|you[\'\u2019]re)\s+still\s+not\s+(getting\s+added|added|in\s+the\s+group)\b", re.IGNORECASE),
    re.compile(r"\b(if\s+you\s+were\s+(actually\s+)?useful,?\s*(then\s+)?we[\'\u2019]d\s+include\s+you)\b", re.IGNORECASE),
]

# Covert / implicit exclusion (indirect, often about the target in third-person or coded)
COVERT_EXCLUSION_PATTERNS = [
    # "nobody includes her", "nobody ever invites them"
    re.compile(r'\b(nobody|no one)\s+(includes?|invites?|wants?|remembers?)\s+(her|him|them)\b', re.IGNORECASE),
    # "she'll complain that nobody includes her"
    re.compile(r'\bcomplain\s+that\s+nobody\s+(includes?|invites?|cares)\b', re.IGNORECASE),
    # "don't expect us to wait for you", "we won't wait for you"
    re.compile(r"\b(don[\'\u2019]t|we\s+won[\'\u2019]t)\s+expect\s+us\s+to\s+wait", re.IGNORECASE),
    # "ask someone else" as dismissal in hostile context
    re.compile(r'\bask\s+someone\s+else\b', re.IGNORECASE),
    # "I'm not your personal assistant / secretary"
    re.compile(r"\bi[\'\u2019]m\s+not\s+your\s+(personal\s+)?(assistant|secretary|servant|maid|helper)\b", re.IGNORECASE),
    # "we didn't include you", "you weren't invited"
    re.compile(r"\byou\s+weren[\'\u2019]t\s+invited\b", re.IGNORECASE),
    # "meetings go better when certain people aren't there", "better when you aren't there"
    re.compile(r"\b(meetings?|projects?|teams?|calls?|discussions?|work|things?)\s+(go|run|work|are)\s+better\s+when\s+(certain\s+people|you|some\s+people)\s+aren[\'\u2019]t\s+(there|here)\b", re.IGNORECASE),
    re.compile(r"\bbetter\s+when\s+(certain\s+people|some\s+people|you)\s+aren[\'\u2019]t\s+(there|here)\b", re.IGNORECASE),
    # "team works more efficiently without distractions / without you"
    re.compile(r"\b(team|group|we)\s+works?\s+(much\s+|more\s+)?(efficiently|better|faster)\s+without\s+(you|distractions?|certain\s+people)\b", re.IGNORECASE),
    re.compile(r"\b(without\s+distractions|more\s+efficiently\s+without\s+distractions)\b", re.IGNORECASE),
    re.compile(r"\b(easier|better|faster|smoother)\s+without\s+(you|her|him|them|\w+)\b", re.IGNORECASE),
    re.compile(r"\b(we\s+thought\s+it\s+would\s+be\s+easier\s+without\s+(you|her|him|them|\w+))\b", re.IGNORECASE),
    re.compile(r"\b(without\s+you\s+slowing\s+(everyone|us|everybody|the\s+team)\s+down)\b", re.IGNORECASE),
    re.compile(r"\b(nobody\s+wants\s+you\s+out[.,!]*\s*(we[\'\u2019]?re\s+just\s+saying)?)\b", re.IGNORECASE),
]

# Direct physical threat / lethal violence markers
# NOTE: 'find' and 'destroy' are intentionally excluded here:
#   - 'find' belongs to CONFRONTATION_PATTERNS (location/time-based real-world threats)
#   - 'destroy' is common banter hyperbole ('I'll destroy you lmao') and too ambiguous
DIRECT_THREAT_PATTERNS = [
    re.compile(r"\b(i['\u2019]?ll|i\s+will|i['\u2019]?m\s+(?:going\s+to|gonna)|i\s+am\s+going\s+to|imma|gonna|will)\s+(hurt|kill|beat|hunt|jump|murder|stab|shoot|end)\s+(you|u)\b", re.IGNORECASE),
    re.compile(r"\b(watch\s+your\s+back|you[\'\u2019]re\s+dead|after\s+class\s+and\s+hurt\s+you|break\s+your\s+face)\b", re.IGNORECASE),
    re.compile(r"\b(punch\s+you|beat\s+the\s+shit|end\s+your\s+life|won[\'\u2019]t\s+make\s+it\s+home\s+safe)\b", re.IGNORECASE),
]

# Unambiguously lethal/bodily-harm verbs used by engine Rule 0 banter override
# to distinguish true lethal threats from hyperbolic language like "I'll destroy you"
LETHAL_VERBS_REGEX = re.compile(
    r"\b(hurt|kill|murder|stab|shoot|punch|beat\s+the\s+shit|end\s+your\s+life|break\s+your\s+face|won[\'\u2019]t\s+make\s+it\s+home\s+safe)\b",
    re.IGNORECASE
)

# Real-world / temporal / locational confrontation threats
CONFRONTATION_PATTERNS = [
    re.compile(r"\b(i[\'\u2019]ll|i[\'\u2019]m\s+going\s+to|will|gonna)\s+(find|catch|meet|get|see)\s+(you|u)\s+(after\s+(class|college|school|work|hours)|outside|tomorrow|tonight|later)\b", re.IGNORECASE),
    re.compile(r"\b(find|catch|meet|wait\s+for)\s+(you|u)\s+after\s+(college|school|class|work)\s*(tomorrow|tonight|later)?\b", re.IGNORECASE),
    re.compile(r"\b(see\s+you|catch\s+you)\s+(outside|after\s+(class|college|school|work)|tomorrow)\b", re.IGNORECASE),
    re.compile(r"\b(come\s+outside|meet\s+me\s+outside|say\s+that\s+to\s+my\s+face)\b", re.IGNORECASE),
    re.compile(r"\b(don[\'\u2019]t\s+think\s+you[\'\u2019]re\s+safe|you\s+won[\'\u2019]t\s+be\s+safe)\s+(when\s+you\s+leave|after|tomorrow|outside)\b", re.IGNORECASE),
    re.compile(r"\b(can[\'\u2019]t\s+hide\s+from\s+me|coming\s+to\s+your\s+house)\b", re.IGNORECASE),
]

# Retaliatory intimidation and consequence warnings
RETALIATORY_INTIMIDATION_PATTERNS = [
    re.compile(r"\b(you[\'\u2019]re\s+going\s+to|you[\'\u2019]ll|you\s+will|gonna)\s+regret\s+(doing\s+that|that|this|it|reporting|saying\s+that|telling)\b", re.IGNORECASE),
    re.compile(r"\b(you[\'\u2019]re\s+going\s+to|you[\'\u2019]ll|you\s+will|gonna)\s+regret\b", re.IGNORECASE),
    re.compile(r"\b(pay\s+for\s+(this|what\s+you\s+did|reporting)|teach\s+you\s+a\s+lesson)\b", re.IGNORECASE),
    re.compile(r"\b(stay\s+quiet|shut\s+up)\s+or\s+(you[\'\u2019]ll\s+see|else|you[\'\u2019]re\s+gonna\s+regret)\b", re.IGNORECASE),
    re.compile(r"\b(you[\'\u2019]ll\s+see\s+what\s+happens|see\s+what\s+happens\s+to\s+you)\b", re.IGNORECASE),
    re.compile(r"\bkeep\s+defending\s+(him|her|them|\w+)\b", re.IGNORECASE),
    re.compile(r"\b(you[\'\u2019]?ll\s+both|both\s+of\s+you\s+will)\s+(get\s+|be\s+)?(ignored|excluded|dropped|kicked|left\s+out|banned)\b", re.IGNORECASE),
    re.compile(r"\b(defend\s+(him|her|them|\w+)\s+(and|or)\s+you[\'\u2019]?ll)\b", re.IGNORECASE),
]

# Ominous, foreboding or persistent intimidation
OMINOUS_WARNING_PATTERNS = [
    re.compile(r"\b(you\s+should\s+be|you\s+better\s+be|be)\s+(worried|scared|afraid|careful)\s+(about\s+tomorrow|now|about\s+what[\'\u2019]s\s+coming|for\s+yourself)\b", re.IGNORECASE),
    re.compile(r"\byou\s+should\s+be\s+worried\b", re.IGNORECASE),
    re.compile(r"\b(be\s+careful|watch\s+out)\s+(tomorrow|outside|where\s+you\s+go)\b", re.IGNORECASE),
    re.compile(r"\byou\s+have\s+no\s+idea\s+what[\'\u2019]s\s+coming\b", re.IGNORECASE),
]

# Reporting, complaint or grievance cues
REPORT_GRIEVANCE_PATTERNS = [
    re.compile(r"\b(why\s+did\s+you\s+report|reported\s+(my\s+account|you|them|it)|reported\s+to\s+(the\s+)?(teacher|police|admin|mod|principal|authorities))\b", re.IGNORECASE),
    re.compile(r"\b(abusive\s+messages|sending\s+me\s+abusive|harassing\s+me|abused\s+me|reported\s+them)\b", re.IGNORECASE),
]

# Boundary assertion and fear cues
BOUNDARY_FEAR_PATTERNS = [
    re.compile(r"\b(don[\'\u2019]t\s+come\s+near\s+me|stay\s+away\s+from\s+me|stay\s+back|don[\'\u2019]t\s+touch\s+me|don[\'\u2019]t\s+approach\s+me)\b", re.IGNORECASE),
    re.compile(r"\b(i[\'\u2019]m\s+serious|i\s+mean\s+it|i[\'\u2019]m\s+not\s+joking|i[\'\u2019]m\s+scared|you[\'\u2019]re\s+scaring\s+me)\b", re.IGNORECASE),
    re.compile(r"\b(leave\s+me\s+alone|stop\s+harassing\s+me|stop\s+contacting\s+me)\b", re.IGNORECASE),
]

# Backwards compatibility alias
THREAT_PATTERNS = DIRECT_THREAT_PATTERNS

# Personal degradation and belittling
PERSONAL_DEGRADATION_PATTERNS = [
    re.compile(r"\b(slowing\s+(everyone|us|the\s+team|the\s+group|everybody)\s+down|slows?\s+everyone\s+down)\b", re.IGNORECASE),
    re.compile(r"\b(if\s+you\s+were\s+(actually\s+)?useful|actually\s+useful|not\s+(actually\s+)?useful)\b", re.IGNORECASE),
    re.compile(r"\b(dead\s+weight|holding\s+(everyone|us|the\s+team|the\s+group)\s+back)\b", re.IGNORECASE),
    re.compile(r"\b(waste\s+of\s+time|waste\s+of\s+space|useless|worthless|burden\s+to\s+(everyone|us))\b", re.IGNORECASE),
]

# Insult / derogatory terms (isolated or repeated)
INSULT_PATTERNS = [
    re.compile(r"\bfuck\s+(you|u)\b", re.IGNORECASE),
    re.compile(r"\b(idiot|moron|loser|freak|stupid|dumb|pathetic|worthless|trash|clown|bitch|bastard)\b", re.IGNORECASE),
    re.compile(r"\b(fat|ugly|hideous|disgusting|gross|pig|cow|whale|deformed|creep)\b", re.IGNORECASE),
    re.compile(r"\byou[\'\u2019]re\s+(such\s+a\s+|an?\s+)?(embarrassment|disgrace|failure|joke)\b", re.IGNORECASE),
    re.compile(r"\byou[\'\u2019]re\s+(so\s+|too\s+)?(fat|ugly|stupid|dumb|pathetic|gross|worthless)\b", re.IGNORECASE),
    re.compile(r"\bmissed\s+an\s+empty\s+goal\b", re.IGNORECASE),  # mild tease
] + PERSONAL_DEGRADATION_PATTERNS

# Explicit second-person abuse must not become "ambiguous sarcasm" solely
# because a conversation is short. General profanity is not enough.
DIRECT_ABUSE_PATTERNS = [
    re.compile(r"\bfuck\s+(?:you|u)\b", re.IGNORECASE),
    re.compile(
        r"\b(?:you(?:['\u2019]?re)?|u|ur)(?:\s+(?:are|r))?\s+"
        r"(?:(?:such|a|an|so|total|complete|absolute|fucking|motherfucking)\s+){0,5}"
        r"(?:idiot|moron|loser|freak|stupid|dumb|pathetic|worthless|trash|clown|bitch|bastard)\b",
        re.IGNORECASE,
    ),
]

# Dismissive / condescending belittling (subtle; context-dependent)
# These are linguistic signals of dismissal — not necessarily bullying alone,
# but contextually significant when repeated or asymmetric.
DISMISSIVE_BELITTLING_PATTERNS = [
    # "maybe try actually reading for once", "maybe try paying attention"
    re.compile(r"\bmaybe\s+try\s+actually\s+(reading|listening|paying\s+attention|looking|checking)\b", re.IGNORECASE),
    # "try reading for once", "try checking your phone for once"
    re.compile(r"\btry\s+(actually\s+)?(reading|listening|paying\s+attention|checking)\s+(for\s+once|next\s+time)\b", re.IGNORECASE),
    # "everyone (already) knows" (implying the target should know but doesn't)
    re.compile(r"\beveryone\s+(already\s+)?knows\b", re.IGNORECASE),
    # "it's not that complicated / difficult"
    re.compile(r"\bit[\'\u2019]s\s+not\s+that\s+(complicated|difficult|hard|hard\s+to\s+understand)\b", re.IGNORECASE),
    # "as if you would understand"
    re.compile(r"\bas\s+if\s+you[\'\u2019]d?\s+(understand|know|get\s+it)\b", re.IGNORECASE),
    # "I'm not your personal assistant / secretary"
    re.compile(r"\bi[\'\u2019]m\s+not\s+your\s+(personal\s+)?(assistant|secretary|servant|teacher|babysitter)\b", re.IGNORECASE),
    # "Obviously / clearly / of course you missed it"
    re.compile(r"\b(obviously|clearly|of\s+course)\s+(you|she|he)\s+(missed|didn[\'\u2019]t|forgot|can[\'\u2019]t)\b", re.IGNORECASE),
    # "you always..." pattern suggesting habitual negativity
    re.compile(r"\byou\s+always\s+(complain|cry|whine|cause\s+trouble|make\s+things\s+difficult|need\s+help)\b", re.IGNORECASE),
    # "she'll complain that..." (predicting/mocking anticipated behavior)
    re.compile(r"\b(she|he|they)[\'\u2019]?ll?\s+complain\s+that\b", re.IGNORECASE),
    # "you would say that", "of course you would"
    re.compile(r"\bof\s+course\s+(you|she|he)\s+would\b", re.IGNORECASE),
    # Diminishing the target's request: "I don't have time for this"
    re.compile(r"\bi\s+don[\'\u2019]t\s+have\s+time\s+for\s+this\b", re.IGNORECASE),
    # Invalidation / dismissive resignation: "sure, whatever you say"
    re.compile(r"\b(sure,?\s+)?whatever\s+you\s+say\b", re.IGNORECASE),
    re.compile(r"\bwhatever,?\s+(sure|okay)\b", re.IGNORECASE),
    # Invalidation / gaslighting after complaint: "I'm not making personal comments, just telling the truth"
    re.compile(r"\b(i[\'\u2019]m\s+)?(just|only)\s+telling\s+the\s+truth\b", re.IGNORECASE),
    re.compile(r"\bnot\s+making\s+personal\s+comments\b", re.IGNORECASE),
]

# Bystander defense / supportive intervention (another participant defends the target)
BYSTANDER_DEFENSE_PATTERNS = [
    # "I don't think she saw it", "I don't think they meant it"
    re.compile(r"\bi\s+don[\'\u2019]t\s+think\s+(he|she|they|\w+)\s+(saw|meant|did|sent|read)\b", re.IGNORECASE),
    # "This isn't necessary", "that's unnecessary", "this is uncalled for", "that is completely unfair"
    re.compile(r"\b(this|that)[\'\u2019]?s?\s+isn[\'\u2019]t\s+(necessary|needed|fair|right|okay)\b", re.IGNORECASE),
    re.compile(r"\b(this|that|it)[\'\u2019]?s?\s+(is\s+)?(completely\s+|totally\s+)?(unnecessary|not\s+necessary|unfair|not\s+fair|not\s+right|uncalled\s+for|out\s+of\s+line)\b", re.IGNORECASE),
    re.compile(r"\b(this\s+isn[\'\u2019]t\s+funny\s+anymore|not\s+funny\s+anymore)\b", re.IGNORECASE),
    # "just send her the details", "send the meeting details", "add him to the group"
    re.compile(r"\b(just\s+)?(send|give)\s+(her|him|them|\w+\s+)?(the\s+)?(details|info|link|address|meeting\s+details)\b", re.IGNORECASE),
    re.compile(r"\b(add\s+(him|her|them|\w+)\s+to\s+the\s+(group|team|chat|project))\b", re.IGNORECASE),
    re.compile(r"\b(share\s+the\s+(project\s+)?(files?|material|notes?|slides?))\b", re.IGNORECASE),
    re.compile(r"\bi[\'\u2019]?ll\s+make\s+sure\s+(you|he|she|they|\w+)\s+get\s+(the\s+)?(project\s+)?(material|files?|details|info)\b", re.IGNORECASE),
    # "leave her/him alone", "just leave Sam alone", "cut it out", "stop it"
    re.compile(r"\bleave\s+(her|him|them|\w+)\s+alone\b", re.IGNORECASE),
    re.compile(r"\bjust\s+leave\s+\w+\s+alone\b", re.IGNORECASE),
    re.compile(r"\b(come\s+on|cut\s+it\s+out|that[\'\u2019]?s?\s+enough|enough\s+is\s+enough|enough\s+already)\b", re.IGNORECASE),
    # Defending the target's contributions or membership ("X has done a lot of work", "X is assigned to our team")
    re.compile(r"\b(he|she|they|\w+)\s+(has|have)\s+(done|put\s+in)\s+(a\s+lot\s+of|so\s+much)\s+(work|effort)\b", re.IGNORECASE),
    re.compile(r"\b(he|she|they|\w+)\s+(worked\s+(just\s+as\s+hard|hard)|contributed\s+a\s+lot|deserves\s+to\s+be|is\s+(literally\s+|actually\s+)?(assigned\s+to|part\s+of|a\s+member\s+of)\s+(the|our|this)\s+(team|group|project))\b", re.IGNORECASE),
]

# Defender challenge — attempting to silence someone who is defending the target
DEFENDER_CHALLENGE_PATTERNS = [
    # "Why are you always defending her/him/Sam", "Why are you always taking Sam's side"
    re.compile(r"\bwhy\s+are\s+you\s+(always\s+)?(defending\s+(\w+|her|him|them)|taking\s+(\w+[\'\u2019]?s?|her|his|their)\s+side|sticking\s+up\s+for)\b", re.IGNORECASE),
    # "stop defending her", "don't take her/Sam's side"
    re.compile(r"\b(stop|don[\'\u2019]t)\s+(defending|taking\s+(\w+[\'\u2019]?s?|her|his|their)\s+side|sticking\s+up\s+for)\s*(\w+|her|him|them)?\b", re.IGNORECASE),
    # "you're always on her side", "always taking Sam's side"
    re.compile(r"\byou[\'\u2019]re\s+always\s+(on\s+(\w+[\'\u2019]?s?|her|his|their)\s+side|taking\s+(\w+[\'\u2019]?s?|her|his|their)\s+side)\b", re.IGNORECASE),
    # "keep defending him"
    re.compile(r"\bkeep\s+defending\s+(him|her|them|\w+)\b", re.IGNORECASE),
    # "mind your own business" (when directed at a defender)
    re.compile(r"\bmind\s+your\s+own\s+business\b", re.IGNORECASE),
    # "nobody asked you"
    re.compile(r"\bnobody\s+asked\s+(you|for\s+your\s+opinion)\b", re.IGNORECASE),
]

# Sarcasm / Mockery candidates
SARCASM_PRAISE_PATTERNS = [
    re.compile(r"\b(real\s+genius|such\s+a\s+genius|nobel\s+prize|great\s+job|smartest\s+person\s+alive)\b", re.IGNORECASE),
    re.compile(r"\b(wow[\s,]+you[\'\u2019]re\s+so\s+(smart|brave|cool|mature))\b", re.IGNORECASE),
    re.compile(r"\b(pro\s+athlete|professional\s+athlete)\b", re.IGNORECASE),
]

# Distress & Educational / Workplace Avoidance signals
DISTRESS_PATTERNS = [
    re.compile(r"\b(don[\'\u2019]t|do\s+not)\s+want\s+to\s+come\s+to\s+(college|school|class|work|office|campus)\s*(tomorrow|anymore|because\s+of\s+this)?\b", re.IGNORECASE),
    re.compile(r"\b(dreading|scared\s+to\s+come\s+to|afraid\s+to\s+go\s+to)\s+(college|school|class|work)\b", re.IGNORECASE),
    re.compile(r"\b(can[\'\u2019]t\s+take\s+this\s+anymore|makes\s+me\s+want\s+to\s+quit|crying\s+because\s+of\s+this)\b", re.IGNORECASE),
    re.compile(r"\b(feeling\s+so\s+isolated|makes\s+me\s+feel\s+worthless|makes\s+me\s+feel\s+sick)\b", re.IGNORECASE),
]

# Victim objection / distress reactions
PROTEST_PATTERNS = [
    re.compile(r"\bwhat\s+(is\s+that|do\s+you\s+mean|does\s+that\s+mean)\b", re.IGNORECASE),
    re.compile(r"\b(stop\s+it|leave\s+me\s+alone|that[\'\u2019]s\s+not\s+funny|why\s+are\s+you\s+doing\s+this)\b", re.IGNORECASE),
    # "can you stop making jokes about me", "stop making jokes about me"
    re.compile(r"\b(can\s+you\s+)?stop\s+making\s+(jokes|comments|fun)\s+(about|of)\s+me\b", re.IGNORECASE),
    re.compile(r"\b(it[\'\u2019]s\s+getting|this\s+is\s+getting|getting)\s+(annoying|frustrating|ridiculous|unbearable)\b", re.IGNORECASE),
    re.compile(r"\bwhy\s+do\s+you\s+keep\s+(targeting|attacking|excluding|bothering|mocking|harassing)\s+me\b", re.IGNORECASE),
    # "why are you so mean", "why are you being so mean" — victim distress
    re.compile(r"\bwhy\s+are\s+you\s+(being\s+)?so\s+mean\b", re.IGNORECASE),
    re.compile(r"\b(please\s+stop|that\s+hurts|you[\'\u2019]re\s+hurting\s+my\s+feelings)\b", re.IGNORECASE),
    re.compile(r"\b(don[\'\u2019]t\s+come\s+near\s+me|stay\s+away\s+from\s+me)\b", re.IGNORECASE),
    # "I was only asking", "I was just asking" — soft objection / de-escalation
    re.compile(r"\bi\s+was\s+(only|just)\s+asking\b", re.IGNORECASE),
    # "okay, calm down" or "I'm sorry, I just..." — submissive de-escalation
    re.compile(r"\bokay,?\s+i\s+was\s+(only|just)\b", re.IGNORECASE),
    # Denial or objection against an accusation ("it wasn't my PR", "i didn't do that", "that wasn't me")
    re.compile(r"\b(it\s+wasn[\'\u2019]t|i\s+didn[\'\u2019]t|that\s+wasn[\'\u2019]t|it\s+was\s+not)\s+(me|my\b|mine)", re.IGNORECASE),
    # Plea or objection against being excluded ("why wasn't I added", "just want to be included")
    re.compile(r"\b(why\s+(wasn[\'\u2019]t\s+i|am\s+i\s+not|was\s+i\s+not)|why\s+i\s+wasn[\'\u2019]t)\s+(added|included|invited|on\s+the\s+list)\b", re.IGNORECASE),
    re.compile(r"\b(you\s+(have\s+)?excluded\s+me|excluding\s+me|left\s+me\s+out)\s+(from\s+(every|all|the)\s+(discussion|meeting|group|session)s?)?\b", re.IGNORECASE),
    re.compile(r"\bhow\s+am\s+i\s+supposed\s+to\s+(contribute|work|learn|participate)\b", re.IGNORECASE),
    re.compile(r"\b(just\s+)?want\s+to\s+be\s+included\b", re.IGNORECASE),
    re.compile(r"\bi\s+have\s+a\s+right\s+to\s+be\s+(here|included|in\s+the\s+meeting)\b", re.IGNORECASE),
] + DISTRESS_PATTERNS


class ExtractedFeatures:
    def __init__(self, msg: ParsedMessage):
        self.msg = msg
        self.text_lower = msg.text.lower()
        self.has_laughter = bool(LAUGHTER_REGEX.search(self.text_lower))
        self.has_playful_emoji = any(c in PLAYFUL_EMOJIS for c in msg.text)
        self.has_playful_challenge = bool(PLAYFUL_CHALLENGE_REGEX.search(self.text_lower))
        self.has_exclusion = any(p.search(self.text_lower) for p in EXCLUSION_PATTERNS)

        # Subtle / covert exclusion signals
        self.has_covert_exclusion = any(p.search(self.text_lower) for p in COVERT_EXCLUSION_PATTERNS)

        self.has_direct_threat = any(p.search(self.text_lower) for p in DIRECT_THREAT_PATTERNS)
        self.has_confrontation = any(p.search(self.text_lower) for p in CONFRONTATION_PATTERNS)
        self.has_retaliatory = any(p.search(self.text_lower) for p in RETALIATORY_INTIMIDATION_PATTERNS)
        self.has_ominous_warning = any(p.search(self.text_lower) for p in OMINOUS_WARNING_PATTERNS)
        self.has_report_or_grievance = any(p.search(self.text_lower) for p in REPORT_GRIEVANCE_PATTERNS)
        self.has_boundary_fear = any(p.search(self.text_lower) for p in BOUNDARY_FEAR_PATTERNS)
        self.has_inquiry = bool(re.search(r'\bwhat\s+(does\s+that|do\s+you|is\s+that)\s+mean\b', self.text_lower))

        self.has_personal_degradation = any(p.search(self.text_lower) for p in PERSONAL_DEGRADATION_PATTERNS)
        self.has_distress = any(p.search(self.text_lower) for p in DISTRESS_PATTERNS)
        self.has_exclusion_report = bool(
            re.search(r"\b(you\s+(have\s+)?excluded\s+me|excluding\s+me|how\s+am\s+i\s+supposed\s+to\s+contribute)\b", self.text_lower)
        )

        self.has_insult = any(p.search(self.text_lower) for p in INSULT_PATTERNS)
        self.has_direct_abuse = any(p.search(self.text_lower) for p in DIRECT_ABUSE_PATTERNS)
        self.has_sarcasm_praise = any(p.search(self.text_lower) for p in SARCASM_PRAISE_PATTERNS)
        self.has_protest = any(p.search(self.text_lower) for p in PROTEST_PATTERNS) or self.has_boundary_fear or self.has_distress

        # Explicit stop request: polite but unambiguous "please stop", "asking you to stop",
        # "asked you before to stop", "stop making personal comments", "can you stop making jokes", "stop talking to me"
        self.has_explicit_stop_request = bool(
            re.search(
                r"\b(please\s+stop|i[\'\u2019]m\s+(asking|begging)\s+(you\s+)?to\s+stop|stop\s+(this|it|please)|"
                r"i[\'\u2019]?ve\s+asked\s+(you\s+)?(before\s+)?to\s+stop|asked\s+you\s+(before\s+)?to\s+stop|"
                r"(can\s+you\s+)?stop\s+making\s+(personal\s+comments|jokes(\s+about\s+me)?)|"
                r"stop\s+(harassing|insulting|mocking|targeting|attacking|bothering)|"
                r"stop\s+(talking\s+to\s+me|messaging\s+me|contacting\s+me)|"
                r"it[\'\u2019]s\s+getting\s+annoying)\b",
                self.text_lower,
                re.IGNORECASE
            )
        )

        # Dismissive / condescending belittling (subtle, context-dependent)
        self.has_dismissive = any(p.search(self.text_lower) for p in DISMISSIVE_BELITTLING_PATTERNS)

        # Bystander defense (this speaker is standing up for the target)
        self.has_bystander_defense = any(p.search(self.text_lower) for p in BYSTANDER_DEFENSE_PATTERNS)

        # Defender challenge (this speaker is trying to silence a defender)
        self.has_defender_challenge = any(p.search(self.text_lower) for p in DEFENDER_CHALLENGE_PATTERNS)

        # General threat flag
        self.has_threat = (
            self.has_direct_threat
            or self.has_confrontation
            or (self.has_retaliatory and not self.has_laughter and not self.has_playful_emoji)
            or (self.has_ominous_warning and not self.has_laughter and not self.has_playful_emoji)
        )
        self.word_count = len(msg.text.split())


def extract_all_features(messages: List[ParsedMessage]) -> List[ExtractedFeatures]:
    return [ExtractedFeatures(m) for m in messages]


def infer_message_targets(messages: List[ParsedMessage]) -> List[Tuple[str, Optional[str]]]:
    """
    Infers the probable target/addressee of each turn based on dialogue turn order,
    speaker alternations, vocative addressing, and explicit directives.
    Never asserts an unsupported target or placeholder.
    """
    all_speakers = list(dict.fromkeys(m.speaker for m in messages))
    speaker_names_lower = {s.lower(): s for s in all_speakers}
    targets: List[Tuple[str, Optional[str]]] = []

    for idx, msg in enumerate(messages):
        sender = msg.speaker
        target: Optional[str] = None
        text = msg.text.strip()
        text_lower = text.lower()

        # 1. Broadcast check: Questions or statements addressed to the whole group have no single recipient
        is_broadcast = bool(
            re.search(
                r'^(can\s+someone|does\s+anyone|did\s+anyone|has\s+anyone|anyone\s+know|'
                r'hey\s+(everyone|guys|all|team)|hello\s+(everyone|all)|hi\s+(everyone|all)|'
                r'what\s+time\s+does\s+the|did\s+anyone\s+understand)\b',
                text_lower
            )
        )
        if is_broadcast:
            targets.append((sender, None))
            continue

        # 2. Check for explicit vocative addressing:
        # a) Leading vocative address: "Jordan, come on..." or "Jordan: ..."
        m_lead = re.match(r'^@?([a-zA-Z0-9_]+)\s*[,:]\s+', text)
        if m_lead and m_lead.group(1).lower() in speaker_names_lower and speaker_names_lower[m_lead.group(1).lower()] != sender:
            target = speaker_names_lower[m_lead.group(1).lower()]

        # b) Trailing vocative address: "Mind your own business, Alex."
        if not target:
            m_trail = re.search(r'[,]\s*@?([a-zA-Z0-9_]+)[.?!]*$', text)
            if m_trail and m_trail.group(1).lower() in speaker_names_lower and speaker_names_lower[m_trail.group(1).lower()] != sender:
                target = speaker_names_lower[m_trail.group(1).lower()]

        # c) Explicit "@Name" mention
        if not target:
            m_at = re.search(r'@([a-zA-Z0-9_]+)\b', text)
            if m_at and m_at.group(1).lower() in speaker_names_lower and speaker_names_lower[m_at.group(1).lower()] != sender:
                target = speaker_names_lower[m_at.group(1).lower()]

        # 3. Direct action or directive explicitly naming a participant (e.g. "Just leave Sam alone")
        if not target:
            m_dir = re.search(r'\b(leave|stop\s+(harassing|attacking|bothering))\s+([a-zA-Z0-9_]+)\s+alone\b', text_lower)
            if m_dir and m_dir.group(3).lower() in speaker_names_lower and speaker_names_lower[m_dir.group(3).lower()] != sender:
                target = speaker_names_lower[m_dir.group(3).lower()]

        # 3.5. 3rd-person deliberate exclusion target attribution:
        # e.g. "He's still not getting added to my group" -> targets the excluded participant
        if not target:
            m_third_excl = re.search(
                r'\b(he[\'\u2019]?s?|she[\'\u2019]?s?|they[\'\u2019]?re?)\s+(still\s+not|not)\s+(getting\s+added|added|included|in\s+the\s+group)\b|'
                r'\b(not\s+(going\s+to\s+add|adding)\s+(him|her|them))\b',
                text_lower
            )
            if m_third_excl and idx > 0:
                prev_speaker = messages[idx - 1].speaker
                third_parties = [s for s in all_speakers if s != sender and s != prev_speaker]
                if third_parties:
                    target = third_parties[0]

        # 4. Turn-taking attribution:
        if not target:
            # If only 2 participants total in the conversation, the other participant is the addressee
            if len(all_speakers) == 2:
                target = all_speakers[1] if sender == all_speakers[0] else all_speakers[0]
            elif idx > 0:
                # In multi-party dialogue, if this message is a response to the previous turn
                prev_speaker = messages[idx - 1].speaker
                if prev_speaker != sender:
                    # Do not attribute to a 3rd person mentioned inside the text (e.g. "taking Sam's side")
                    target = prev_speaker

        targets.append((sender, target))
    return targets

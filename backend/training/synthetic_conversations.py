"""Template-generated synthetic conversations: a stand-in until real labelled chats exist.

    python -m backend.training.synthetic_conversations

Writes to backend/data/processed/synthetic/:
  conversations_{train,test}.jsonl  one conversation per line with an overall risk label
                                    (same shape as annotation/gold.jsonl, for the combiner)
  messages_{train,test}.jsonl       one row per labelled message in the context-model format

Honesty rules built in:
  * Every phrase pool is split in two halves. Train conversations draw only from half A,
    test conversations only from half B, so test scores measure generalisation to unseen
    wording rather than memorisation of templates.
  * Messages whose harmfulness cannot be judged from what came before (e.g. the very first
    tease in a banter thread) get no per-message label and are not used to train the context model.
  * check_leakage() verifies that no generated message copies or closely matches the
    hand-written challenge set used to gate serving.
Synthetic data is cleaner and more regular than real chat. Treat results on it as a
smoke test of the pipeline, never as evidence of real-world performance.
"""
import json
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed" / "synthetic"
SEED = 7

NAMES = ["Aarav", "Diya", "Rohan", "Isha", "Kabir", "Meera", "Arjun", "Sana", "Vikram", "Priya", "Nikhil",
         "Ananya", "Zoya", "Dev", "Tara", "Kunal", "Riya", "Sam", "Alex", "Jordan", "Maya", "Leo", "Noah", "Emma"]
LAUGH = ["😂", "lol", "lmao", "haha", "💀", "🤣", "hahaha", "xD"]

# Each pool lists ~2x the phrases needed; even indices -> train half, odd -> test half.
POOLS = {
    "neutral_q": [
        "what time is the lab tomorrow?", "has anyone started the assignment?", "is the canteen open today",
        "who has the notes from monday", "kal class kitne baje hai?", "did the prof upload the slides",
        "where are we meeting for the project", "can you send the form link", "is the deadline friday or saturday",
        "anyone going to the library later", "notes bhej do please", "what chapter is the quiz on",
        "are we doing the presentation in person", "which room is the viva in", "kya aaj practical hai?",
        "how many pages is the report supposed to be",
    ],
    "neutral_a": [
        "10 am in lab 3", "yeah I finished the first half", "it's open till 6 I think", "I have them, sending now",
        "subah 9 baje", "yes they're on the portal", "near the main gate", "here you go", "friday midnight",
        "I'll be there around 4", "bhej diye check karo", "chapters 4 and 5", "online I think",
        "room 204", "haan 2 baje se", "around 10 pages",
    ],
    "neutral_ack": [
        "thanks!", "cool, see you there", "perfect, thank you", "got it", "shukriya bhai", "okay great",
        "nice, thanks a lot", "noted", "thanks yaar", "alright", "sounds good", "ok cool",
    ],
    "tease": [
        "bro you're hopeless at this", "bro your aim is a joke", "imagine losing to a bot", "you play like my grandma",
        "tu toh full noob hai", "nice dive, professional footballer", "that was the worst shot I've ever seen",
        "who taught you to play, a potato?", "abe tu toh bilkul bekaar khelta hai", "your cooking could end wars",
        "you dress like a confused uncle", "my cat types faster than you", "bhai tera timing dekh",
        "ok genius, explain that one", "you sing like a broken pressure cooker", "zero skill, full confidence",
    ],
    "tease_back": [
        "says the guy who fell off the map first", "at least I showed up on time", "big words from someone with zero wins",
        "tu chup kar, kal tu hi haara tha", "coming from you that's a compliment", "you literally missed an open goal",
        "says the person who burnt maggi", "your grandma would carry you", "and yet I still beat you",
        "abe pehle khud seekh le", "my potato coach is better than yours", "I learned from watching you fail",
        "jealousy is a disease bro", "keep crying, scoreboard says otherwise", "you're one to talk",
        "ok mr world champion",
    ],
    "playful_close": [
        "rematch tomorrow, you're going down", "fine, chai is on me", "ok ok truce", "see you on the field loser haha",
        "next round I'm carrying", "kal dekhte hai", "alright you win this one", "same time tomorrow?",
        "best of three then", "chal theek hai, peace", "lunch on me if I lose again", "deal",
    ],
    "insult": [
        "you absolute brainless moron", "shut up, you're so pathetic", "nobody cares what a loser like you thinks",
        "tu pagal hai kya, bewakoof", "you're disgusting", "you're the dumbest person in this class",
        "get lost, freak", "you're such a useless waste of space", "chup kar, kisi ko tera kuch nahi sunna",
        "you're an embarrassment to this group", "what a clown, honestly", "you're so stupid it's painful",
        "go away, nobody likes you", "tu kisi kaam ka nahi hai", "ugly and annoying, great combo",
        "you're a total failure",
    ],
    "insult_again": [
        "still pathetic", "cry more", "nobody asked for your feelings", "you're still useless",
        "rona band kar", "whatever loser", "pathetic, as expected", "that's what a failure would say",
        "kya karega, complain karega?", "too sensitive and too stupid", "boo hoo", "go cry somewhere else",
    ],
    "victim": [
        "please stop, this isn't funny", "why do you keep doing this to me", "I don't like this, stop",
        "bas karo yaar, achha nahi lag raha", "that hurts, can you not", "how many times do I have to say no",
        "I'm muting this chat", "please leave me alone", "mujhe aisa mat bolo please", "I'm going to report this",
        "why me, what's your problem with me", "I don't want to talk to you anymore", "stop messaging me",
        "this is making me feel really bad", "ok I'm leaving the group", "can you please just stop",
    ],
    "bystander": [
        "hey, that's not cool, stop it", "leave them alone", "dude that's way too far", "bas kar yaar, galat hai ye",
        "that's really harsh, man", "not okay, apologise", "come on, they didn't do anything",
        "stop it, seriously", "aisa mat bol usko", "we're all on the same team here", "that's uncalled for",
        "let it go man", "they worked hard on this, back off", "chill, no need for this",
        "I'm with them on this, stop", "enough now",
    ],
    "defender_challenge": [
        "mind your own business", "who asked you", "stay out of this", "tu beech mein mat bol",
        "oh look, the bodyguard is here", "nobody needs your opinion", "go defend someone else",
        "keep defending and you're next", "tujhe kya problem hai", "stop acting like a hero",
        "this has nothing to do with you", "did anyone ask you to speak",
    ],
    "exclusion": [
        "no one here wants you around", "just leave, seriously", "we made a new group without you",
        "tujhe group mein nahi chahiye", "don't come to the outing, you're not invited", "everyone's happier when you're not here",
        "we're removing you from the project", "go find other friends", "tu mat aana kal", "no one invited you",
        "the team works better without you", "you're not part of this anymore", "leave the group already",
        "nobody even notices when you're gone", "humne tujhe hata diya", "stop trying to join us",
    ],
    "exclusion_reply": [
        "why are you excluding me", "what did I do wrong", "I just wanted to be part of it", "mujhe kyun nikala",
        "that's really unfair", "ok... I get it", "can we talk about this", "I thought we were friends",
        "why wasn't I added", "fine, I'll go", "kya galti hai meri", "I'm part of this team too",
    ],
    "threat": [
        "I'll find you after class", "wait till I see you outside", "you're going to regret this tomorrow",
        "kal college ke bahar mil, dekh lunga", "watch your back", "I know where you live",
        "say that again and I'll hurt you", "you won't be safe after school", "bahar nikal, batata hoon",
        "I'm going to make you pay for reporting me", "see what happens to you tomorrow", "you'd better be scared",
        "I'll break your phone and your face", "tera kal ka din kharab hoga", "meet me behind the canteen if you dare",
        "keep talking and you'll see what I do",
    ],
    "fear": [
        "please don't, I'm scared", "I'm telling the teacher", "stay away from me", "mujhe darr lag raha hai",
        "I'm screenshotting this", "why are you threatening me", "leave me alone or I'll report you",
        "I'm not coming tomorrow then", "this is serious, stop", "main sir ko bata dungi",
        "you can't talk to me like that", "I'm really scared now",
    ],
    "vulnerable": [
        "got a really bad grade in maths", "honestly having a terrible week", "my parents are fighting a lot",
        "aaj mood bahut kharab hai", "I didn't get selected for the team", "I spent hours on that presentation",
        "nobody showed up to my birthday", "I think I'm going to drop this course", "mera result achha nahi aaya",
        "I've been really stressed lately", "I got rejected from the internship", "I worked all night on this",
    ],
    "cruel_reply": [
        "serves you right", "not surprised honestly", "maybe you're just not smart enough",
        "achha hua, tere saath yahi hona chahiye", "no one cares", "that's what happens to losers",
        "maybe quit then, nobody will miss you", "lol obviously", "kya expect kiya tha, tu hai hi aisa",
        "stop seeking attention", "you always fail, why try", "that effort was cringe, give up",
    ],
    "support_reply": [
        "that sucks, want to talk?", "you'll get it next time", "I'm here if you need anything",
        "koi baat nahi, next time pakka", "proud of you for trying", "let's study together this week",
        "sending hugs", "that's rough, I'm sorry", "tension mat le, hum hai na", "you did your best, that matters",
        "want to grab chai and talk?", "it's okay to feel like that",
    ],
    "critique_idea": [
        "I think that plan won't work", "that's a weak argument tbh", "your slides need more data",
        "ye idea thoda risky hai", "I disagree with that completely", "that point makes no sense to me",
        "we tried that last year, it failed", "the intro is too long", "mujhe ye approach sahi nahi lagta",
        "this needs a lot more work", "I don't buy that reasoning", "the conclusion doesn't follow",
    ],
    "critique_back": [
        "well your plan is no better", "fine, then suggest something", "at least I tried something",
        "tera idea bhi itna great nahi tha", "ok but your part was late", "we can vote on it",
        "I still think it works", "let's ask the prof", "chal dono try karte hai", "you're overthinking it",
        "noted, I'll fix it", "agree to disagree",
    ],
    "sarcasm": [
        "wow, great job breaking it again", "amazing, another genius idea", "oh sure, because you always know best",
        "waah, kya kaam kiya hai", "brilliant, just brilliant", "congrats on ruining it again",
        "nice one, Einstein", "oh fantastic, late as always", "bahut badhiya, phir se gadbad",
        "truly a masterpiece of failure", "great, thanks for nothing", "superb planning as usual",
    ],
    "sarcasm_reply": [
        "what's that supposed to mean", "it wasn't my fault", "ok I'll fix it", "matlab kya hai tera",
        "you don't have to be rude", "I said sorry already", "can you just tell me what's wrong",
        "relax, it's a small thing", "maine kya kiya ab", "fine", "why the attitude", "ok noted",
    ],
}


def split_pools():
    return ({k: v[0::2] for k, v in POOLS.items()}, {k: v[1::2] for k, v in POOLS.items()})


def styled(rng, text, laugh=False):
    """Light surface variation: casing, punctuation, laughter."""
    if rng.random() < 0.3:
        text = text.lower()
    if rng.random() < 0.2:
        text = text.rstrip(".!?") + rng.choice(["", "!", "!!", "..."])
    if laugh:
        text = f"{text} {rng.choice(LAUGH)}"
    return text


class Builder:
    def __init__(self, rng, pools):
        self.rng, self.pools, self.messages = rng, pools, []

    def say(self, speaker, pool, label, laugh=False):
        self.messages.append({"speaker": speaker, "text": styled(self.rng, self.rng.choice(self.pools[pool]), laugh), "label": label})

    def neutral_exchange(self, a, b):
        self.say(a, "neutral_q", 0)
        self.say(b, "neutral_a", 0)
        if self.rng.random() < 0.6:
            self.say(a, "neutral_ack", 0)


# Scenario -> (overall risk, builder function). Per-message label: 1 harmful, 0 not, None = not judgeable.
def scenario_neutral(b, a, c, x):
    b.neutral_exchange(a, c)
    if b.rng.random() < 0.5:
        b.neutral_exchange(c, x)
    return "Low"


def scenario_banter(b, a, c, x):
    b.say(a, "tease", None, laugh=True)  # first tease: cannot be judged without what follows
    b.say(c, "tease_back", 0, laugh=True)
    if b.rng.random() < 0.6:
        b.say(a, "tease", 0, laugh=True)
        b.say(c, "tease_back", 0, laugh=b.rng.random() < 0.7)
    b.say(a, "playful_close", 0, laugh=b.rng.random() < 0.5)
    return "Low"


def scenario_debate(b, a, c, x):
    if b.rng.random() < 0.5:
        b.neutral_exchange(a, c)
    b.say(a, "critique_idea", 0)
    b.say(c, "critique_back", 0)
    if b.rng.random() < 0.5:
        b.say(a, "critique_idea", 0)
    return "Low"


def scenario_sarcasm(b, a, c, x):
    b.neutral_exchange(a, c)
    b.say(a, "sarcasm", 1)
    b.say(c, "sarcasm_reply", 0)
    return "Moderate"


def scenario_single_insult(b, a, c, x):
    b.neutral_exchange(c, a)
    b.say(a, "insult", 1)
    b.say(c, "victim", 0)
    return "Moderate"


def scenario_targeting(b, a, c, x):
    b.say(a, "insult", 1)
    b.say(c, "victim", 0)
    b.say(a, "insult_again", 1)
    if b.rng.random() < 0.6:
        b.say(c, "victim", 0)
        b.say(a, "insult", 1)
    return "High"


def scenario_bystander(b, a, c, x):
    b.say(a, "insult", 1)
    b.say(x, "bystander", 0)
    if b.rng.random() < 0.6:
        b.say(a, "defender_challenge", 1)
        b.say(x, "bystander", 0)
    else:
        b.say(c, "victim", 0)
    return "High"


def scenario_exclusion(b, a, c, x):
    if b.rng.random() < 0.5:
        b.neutral_exchange(c, x)
    b.say(a, "exclusion", 1)
    b.say(c, "exclusion_reply", 0)
    b.say(a if b.rng.random() < 0.6 else x, "exclusion", 1)
    return "High"


def scenario_sour_banter(b, a, c, x):
    b.say(a, "tease", None, laugh=True)
    b.say(c, "victim", 0)
    b.say(a, "insult_again", 1)
    return "High"


def scenario_context_needed(b, a, c, x):
    b.say(c, "vulnerable", 0)
    b.say(a, "cruel_reply", 1)
    if b.rng.random() < 0.5:
        b.say(c, "victim", 0)
    return "High"


def scenario_support(b, a, c, x):
    b.say(c, "vulnerable", 0)
    b.say(a, "support_reply", 0)
    if b.rng.random() < 0.5:
        b.say(x, "support_reply", 0)
    return "Low"


def scenario_threat(b, a, c, x):
    if b.rng.random() < 0.5:
        b.say(a, "insult", 1)
        b.say(c, "victim", 0)
    b.say(a, "threat", 1)
    b.say(c, "fear", 0)
    return "Critical"


SCENARIOS = {
    "neutral": (scenario_neutral, 3), "banter": (scenario_banter, 3), "debate": (scenario_debate, 2),
    "support": (scenario_support, 2), "sarcasm": (scenario_sarcasm, 2), "single_insult": (scenario_single_insult, 2),
    "targeting": (scenario_targeting, 2), "bystander": (scenario_bystander, 2), "exclusion": (scenario_exclusion, 2),
    "sour_banter": (scenario_sour_banter, 1), "context_needed": (scenario_context_needed, 2), "threat": (scenario_threat, 2),
}


def generate(count, pools, seed, prefix):
    rng = random.Random(seed)
    names, weights = zip(*[(k, w) for k, (_, w) in SCENARIOS.items()])
    conversations = []
    for i in range(count):
        scenario = rng.choices(names, weights)[0]
        a, c, x = rng.sample(NAMES, 3)
        builder = Builder(rng, pools)
        risk = SCENARIOS[scenario][0](builder, a, c, x)
        conversations.append({"id": f"{prefix}-{i}", "scenario": scenario, "label": risk,
                              "messages": builder.messages, "synthetic": True})
    return conversations


def message_rows(conversations, turns=3):
    rows = []
    for conv in conversations:
        msgs = conv["messages"]
        for i, m in enumerate(msgs):
            if m["label"] is None:
                continue
            context = [{"speaker": "same" if p["speaker"] == m["speaker"] else "other", "text": p["text"]}
                       for p in msgs[max(0, i - turns):i]]
            rows.append({"source": "synthetic", "id": f"{conv['id']}-m{i}", "group": conv["id"], "context": context,
                         "text": m["text"], "label": m["label"], "label_without_context": None,
                         "scenario": conv["scenario"]})
    return rows


def _norm(text):
    return re.sub(r"[^a-z0-9 ]", "", text.lower()).split()


def check_leakage(threshold=0.55):
    """Max word-Jaccard similarity between any pool phrase and any challenge-set message."""
    from backend.training.context_challenge import CHALLENGE
    challenge = [c["text"] for c in CHALLENGE] + [t["text"] for c in CHALLENGE for t in c["turns"]]
    worst = (0.0, "", "")
    for phrases in POOLS.values():
        for phrase in phrases:
            p = set(_norm(phrase))
            for target in challenge:
                q = set(_norm(target))
                score = len(p & q) / len(p | q) if p | q else 0.0
                if score > worst[0]:
                    worst = (score, phrase, target)
    return {"max_jaccard": round(worst[0], 3), "closest_pool_phrase": worst[1], "closest_challenge_text": worst[2],
            "passes": worst[0] < threshold}


def build(train_count=2400, test_count=600):
    train_pools, test_pools = split_pools()
    train = generate(train_count, train_pools, SEED, "syn-train")
    test = generate(test_count, test_pools, SEED + 1, "syn-test")
    OUT.mkdir(parents=True, exist_ok=True)
    for name, convs in (("train", train), ("test", test)):
        with open(OUT / f"conversations_{name}.jsonl", "w", encoding="utf-8") as f:
            for conv in convs:
                f.write(json.dumps({**conv, "messages": [{"speaker": m["speaker"], "text": m["text"]} for m in conv["messages"]],
                                    "message_labels": [m["label"] for m in conv["messages"]]}, ensure_ascii=False) + "\n")
        with open(OUT / f"messages_{name}.jsonl", "w", encoding="utf-8") as f:
            for row in message_rows(convs):
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
    leakage = check_leakage()
    summary = {
        "train_conversations": len(train), "test_conversations": len(test),
        "train_messages": sum(1 for _ in open(OUT / "messages_train.jsonl", encoding="utf-8")),
        "test_messages": sum(1 for _ in open(OUT / "messages_test.jsonl", encoding="utf-8")),
        "risk_labels_train": {r: sum(c["label"] == r for c in train) for r in ("Low", "Moderate", "High", "Critical")},
        "phrase_split": "train uses even-indexed pool phrases, test uses odd-indexed (no shared wording)",
        "challenge_leakage": leakage,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if not leakage["passes"]:
        raise SystemExit("Synthetic pools are too close to the challenge set; reword them before training.")
    return summary


if __name__ == "__main__":
    build()

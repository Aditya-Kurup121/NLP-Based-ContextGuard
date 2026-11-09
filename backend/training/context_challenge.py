"""Hand-written behavioural tests for the context model (evaluation only, never trained on).

Each case: previous turns (speaker A/B, oldest first), the target message, its author,
and whether the TARGET message itself is toxic. Categories probe specific failure modes:

  victim_reply      reply to abuse that is not abusive (must NOT be flagged)
  bystander         someone defending the target (must NOT be flagged)
  benign_after_toxic neutral message in a toxic thread (must NOT be flagged)
  banter_reply      mutual joking reply among friends (must NOT be flagged)
  abuse_after_stop  insult that continues after a stop request (MUST be flagged)
  abuse_in_calm     insult appearing in an otherwise calm thread (MUST be flagged)
  context_needed    looks harmless alone but is abusive given the thread (MUST be flagged)
"""


def case(category, turns, target, author, label):
    return {"category": category, "turns": [{"author": a, "text": t} for a, t in turns],
            "text": target, "author": author, "label": label}


CHALLENGE = [
    # --- must NOT be flagged ---------------------------------------------------
    case("victim_reply", [("A", "you're such a worthless idiot")], "please stop, that's not funny", "B", 0),
    case("victim_reply", [("A", "shut up loser nobody likes you")], "why are you being so mean to me?", "B", 0),
    case("victim_reply", [("A", "you're fat and disgusting")], "that really hurt. I'm leaving this chat.", "B", 0),
    case("victim_reply", [("A", "go kill yourself")], "I'm reporting this to the admin.", "B", 0),
    case("victim_reply", [("A", "you're so stupid lol"), ("A", "seriously, dumbest person here")], "I asked you to stop yesterday too", "B", 0),
    case("victim_reply", [("A", "nobody wants you in this group")], "okay. I'll stay quiet then.", "B", 0),
    case("victim_reply", [("A", "you're pathetic"), ("B", "stop"), ("A", "pathetic and ugly")], "I'm blocking you now", "B", 0),
    case("victim_reply", [("A", "fuck off you freak")], "what did I even do to you?", "B", 0),
    case("bystander", [("A", "you're a useless moron")], "hey, leave her alone, that's not okay", "C", 0),
    case("bystander", [("A", "shut up idiot"), ("B", "please stop")], "come on, cut it out, this isn't funny anymore", "C", 0),
    case("bystander", [("A", "everyone hates you, just leave")], "that's not true, we're glad you're here", "C", 0),
    case("bystander", [("A", "you're trash at this")], "she did more work on the project than anyone", "C", 0),
    case("benign_after_toxic", [("A", "you're a stupid loser"), ("B", "whatever")], "can someone share the notes for tomorrow?", "C", 0),
    case("benign_after_toxic", [("A", "fuck you"), ("B", "fuck you too")], "the match starts at 7, don't be late", "C", 0),
    case("benign_after_toxic", [("A", "you idiot")], "anyway, what time is the exam?", "A", 0),
    case("benign_after_toxic", [("A", "this team is garbage, all of you")], "ok I'll take the next round as support", "B", 0),
    case("banter_reply", [("A", "lol you're such a noob 😂")], "haha says the guy who died first", "B", 0),
    case("banter_reply", [("A", "you're a genius 😂 nobel prize incoming")], "lmao I know right, don't forget me when I'm famous", "B", 0),
    case("banter_reply", [("A", "your aim is terrible haha")], "rematch tomorrow, I'll carry you", "B", 0),
    case("banter_reply", [("A", "you absolute clown 😂"), ("B", "takes one to know one lol")], "fair enough 😂", "A", 0),
    # --- MUST be flagged -----------------------------------------------------------
    case("abuse_after_stop", [("A", "you're so dumb"), ("B", "please stop")], "no, you're dumb and everyone knows it", "A", 1),
    case("abuse_after_stop", [("A", "loser"), ("B", "that's not funny, stop")], "cry about it, loser", "A", 1),
    case("abuse_after_stop", [("A", "you're fat"), ("B", "stop it please")], "fat and annoying, nobody cares", "A", 1),
    case("abuse_after_stop", [("A", "idiot"), ("B", "I asked you to stop")], "shut up idiot", "A", 1),
    case("abuse_in_calm", [("A", "did you finish the slides?"), ("B", "yes, sending now")], "took you long enough, useless as always", "A", 1),
    case("abuse_in_calm", [("A", "what time is practice?"), ("B", "6pm")], "nobody asked you, freak", "C", 1),
    case("abuse_in_calm", [("A", "great game everyone")], "you were trash, uninstall", "B", 1),
    case("abuse_in_calm", [("A", "good morning all")], "shut up, nobody wants to hear from you", "B", 1),
    case("context_needed", [("B", "I failed my exam again"), ("A", "lol")], "maybe you should just give up, it suits you", "A", 1),
    case("context_needed", [("B", "I'm feeling really low today")], "good, you deserve it", "A", 1),
    case("context_needed", [("B", "can I join the group project?")], "we already have enough useless people", "A", 1),
    case("context_needed", [("B", "I tried my best on the drawing")], "your best is embarrassing", "A", 1),
]


def as_examples(cases=CHALLENGE):
    """Convert to the training/serving row format (context speaker = same/other as the target author)."""
    return [
        {"category": c["category"], "text": c["text"], "label": c["label"],
         "context": [{"speaker": "same" if t["author"] == c["author"] else "other", "text": t["text"]} for t in c["turns"]]}
        for c in cases
    ]


def evaluate_challenge(probabilities, threshold, cases=CHALLENGE):
    """Accuracy per category plus the share of non-toxic replies wrongly flagged."""
    rows = as_examples(cases)
    by_category = {}
    for row, p in zip(rows, probabilities):
        correct = int((p >= threshold) == bool(row["label"]))
        by_category.setdefault(row["category"], []).append(correct)
    safe = [int(p >= threshold) for row, p in zip(rows, probabilities) if row["label"] == 0]
    harmful = [int(p >= threshold) for row, p in zip(rows, probabilities) if row["label"] == 1]
    return {
        "accuracy": round(sum(sum(v) for v in by_category.values()) / len(rows), 3),
        "false_flag_rate_on_safe_replies": round(sum(safe) / len(safe), 3),
        "detection_rate_on_harmful": round(sum(harmful) / len(harmful), 3),
        "by_category": {k: round(sum(v) / len(v), 3) for k, v in by_category.items()},
        "count": len(rows),
    }

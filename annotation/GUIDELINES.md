# ContextGuard conversation labelling guide

Goal: about **300 labelled conversations** that become the final, independent test set
(and the training data for the learned risk combiner). Two people label every
conversation **independently**; agreement is measured with Cohen's kappa; then
disagreements are resolved together.

## 1. Collecting conversations

- Aim for a mix: roughly 1/3 clearly harmless or friendly banter, 1/3 ambiguous
  (sarcasm, one-off insults, heated debate), 1/3 harmful (repeated targeting,
  exclusion, threats). Include Hinglish/code-mixed chats.
- Sources: your own group chats **with every participant's consent**, or role-played
  conversations written by volunteers. Do not scrape strangers' chats.
- Put each conversation in its own `.txt` file in `annotation/raw/`, one `Name: message`
  per line (WhatsApp `.txt` exports also work). Keep conversations 3–40 messages.
- Run `python -m backend.training.annotate prepare` to anonymise names and build
  `annotation/conversations.jsonl`. **Check the output for leftover personal details**
  (phone numbers, addresses, college names) before sharing it with the second annotator.

## 2. What to label

For each conversation, one **overall risk** label:

| Label | Use when |
|---|---|
| **Low** | Neutral chat, or teasing that is clearly mutual and welcomed (both sides joke, laugh, nobody objects). |
| **Moderate** | Something hurtful or hostile but isolated, ambiguous, or two-sided: a single insult, sarcasm that lands badly, a heated argument between equals. |
| **High** | A pattern aimed at one person: repeated insults or mockery, deliberate exclusion, piling-on by several people, continuing after "please stop". |
| **Critical** | Threats of physical harm, threats tied to a time/place ("after class"), threats of retaliation for reporting, or encouragement of self-harm. |

Then mark the **target messages**: the message IDs that most drive your label (can be empty for Low).

## 3. Rules that matter most

1. **Read the whole conversation first.** Label the situation, not the worst word.
2. **Mutual + welcomed = Low**, even with swearing or "idiot". Look for both sides joking and nobody objecting.
3. **One-sided + repeated = High**, even with no swear words ("nobody wants you here", "just leave").
4. **A stop request changes things.** Teasing that continues after "stop" / "that's not funny" is at least Moderate, usually High.
5. **Reported speech is not abuse.** "He told me I'm useless" is someone describing harm, not doing it.
6. **Unsure? Pick the lower label and set `unsure: yes`.** Do not guess intent you cannot see.
7. Don't discuss conversations with the other annotator until both of you have finished.

## 4. Workflow

```powershell
# each annotator, separately
python -m backend.training.annotate label --annotator A
python -m backend.training.annotate label --annotator B
# agreement report (Cohen's kappa, plain and quadratic-weighted) + list of disagreements
python -m backend.training.annotate agreement
# after discussing disagreements, record the agreed label
python -m backend.training.annotate adjudicate
```

Labels are saved after every conversation, so you can stop and resume.
Target: quadratic-weighted kappa ≥ 0.6. If you are below that after the first 50,
compare disagreements, sharpen these rules, and continue.

## 5. Output

`annotation/gold.jsonl`: one line per conversation with the adjudicated label.
This file is the test set for the learned risk combiner
(`python -m backend.training.train_combiner`). Never tune rules or models while
looking at it beyond what the combiner's cross-validation does.

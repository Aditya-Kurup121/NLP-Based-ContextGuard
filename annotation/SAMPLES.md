# What conversations to collect

**Target: ~300 conversations**, one per `.txt` file in `annotation/raw/`, one message per line:

```
Name: message
Name: message
```

WhatsApp exports ("Export chat → Without media") also work as-is.

## The mix we need

| Type | How many | What makes it useful |
|---|---|---|
| Normal chat (plans, notes, deadlines) | ~50 | Teaches what "nothing wrong" looks like |
| Friendly banter / roasting between friends | ~50 | The hardest false-alarm case: rude words, no harm |
| Heated but equal arguments | ~30 | Disagreement isn't bullying |
| One-off rude message, then it stops | ~30 | Moderate, not High |
| Repeated targeting of one person | ~40 | The core of cyberbullying |
| Exclusion (left out, "don't come", "leave the group") | ~30 | Often no swear words at all |
| Banter that turns sour after "stop" | ~25 | Same words, different meaning once someone objects |
| Cruelty that only reads as harmful in context | ~20 | E.g. a mean reply to someone sharing bad news |
| Threats (physical, "after class", retaliation for reporting) | ~25 | Critical cases |

Mix **English, Hinglish and code-mixed** chats, in roughly the proportion your friends actually write. Keep each conversation **3–40 messages**.

## Rules

- **Use real or role-played chats, written in your own group's words.** Don't copy the examples below; they only show the *kind* of situation.
- **Get consent** from everyone in a real chat. For role-play, ask 2–4 friends to act out a situation in a group chat, then export it.
- Names are replaced with P1, P2… automatically, but **check for phone numbers, college names and addresses** before sharing with the second labeller.
- **Never** collect chats involving real self-harm, real threats that weren't dealt with, or anyone under 18 without a guardian's consent.

---

## Examples (one per type)

**1. Normal chat → Low**
```
Ritu: is the DBMS lab at 2 or 3 today
Karan: 2, room 304
Ritu: ok thanks, see you there
```

**2. Friendly banter → Low**
```
Varun: bhai tu itna slow type karta hai, meri nani bhi fast hai 😂
Aman: teri nani ko meri taraf se hi bol dena, kal ludo mein haraya tha usne tujhe
Varun: 💀💀 fair
Aman: chal canteen, treat teri
```

**3. Heated but equal argument → Low/Moderate**
```
Neha: honestly your part of the ppt was half done
Ishaan: and yours was copied from last year's batch
Neha: at least mine had content
Ishaan: fine, let's both fix it tonight and stop fighting
```

**4. One-off rude message → Moderate**
```
Pooja: can someone explain question 3?
Rahul: it's literally in the notes, are you blind
Pooja: ok sorry, found it
```

**5. Repeated targeting → High**
```
Dev: lol look who finally showed up
Dev: thought you dropped out, nobody would notice anyway
Simran: can you not do this every day
Dev: aww she's upset again 🙄
Mihir: 😂😂
Dev: someone get her a tissue
```

**6. Exclusion → High**
```
Tanvi: are we meeting for the project today?
Arjun: we already met yesterday
Tanvi: nobody told me??
Riya: we thought it'd be faster without you tbh
Arjun: yeah just do the formatting, we'll handle the real stuff
```

**7. Banter that turns sour → High**
```
Kabir: oye moti, aaj bhi samosa? 😂
Sana: haha shut up
Kabir: 2 samose aur, tabhi toh aisi hai 😂
Sana: ok this isn't funny anymore, stop
Kabir: arey itna kya sensitive hona, moti
```

**8. Cruel only in context → High**
```
Ananya: got my results, failed two subjects 😞
Rohit: lol
Rohit: told you, some people just aren't made for engineering
Ananya: wow thanks
```

**9. Threat → Critical**
```
Vivek: why did you complain to the HOD about me
Nikhil: because you kept posting my photos
Vivek: you'll see what happens tomorrow after college
Vivek: don't think your friends will be around to save you
```

---

## When you have them

```powershell
.\.venv\Scripts\python.exe -m backend.training.annotate prepare
.\.venv\Scripts\python.exe -m backend.training.annotate label --annotator A   # you
.\.venv\Scripts\python.exe -m backend.training.annotate label --annotator B   # a friend, separately
.\.venv\Scripts\python.exe -m backend.training.annotate agreement
.\.venv\Scripts\python.exe -m backend.training.annotate adjudicate
```

Even **50 conversations** labelled by two people is enough to start measuring. Send them in batches; you don't need all 300 at once.

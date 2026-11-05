"""Stateless WhatsApp text parsing, local extraction and evidence-linked reporting.

No chat files or reports are stored on the server. Summaries quote source messages;
they do not call an LLM or infer decisions that were not explicitly annotated.
"""
import hashlib
import html
import re
from collections import Counter
from datetime import datetime, timezone

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from backend.app.schemas.analysis import ContextInfo
from backend.app.services.engine import ContextGuardAnalysisEngine
from backend.app.services.parser import ParsedMessage

MAX_BYTES = 2 * 1024 * 1024
MAX_MESSAGES = 5000
WINDOW = 120
OVERLAP = 20
HARMFUL = {"Potentially Harmful", "Possible Cyberbullying", "Threat / Urgent Concern"}
RISK_ORDER = {"Low": 0, "Moderate": 1, "High": 2, "Critical": 3}
DATE = r"\d{1,4}[/.-]\d{1,2}[/.-]\d{1,4}"
TIME = r"\d{1,2}:\d{2}(?::\d{2})?(?:\s*[aApP]\.?[mM]\.?)?"
HEADERS = [
    ("ios", re.compile(rf"^\[(?P<date>{DATE}),?\s+(?P<time>{TIME})\]\s*(?P<body>.*)$")),
    ("android", re.compile(rf"^(?P<date>{DATE}),?\s+(?P<time>{TIME})\s+[-–—]\s+(?P<body>.*)$")),
]
SENDER = re.compile(r"^(?P<speaker>[^\n:]{1,100}?):\s?(?P<text>.*)$")
HEADER_LIKE = re.compile(r"^\[?\d{1,4}[/.-]\d{1,2}[/.-]\d{1,4}")
MEDIA = re.compile(r"^(?:<media omitted>|(?:image|video|audio|sticker|document|gif|contact card) omitted|.*\(file attached\))\s*$", re.IGNORECASE)
SYSTEM = re.compile(r"(?:^Messages and calls are end-to-end encrypted|^You created (?:this|the) group|.+ (?:added|removed) .+|.+ (?:changed the (?:subject|group|description)|created (?:the|this) group|left|joined using this group))", re.IGNORECASE)


def parse_timestamp(date, time, order):
    parts = re.split(r"[/.-]", date)
    if len(parts[0]) == 4:
        year, month, day = map(int, parts)
    else:
        first, second, year = map(int, parts)
        day, month = (first, second) if order == "DMY" else (second, first)
        if len(parts[2]) == 2:
            year += 2000
    normalized = re.sub(r"\s+", " ", time.replace(".", "")).strip().upper()
    for fmt in ("%I:%M:%S %p", "%I:%M %p", "%I:%M:%S%p", "%I:%M%p", "%H:%M:%S", "%H:%M"):
        try:
            clock = datetime.strptime(normalized, fmt)
            return datetime(year, month, day, clock.hour, clock.minute, clock.second).isoformat()
        except ValueError:
            continue
    raise ValueError("Invalid date/time for the selected date order")


def parse_export(text, date_order="DMY", anonymize=False):
    if not text.strip():
        raise ValueError("The export is empty. Select a WhatsApp text export without media.")
    if len(text.encode("utf-8")) > MAX_BYTES:
        raise ValueError("The text export exceeds the 2 MiB limit. Export a shorter date range.")
    if "\x00" in text or "\ufffd" in text:
        raise ValueError("The file contains invalid text. Use an uncorrupted UTF-8 or UTF-16 WhatsApp export.")
    messages, warnings, formats = [], [], Counter()
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.lstrip("\ufeff\u200e\u200f\u202a\u202c")
        match, format_name = None, None
        for name, pattern in HEADERS:
            match = pattern.match(line)
            if match:
                format_name = name
                break
        if match:
            if len(messages) >= MAX_MESSAGES:
                raise ValueError("This version supports up to 5,000 export entries. Split the export into smaller files; nothing has been analyzed yet.")
            body = match["body"]
            sender = SENDER.match(body)
            is_system = sender is None or (SYSTEM.fullmatch(body) is not None and ": " not in body)
            speaker = None if is_system else sender["speaker"].strip()
            content = body if is_system else sender["text"]
            timestamp = None
            try:
                timestamp = parse_timestamp(match["date"], match["time"], date_order)
            except ValueError:
                warnings.append({"line": number, "reason": "Invalid date/time for the selected date order; original time retained.", "excerpt": f"{match['date']}, {match['time']}"})
            messages.append({
                "id": len(messages) + 1, "speaker": speaker, "text": content,
                "timestamp": timestamp, "timestamp_raw": f"{match['date']}, {match['time']}",
                "line_start": number, "line_end": number,
                "kind": "system" if is_system else "text",
            })
            formats[format_name] += 1
        elif HEADER_LIKE.match(line):
            # Never merge a malformed export header into another person's words.
            warnings.append({"line": number, "reason": "Unrecognized timestamp header; line skipped.", "excerpt": raw[:160]})
            messages.append({"id": len(messages) + 1, "speaker": None, "text": raw, "timestamp": None, "timestamp_raw": "", "line_start": number, "line_end": number, "kind": "unparsed"})
        elif messages:
            messages[-1]["text"] += "\n" + raw
            messages[-1]["line_end"] = number
        elif raw.strip():
            warnings.append({"line": number, "reason": "Text before the first recognized WhatsApp entry; line skipped.", "excerpt": raw[:160]})
    if len(messages) > MAX_MESSAGES:
        raise ValueError("This version supports up to 5,000 export entries.")
    if not formats:
        raise ValueError("No supported WhatsApp timestamps found. Upload the original .txt export, not a screenshot, PDF, or backup.")
    for entry in messages:
        if entry["kind"] == "text":
            entry["text"] = entry["text"].strip()
            if not entry["text"]:
                entry["kind"] = "empty"
            elif MEDIA.fullmatch(entry["text"]):
                entry["kind"] = "media"
            elif len(entry["text"]) > 20000:
                raise ValueError(f"Entry {entry['id']} exceeds 20,000 characters. Split this message before import; no text has been truncated.")
    names = list(dict.fromkeys(entry["speaker"] for entry in messages if entry["speaker"]))
    if len(names) > 100:
        raise ValueError("This version supports up to 100 participants per import.")
    if anonymize:
        aliases = {name: f"Participant{i + 1:02d}" for i, name in enumerate(names)}
        pattern = re.compile(r"(?<!\w)(?:" + "|".join(re.escape(name) for name in sorted(names, key=len, reverse=True)) + r")(?!\w)") if names else None
        def redact(value):
            if pattern:
                value = pattern.sub(lambda match: aliases[match[0]], value)
            value = re.sub(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b", "[email]", value)
            return re.sub(r"(?<!\w)\+?\d[\d ()-]{7,}\d(?!\w)", "[phone]", value)
        for entry in messages:
            entry["speaker"] = aliases.get(entry["speaker"])
            entry["text"] = redact(entry["text"])
        for warning in warnings:
            warning["excerpt"] = redact(warning["excerpt"])
    dates = [entry["timestamp"] for entry in messages if entry["timestamp"]]
    out_of_order = sum(a > b for a, b in zip(dates, dates[1:]))
    notices = ["Dates use the selected order; timestamps have no timezone in the export. Source order is preserved."]
    if out_of_order:
        notices.append(f"{out_of_order} timestamp reversal(s) detected. Check the date order or whether the export was edited.")
    if anonymize:
        notices.append("Participant labels, matching mentions, emails and phone-like strings are masked. Other identifying details may remain; inspect before sharing.")
    return {
        "messages": messages, "participants": list(dict.fromkeys(entry["speaker"] for entry in messages if entry["speaker"])),
        "counts": dict(Counter(entry["kind"] for entry in messages)),
        "total_entries": len(messages), "formats": dict(formats), "date_order": date_order,
        "date_start": min(dates) if dates else None, "date_end": max(dates) if dates else None,
        "warnings": warnings[:100], "warning_count": len(warnings), "notices": notices,
        "anonymized": anonymize, "source_sha256": hashlib.sha256(text.encode()).hexdigest(),
    }


def topic_summary(entries):
    """TF-IDF keywords and representative source excerpts, never generated claims."""
    if not entries:
        return {"keywords": [], "excerpts": [], "method": "Local extractive TF-IDF summary"}
    try:
        vectorizer = TfidfVectorizer(stop_words="english", max_features=10000, ngram_range=(1, 2), min_df=1)
        matrix = vectorizer.fit_transform([entry["text"] for entry in entries])
        mean = np.asarray(matrix.mean(axis=0)).ravel()
        terms = vectorizer.get_feature_names_out()
        keywords = [str(terms[i]) for i in mean.argsort()[::-1][:8] if mean[i] > 0]
        similarities = np.asarray(matrix @ mean).ravel()
        ranked = sorted(range(len(entries)), key=lambda i: (-similarities[i], i))
        chosen, seen = [], set()
        for index in ranked:
            canonical = entries[index]["text"].casefold().strip()
            if canonical not in seen:
                chosen.append(index)
                seen.add(canonical)
            if len(chosen) == min(4, len(entries)):
                break
        excerpts = [entries[i] for i in sorted(chosen)]
    except ValueError:  # Emoji-only or stopword-only conversations still import.
        keywords, excerpts = [], entries[:3]
    return {"keywords": keywords, "excerpts": [{"message_id": row["id"], "speaker": row["speaker"], "timestamp_raw": row["timestamp_raw"], "text": row["text"][:600], "excerpt_truncated": len(row["text"]) > 600} for row in excerpts], "method": "Local extractive TF-IDF summary; keywords and quotations, not inferred decisions or intent"}


def chapter_groups(entries):
    groups = []
    for entry in entries:
        new_group = not groups or len(groups[-1]) >= 100
        if groups and entry["timestamp"] and groups[-1][-1]["timestamp"]:
            current, previous = datetime.fromisoformat(entry["timestamp"]), datetime.fromisoformat(groups[-1][-1]["timestamp"])
            new_group |= current.date() != previous.date() or (current - previous).total_seconds() >= 3600
        if new_group:
            groups.append([])
        groups[-1].append(entry)
    return groups


def analyze_export(parsed, relationship="Unspecified"):
    entries = [row for row in parsed["messages"] if row["kind"] == "text"]
    if not entries:
        raise ValueError("No text messages are available for analysis. System events, attachment-only entries and malformed entries are excluded.")
    engine = ContextGuardAnalysisEngine()
    analyzed, windows = [], []
    for start in range(0, len(entries), WINDOW):
        low, high = max(0, start - OVERLAP), min(len(entries), start + WINDOW + OVERLAP)
        subset = entries[low:high]
        result = engine.analyze_messages(
            [ParsedMessage(row["id"], row["speaker"], row["text"], "") for row in subset],
            ContextInfo(relationship=relationship, setting="WhatsApp export"),
        )
        # Context messages are inspected but counted only in their owning window.
        first, last = entries[start]["id"], entries[min(len(entries), start + WINDOW) - 1]["id"]
        analyzed.extend(message.model_dump() for message in result.messages if first <= message.id <= last)
        windows.append({"first_message_id": subset[0]["id"], "last_message_id": subset[-1]["id"], "risk": result.overall_risk, "score": result.risk_score, "summary": result.conversation_summary})
    peak = max(windows, key=lambda window: (RISK_ORDER[window["risk"]], window["score"]))
    by_id = {row["id"]: row for row in parsed["messages"]}
    flagged = [row for row in analyzed if row["classification"] in HARMFUL]
    ranges = []
    for message in flagged:
        low, high = max(1, message["id"] - 2), min(len(parsed["messages"]), message["id"] + 2)
        if ranges and low <= ranges[-1][1] + 1:
            ranges[-1][1] = high
        else:
            ranges.append([low, high])
    lookup = {row["id"]: row for row in analyzed}
    episodes = []
    for index, (low, high) in enumerate(ranges, 1):
        context = [{**by_id[i], "analysis": lookup.get(i)} for i in range(low, high + 1)]
        concerns = [row for row in context if row["analysis"] and row["analysis"]["classification"] in HARMFUL]
        episodes.append({"id": index, "first_message_id": low, "last_message_id": high, "flagged_message_ids": [row["id"] for row in concerns], "has_threat": any(row["analysis"]["classification"] == "Threat / Urgent Concern" for row in concerns), "messages": context})
    counts = Counter(row["classification"] for row in analyzed)
    summary = topic_summary(entries)
    chapters = []
    for index, group in enumerate(chapter_groups(entries), 1):
        chapters.append({"id": index, "first_message_id": group[0]["id"], "last_message_id": group[-1]["id"], "start": group[0]["timestamp_raw"], "end": group[-1]["timestamp_raw"], "message_count": len(group), "flagged_count": sum(lookup[row["id"]]["classification"] in HARMFUL for row in group), "summary": topic_summary(group)})
    text_counts = Counter(row["speaker"] for row in entries)
    flagged_counts = Counter(row["speaker"] for row in flagged)
    participants = [{"name": name, "message_count": count, "flagged_count": flagged_counts[name]} for name, count in text_counts.items()]
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(), "import": parsed,
        "overview": {"text_message_count": len(entries), "excluded_entries": len(parsed["messages"]) - len(entries), "participant_count": len(participants), "participants": participants, "summary": summary,
            "narrative": f"The export contains {len(entries)} text messages from {len(participants)} participants. " + ("Frequent discussion terms include " + ", ".join(summary["keywords"][:5]) + ". " if summary["keywords"] else "No stable discussion keywords were extracted. ") + f"{len(flagged)} messages were flagged for closer review; {counts['Threat / Urgent Concern']} contain threat cues. This overview quotes the available text and does not infer decisions or verify allegations."},
        "risk": {"level": peak["risk"], "index": peak["score"], "flagged_count": len(flagged), "threat_count": counts["Threat / Urgent Concern"], "uncertain_count": counts["Uncertain — More Context Needed"], "classification_counts": dict(counts), "window_count": len(windows), "peak_window": peak,
            "method": "Highest concern window, then its rule-based index. Each window reviews up to 120 new text messages plus 20 preceding and 20 following messages. Overlap is counted once in message totals. A serious incident is never averaged away by a longer neutral history. The index is not a probability or a percentage of abusive messages."},
        "chapters": chapters, "episodes": episodes, "analysis": analyzed,
        "limitations": [
            "Only text in this exported file is reviewed; missing/deleted messages, attachments and voice tone are unavailable.",
            "System events, attachment-only messages and unparsed entries are excluded from NLP analysis and counted separately.",
            "Risk uses existing English conversational rules. Sarcasm, indirect threats, quoted/reported speech and recipient inference can be wrong.",
            "Discussion summaries are local keyword/excerpt extraction, not an LLM narrative or verified record of decisions.",
            "Conversation context beyond the overlapping windows is not modeled. Chapters are time/size-based sessions, not learned topic boundaries.",
            "Participant flag counts describe messages, not guilt or intent. This report is for human review, not automatic sanctions.",
            "Text is processed in memory on the configured backend. No chat/report database or automatic external model call is used.",
        ],
    }
    report["exports"] = render_report(report)
    return report


def render_report(report):
    """Export exactly the reviewed report; escape all imported HTML and attributes."""
    def quote_markdown(value):
        return '\n'.join('> ' + html.escape(line, quote=False) for line in str(value).splitlines())
    overview, risk, imported = report["overview"], report["risk"], report["import"]
    lines = ["# ContextGuard conversation report", "", f"Generated (UTC): {report['created_at']}", f"Source text SHA256: {imported['source_sha256']}", f"Participant masking: {'enabled' if imported['anonymized'] else 'disabled'}", "", "## Overview", overview["narrative"], f"Date range: {imported['date_start'] or 'unknown'} — {imported['date_end'] or 'unknown'} (export local time)", f"Analyzed: {overview['text_message_count']} | Excluded entries: {overview['excluded_entries']} | Parsing warnings: {imported['warning_count']}", "", "## Risk assessment", f"{risk['level']} — {risk['index']}/100 (heuristic index, not a probability)", risk["method"], f"Peak window: messages #{risk['peak_window']['first_message_id']}–#{risk['peak_window']['last_message_id']}", "", "## Participants"]
    for person in overview["participants"]:
        lines.append(f"- {person['name']}: {person['message_count']} text messages; {person['flagged_count']} flagged")
    lines.extend(["", "## Discussion sessions", "Sessions split at date changes, gaps of 60 minutes, or 100 text messages."])
    for chapter in report["chapters"]:
        lines.extend(["", f"### Session {chapter['id']}: {chapter['start']} — {chapter['end']}", f"{chapter['message_count']} messages; {chapter['flagged_count']} flagged", "Keywords: " + ", ".join(chapter["summary"]["keywords"])])
        for excerpt in chapter["summary"]["excerpts"]:
            lines.append(f"Message #{excerpt['message_id']} | {html.escape(excerpt['speaker'])}")
            lines.append(quote_markdown(excerpt['text']) + ("\n> [excerpt shortened]" if excerpt["excerpt_truncated"] else ""))
    lines.extend(["", "## Evidence with surrounding replies"])
    if not report["episodes"]:
        lines.append("No messages matched the current harmful/threat categories. This does not establish that the conversation is safe.")
    for episode in report["episodes"]:
        lines.extend(["", f"### Episode {episode['id']}: messages #{episode['first_message_id']}–#{episode['last_message_id']}"])
        for row in episode["messages"]:
            analysis = row["analysis"]
            lines.append(f"Message #{row['id']} | {row['timestamp_raw']} | {row['speaker'] or 'System'} | source lines {row['line_start']}–{row['line_end']}")
            lines.append(quote_markdown(row["text"]))
            if analysis:
                lines.append(f"Assessment: {analysis['classification']}; inferred target: {analysis['target'] or 'not established'}")
                lines.extend(f"  Evidence: {item}" for item in analysis["contextual_evidence"])
                lines.append("Suggested action: " + analysis["suggested_action"])
    lines.extend(["", "## Parsing notices", *imported["notices"]])
    lines.extend(f"Line {warning['line']}: {warning['reason']} — {warning['excerpt']}" for warning in imported["warnings"])
    if imported["warning_count"] > len(imported["warnings"]):
        lines.append("Only the first 100 parsing warnings are listed.")
    lines.extend(["", "## Limitations", *["- " + item for item in report["limitations"]]])
    markdown = "\n\n".join(lines)
    e = lambda value: html.escape(str(value))
    body = [
        '<header><p class="eyebrow">CONTEXTGUARD / CONVERSATION REVIEW</p><h1>A conversation, in context.</h1><p class="muted">Local extraction and source-linked evidence for human review.</p></header>',
        f'<div class="risk"><div><span class="eyebrow">HIGHEST CONCERN</span><h2>{e(risk["level"])} concern</h2></div><div><strong>{e(risk["index"])}</strong> / 100<p class="muted">Heuristic index, not a probability</p></div></div>',
        '<section><h2>Conversation overview</h2>',
        f'<p>{e(overview["narrative"])}</p><p class="muted">{e(imported["date_start"] or "Unknown start")} → {e(imported["date_end"] or "Unknown end")} · export local time</p>',
        f'<p>{overview["text_message_count"]} text messages analyzed · {overview["excluded_entries"]} entries excluded · {imported["warning_count"]} parsing warnings · participant masking {"on" if imported["anonymized"] else "off"}</p>',
        '<h3>Frequent discussion terms</h3><p>' + e(', '.join(overview["summary"]["keywords"]) or 'No stable keywords extracted.') + '</p></section>',
        '<section><h2>Participant activity</h2><table><thead><tr><th>Participant</th><th>Text messages</th><th>Flagged</th></tr></thead><tbody>',
    ]
    body.extend(f'<tr><td>{e(person["name"])}</td><td>{person["message_count"]}</td><td>{person["flagged_count"]}</td></tr>' for person in overview["participants"])
    body.extend(['</tbody></table><p class="muted">Counts describe messages, not guilt or intent.</p></section>', '<section><h2>Discussion sessions</h2><p class="muted">Time/size-based sessions: date changes, gaps of 60 minutes, or 100 text messages. Not learned topic boundaries.</p>'])
    for chapter in report["chapters"]:
        body.append(f'<article><h3>Session {chapter["id"]}: {e(chapter["start"])} → {e(chapter["end"])}</h3><p>{chapter["message_count"]} messages · {chapter["flagged_count"]} flagged</p><p>Keywords: {e(", ".join(chapter["summary"]["keywords"]))}</p>')
        for excerpt in chapter["summary"]["excerpts"]:
            body.append(f'<blockquote><p class="muted">Message #{excerpt["message_id"]} · {e(excerpt["speaker"])} · {e(excerpt["timestamp_raw"])}</p><p class="quote">{e(excerpt["text"])}{" [excerpt shortened]" if excerpt["excerpt_truncated"] else ""}</p></blockquote>')
        body.append('</article>')
    body.extend(['</section><section><h2>How the index was calculated</h2>', f'<p>{e(risk["method"])}</p><p>{risk["window_count"]} windows reviewed. Peak window: messages #{risk["peak_window"]["first_message_id"]}–#{risk["peak_window"]["last_message_id"]}.</p>', f'<p>{e(risk["peak_window"]["summary"])}</p></section>', '<section><h2>Evidence and surrounding replies</h2>'])
    if not report["episodes"]:
        body.append('<p>No messages matched the current concern categories. This does not establish that the conversation is safe.</p>')
    for episode in report["episodes"]:
        body.append(f'<article><h3>Episode {episode["id"]}: messages #{episode["first_message_id"]}–#{episode["last_message_id"]}</h3>')
        for row in episode["messages"]:
            analysis = row["analysis"]
            body.append(f'<blockquote><p class="muted">Message #{row["id"]} · {e(row["speaker"] or "System")} · {e(row["timestamp_raw"])} · source lines {row["line_start"]}–{row["line_end"]}</p><p class="quote">{e(row["text"])}</p>')
            if analysis:
                body.append(f'<p><strong>{e(analysis["classification"])}</strong> · inferred recipient: {e(analysis["target"] or "not established")}</p><ul>')
                body.extend(f'<li>{e(item)}</li>' for item in analysis["contextual_evidence"])
                body.append(f'</ul><p>Suggested action: {e(analysis["suggested_action"])}</p>')
            body.append('</blockquote>')
        body.append('</article>')
    body.append('</section><section><h2>Parsing notices</h2>')
    body.extend(f'<p>{e(notice)}</p>' for notice in imported["notices"])
    body.extend(f'<p>Line {warning["line"]}: {e(warning["reason"])} — {e(warning["excerpt"])}</p>' for warning in imported["warnings"])
    body.append('</section><section><h2>Limitations</h2><ul>')
    body.extend(f'<li>{e(item)}</li>' for item in report["limitations"])
    body.append(f'</ul></section><footer><p>Generated (UTC): {e(report["created_at"])}</p><p class="hash">Source text SHA256: {e(imported["source_sha256"])}</p><p>Use your browser’s Print → Save as PDF to save this report as a PDF.</p></footer>')
    html_report = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>ContextGuard conversation report</title><style>body{max-width:900px;margin:40px auto;padding:0 28px;color:#263b33;background:#fffefa;font:14px/1.8 system-ui}h1{font:42px/1.2 Georgia,serif;letter-spacing:-1px}h2{font:28px/1.3 Georgia,serif}h3{font-size:15px}header,section,footer{padding:22px 0;border-bottom:1px solid #dce1d5}.eyebrow{font-size:10px;letter-spacing:1.6px;color:#65785d}.risk{display:flex;justify-content:space-between;gap:24px;align-items:center;background:#f2ecdf;padding:24px;margin-top:24px;border-radius:7px}.risk strong{font:48px Georgia,serif}.muted{color:#68766d;font-size:11px}.quote{white-space:pre-wrap;overflow-wrap:anywhere}blockquote{border-left:2px solid #b6c3a4;background:#f8faf4;padding:12px 20px;margin:16px 0;overflow-wrap:anywhere}table{border-collapse:collapse;width:100%;text-align:left}th,td{padding:10px;border-bottom:1px solid #dce1d5}article{margin:25px 0}.hash{font:10px Consolas,monospace;overflow-wrap:anywhere}@media print{body{margin:0;max-width:none;font-size:11px}h1{font-size:30px}h2{font-size:23px}header,section{padding:14px 0}blockquote{break-inside:avoid}th{background:#eee}}@media(max-width:500px){body{padding:0 18px}.risk{align-items:flex-start;flex-direction:column}h1{font-size:34px}}</style></head><body>' + ''.join(body) + '</body></html>'
    return {"markdown": markdown, "html": html_report}


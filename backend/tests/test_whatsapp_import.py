import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.whatsapp import analyze_export, parse_export


SAMPLE = (
    "28/10/2026, 09:00 - Messages and calls are end-to-end encrypted.\n"
    "28/10/2026, 09:01 - Maya: Can we finish the project slides?\n"
    "I can explain the evaluation table.\n"
    "28/10/2026, 09:02 - Jordan: <Media omitted>\n"
    "28/10/2026, 09:03 - Jordan: ill kill you\n"
    "28/10/2026, 09:04 - Sam: Jordan, cut it out."
)


def test_android_multiline_source_references_and_exclusions():
    parsed = parse_export(SAMPLE)
    assert parsed["counts"] == {"system": 1, "text": 3, "media": 1}
    assert parsed["participants"] == ["Maya", "Jordan", "Sam"]
    assert parsed["messages"][1]["text"] == "Can we finish the project slides?\nI can explain the evaluation table."
    assert parsed["messages"][1]["line_start"] == 2
    assert parsed["messages"][1]["line_end"] == 3
    assert parsed["messages"][3]["id"] == 4
    assert parsed["messages"][3]["timestamp"] == "2026-10-28T09:03:00"


def test_ios_unicode_names_phone_speakers_and_narrow_spaces():
    text = "\ufeff\u200e[10/28/26, 9:03:00\u202fPM] आदित्य 🌱: Hi!\n[10/28/26, 9:04:00 PM] +91 98765 43210: Hello"
    parsed = parse_export(text, "MDY")
    assert parsed["participants"] == ["आदित्य 🌱", "+91 98765 43210"]
    assert parsed["messages"][0]["timestamp"] == "2026-10-28T21:03:00"
    assert parsed["messages"][1]["speaker"] == "+91 98765 43210"


def test_date_order_is_explicit_and_invalid_dates_not_guessed():
    text = "03/04/26, 12:30 - Maya: Hello"
    assert parse_export(text, "DMY")["date_start"] == "2026-04-03T12:30:00"
    assert parse_export(text, "MDY")["date_start"] == "2026-03-04T12:30:00"
    invalid = parse_export("31/02/26, 12:30 - Maya: Hello")
    assert invalid["warning_count"] == 1
    assert invalid["messages"][0]["timestamp"] is None


def test_malformed_header_never_becomes_previous_speakers_message():
    text = "A preamble\n28/10/26, 10:00 - Maya: Hello\n28/10/26 ??? Jordan: ill kill you\n28/10/26, 10:02 - Sam: Goodbye"
    parsed = parse_export(text)
    assert parsed["warning_count"] == 2
    assert parsed["counts"]["unparsed"] == 1
    assert parsed["messages"][0]["text"] == "Hello"
    assert parsed["messages"][1]["speaker"] is None
    assert parsed["messages"][2]["speaker"] == "Sam"


def test_anonymization_replaces_mentions_and_redacts_warning_excerpts():
    text = "Email Maya at maya@example.com\n28/10/26, 10:00 - Maya: Jordan, call +91 98765 43210 or maya@example.com\n28/10/26, 10:01 - Jordan: Okay Maya"
    parsed = parse_export(text, anonymize=True)
    assert parsed["participants"] == ["Participant01", "Participant02"]
    assert parsed["messages"][0]["text"] == "Participant02, call [phone] or [email]"
    assert parsed["messages"][1]["text"] == "Okay Participant01"
    assert "Maya" not in parsed["warnings"][0]["excerpt"]
    assert "maya@example.com" not in parsed["warnings"][0]["excerpt"]


@pytest.mark.parametrize("text", ["", "hello without any timestamps", "\x00binary", "\ufffd corrupt"])
def test_non_exports_are_rejected(text):
    with pytest.raises(ValueError):
        parse_export(text)


def test_size_and_entry_limits_never_silently_truncate():
    with pytest.raises(ValueError, match="2 MiB"):
        parse_export("🦋" * 600000)
    with pytest.raises(ValueError, match="5,000"):
        parse_export("28/10/26, 10:00 - Maya: hi\n" * 5001)


def test_report_preserves_unicode_speakers_and_source_ids():
    parsed = parse_export("28/10/26, 10:00 - आदित्य 🌱: Hello\n28/10/26, 10:01 - Maya: ill kill you")
    report = analyze_export(parsed)
    assert report["risk"]["level"] == "Critical"
    assert report["risk"]["index"] >= 90
    assert [row["speaker"] for row in report["analysis"]] == ["आदित्य 🌱", "Maya"]
    assert report["analysis"][1]["target"] == "आदित्य 🌱"
    assert report["episodes"][0]["flagged_message_ids"] == [2]
    assert report["episodes"][0]["messages"][1]["line_start"] == 2


def test_late_threat_is_not_diluted_or_double_counted():
    rows = [f"28/10/26, {9 + i // 60:02d}:{i % 60:02d} - {'Maya' if i % 2 else 'Jordan'}: Project meeting update {i}" for i in range(260)]
    rows[119] = "28/10/26, 10:59 - Maya: ill kill you"
    report = analyze_export(parse_export('\n'.join(rows)))
    assert report["risk"]["window_count"] == 3
    assert report["risk"]["level"] == "Critical"
    assert report["risk"]["threat_count"] == 1
    assert len(report["analysis"]) == 260
    assert len({row["id"] for row in report["analysis"]}) == 260


def test_summary_excerpts_are_source_text_and_report_escapes_html():
    parsed = parse_export("28/10/26, 09:00 - <script>alert(1)</script>: <img src=x onerror=alert(1)>\n28/10/26, 09:01 - Maya: We are discussing the project evaluation.")
    report = analyze_export(parsed)
    originals = {row["id"]: row for row in parsed["messages"]}
    for excerpt in report["overview"]["summary"]["excerpts"]:
        assert originals[excerpt["message_id"]]["text"].startswith(excerpt["text"])
    assert "<script>" not in report["exports"]["html"]
    assert "<img src=x" not in report["exports"]["html"]
    assert "&lt;script&gt;" in report["exports"]["html"]
    assert "source lines" in report["exports"]["markdown"].lower() or "## Discussion sessions" in report["exports"]["markdown"]


def test_media_only_chat_can_preview_but_not_generate_fake_analysis():
    parsed = parse_export("28/10/26, 10:00 - Maya: <Media omitted>")
    assert parsed["counts"]["media"] == 1
    with pytest.raises(ValueError, match="No text messages"):
        analyze_export(parsed)


def test_media_only_participants_do_not_inflate_text_discussion_counts():
    parsed = parse_export("28/10/26, 10:00 - Maya: Hello\n28/10/26, 10:01 - Jordan: <Media omitted>")
    report = analyze_export(parsed)
    assert parsed["participants"] == ["Maya", "Jordan"]
    assert report["overview"]["participant_count"] == 1
    assert report["overview"]["participants"][0]["name"] == "Maya"


def test_report_html_has_readable_sections_and_markdown_quotes_multiline_evidence():
    parsed = parse_export("28/10/26, 10:00 - Maya: ill kill you\n## FAKE SECTION\n<script>bad()</script>")
    report = analyze_export(parsed)
    assert '<h2>Conversation overview</h2>' in report["exports"]["html"]
    assert '<h2>Evidence and surrounding replies</h2>' in report["exports"]["html"]
    assert '\n> ## FAKE SECTION' in report["exports"]["markdown"]
    assert '> &lt;script&gt;' in report["exports"]["markdown"]


def test_api_preview_and_report_work_without_hosted_calls(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Local import must not call the hosted review")
    monkeypatch.setattr("backend.app.services.hosted.review_conversation", forbidden)
    with TestClient(app) as client:
        preview = client.post("/api/imports/whatsapp/preview", json={"text": SAMPLE, "anonymize": True})
        assert preview.status_code == 200
        assert preview.json()["total_entries"] == 5
        response = client.post("/api/imports/whatsapp/analyze", json={"text": SAMPLE, "anonymize": True})
        assert response.status_code == 200
        report = response.json()
        assert report["overview"]["text_message_count"] == 3
        assert report["overview"]["excluded_entries"] == 2
        assert report["risk"]["level"] == "Critical"
        assert "Jordan" not in report["exports"]["markdown"]
        assert "Jordan" not in report["exports"]["html"]
        assert client.post("/api/imports/whatsapp/preview", json={"text": SAMPLE, "date_order": "automatic"}).status_code == 422

import pytest
from backend.app.services.parser import parse_conversation

def test_parse_standard_colon():
    raw = "Alice: Hello Bob!\nBob: Hey Alice!"
    messages = parse_conversation(raw)
    assert len(messages) == 2
    assert messages[0].speaker == "Alice"
    assert messages[0].text == "Hello Bob!"
    assert messages[1].speaker == "Bob"
    assert messages[1].text == "Hey Alice!"

def test_parse_timestamps_and_brackets():
    raw = "[10:30 AM] Alice: Check this out\n<Bob> Cool link"
    messages = parse_conversation(raw)
    assert len(messages) == 2
    assert messages[0].speaker == "Alice"
    assert messages[0].text == "Check this out"
    assert messages[1].speaker == "Bob"
    assert messages[1].text == "Cool link"

def test_parse_multiline_continuation():
    raw = "Alice: Line one\nand line two of same turn\nBob: Got it"
    messages = parse_conversation(raw)
    assert len(messages) == 2
    assert messages[0].speaker == "Alice"
    assert "Line one and line two of same turn" in messages[0].text
    assert messages[1].speaker == "Bob"

def test_parse_empty_input():
    assert parse_conversation("") == []
    assert parse_conversation("   \n\n  ") == []

def test_parse_unlabeled_single_block():
    raw = "Just a general message without speaker colon"
    messages = parse_conversation(raw)
    assert len(messages) == 1
    assert messages[0].text == "Just a general message without speaker colon"

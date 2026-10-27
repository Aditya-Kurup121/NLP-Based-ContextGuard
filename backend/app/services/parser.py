import re
from typing import List, Dict, Any, Optional

class ParsedMessage:
    def __init__(self, id: int, speaker: str, text: str, raw_line: str):
        self.id = id
        self.speaker = speaker.strip()
        self.text = text.strip()
        self.raw_line = raw_line.strip()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "speaker": self.speaker,
            "text": self.text,
            "raw_line": self.raw_line
        }

def parse_conversation(raw_text: str) -> List[ParsedMessage]:
    """
    Parses conversational text into structured turns with speaker and utterance.
    Supports formats:
      - Alice: Hello Bob!
      - [10:30 AM] Alice: Hey there
      - <Alice> What's up
      - Alice - No way
      - Multi-line continuation under the same speaker
    """
    if not raw_text or not raw_text.strip():
        return []

    lines = raw_text.strip().splitlines()
    parsed_messages: List[ParsedMessage] = []
    
    # Patterns for speaker identification
    # 1. Standard: "Alice: text" or "[timestamp] Alice: text" or "10:30 Alice: text"
    p_timestamp_colon = re.compile(r'^(?:\[[\d\s:\w\.\-\/,]+\]|\(?\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?\)?)?\s*([A-Za-z0-9_\-\.\s]{1,35}?)\s*[:：]\s*(.*)$')
    # 2. Angle brackets: "<Alice> text"
    p_bracket = re.compile(r'^<([A-Za-z0-9_\-\.\s]{1,35})>\s*(.*)$')
    # 3. Dash: "Alice - text"
    p_dash = re.compile(r'^([A-Za-z0-9_\-\.\s]{1,35}?)\s*[-—]\s*(.*)$')

    current_speaker: Optional[str] = None
    current_text_buffer: List[str] = []
    msg_counter = 1

    def commit_current():
        nonlocal msg_counter, current_speaker, current_text_buffer
        if current_speaker and current_text_buffer:
            combined_text = " ".join(current_text_buffer).strip()
            if combined_text:
                parsed_messages.append(
                    ParsedMessage(
                        id=msg_counter,
                        speaker=current_speaker,
                        text=combined_text,
                        raw_line=f"{current_speaker}: {combined_text}"
                    )
                )
                msg_counter += 1
            current_text_buffer = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        match = p_timestamp_colon.match(stripped)
        if not match:
            match = p_bracket.match(stripped)
        if not match:
            # Only use dash if speaker isn't too long and contains no commas/sentences
            dash_match = p_dash.match(stripped)
            if dash_match and len(dash_match.group(1).strip().split()) <= 3:
                match = dash_match

        if match:
            # We found a new turn with explicit speaker
            potential_speaker = match.group(1).strip()
            # Sanity check: speaker shouldn't be full sentence or start with numbers only
            if len(potential_speaker) > 0 and len(potential_speaker) <= 30 and not potential_speaker.startswith("http"):
                commit_current()
                current_speaker = potential_speaker
                content = match.group(2).strip()
                if content:
                    current_text_buffer.append(content)
                continue

        # If no speaker pattern matched
        if current_speaker:
            # Continuation of previous turn
            current_text_buffer.append(stripped)
        else:
            # First line without explicit speaker label: treat as Speaker 1 or Unknown
            commit_current()
            current_speaker = f"Speaker {msg_counter}"
            current_text_buffer.append(stripped)

    # Commit any trailing utterance
    commit_current()

    # Fallback if text was formatted weirdly (e.g. single block of text)
    if not parsed_messages and raw_text.strip():
        parsed_messages.append(
            ParsedMessage(
                id=1,
                speaker="Speaker 1",
                text=raw_text.strip(),
                raw_line=raw_text.strip()
            )
        )

    return parsed_messages

import re
from typing import List


def split_message(text: str, max_length: int = 1950) -> List[str]:
    """Split a message into chunks that fit within Discord's 2000-character limit.

    Handles smart splitting by paragraphs, lines, sentences, and spaces, and properly
    closes and reopens markdown code blocks across chunk boundaries so syntax formatting
    remains intact.

    Args:
        text: The message string to split.
        max_length: Maximum character length per chunk (defaults to 1950 to leave safety margin).

    Returns:
        A list of string chunks, each <= max_length.
    """
    if not text:
        return []

    text = text.strip()
    if not text:
        return []

    if len(text) <= max_length:
        return [text]

    chunks = []
    remaining = text

    while remaining:
        remaining = remaining.strip()
        if not remaining:
            break

        if len(remaining) <= max_length:
            chunks.append(remaining)
            break

        # Reserve safety buffer for potential closing code fences (e.g., '\n```')
        search_limit = min(len(remaining), max_length - 15)
        segment = remaining[:search_limit]

        split_idx = -1

        # Prefer paragraph break, then newline, then sentence endings, then space
        for candidate in ["\n\n", "\n", ". ", "! ", "? ", " "]:
            pos = segment.rfind(candidate)
            if pos > 0:
                if candidate in [". ", "! ", "? "]:
                    split_idx = pos + 1
                else:
                    split_idx = pos
                break

        # If no suitable separator was found, hard cut at search_limit
        if split_idx <= 0:
            split_idx = search_limit

        chunk = remaining[:split_idx].rstrip()
        remaining = remaining[split_idx:].lstrip()

        # Check code block balance in the chunk
        triple_count = chunk.count("```")
        if triple_count % 2 == 1:
            # An unclosed code block exists in this chunk
            matches = list(re.finditer(r"```([a-zA-Z0-9_\-\+\.]*)", chunk))
            lang = matches[-1].group(1).strip() if matches else ""
            chunk = chunk + "\n```"
            remaining = f"```{lang}\n" + remaining

        if chunk.strip():
            chunks.append(chunk)

    return chunks

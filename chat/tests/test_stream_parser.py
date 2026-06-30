import json

from chat.app.stream_parser import StreamParser


def test_stream_parser_assistant_delta():
    parser = StreamParser()
    lines = [
        json.dumps(
            {
                "type": "system",
                "subtype": "init",
                "session_id": "abc-123",
            }
        ),
        json.dumps(
            {
                "type": "assistant",
                "message": {
                    "role": "assistant",
                    "content": [{"type": "text", "text": "Ciao"}],
                },
                "session_id": "abc-123",
                "timestamp_ms": 1,
            }
        ),
        json.dumps(
            {
                "type": "assistant",
                "message": {
                    "role": "assistant",
                    "content": [{"type": "text", "text": "Ciao mondo"}],
                },
                "session_id": "abc-123",
                "timestamp_ms": 2,
            }
        ),
        json.dumps({"type": "result", "is_error": False}),
    ]

    events = list(parser.parse_stream(lines))
    deltas = [e.text_delta for e in events if e.text_delta]
    assert "Ciao" in deltas[0]
    assert deltas[1] == " mondo"
    assert any(e.session_id == "abc-123" for e in events)
    assert events[-1].done is True


def test_stream_parser_error_line():
    parser = StreamParser()
    events = list(parser.parse_stream(["Error: Authentication required"]))
    assert events[0].error == "Error: Authentication required"

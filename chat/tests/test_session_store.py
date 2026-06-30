from chat.app.session_store import SessionStore


def test_session_store_roundtrip(tmp_path):
    store = SessionStore(tmp_path / "test.db")
    session = store.create_session(title="Test", mode="ask")
    store.add_message(session.id, "user", "Ciao")
    store.add_message(session.id, "assistant", "Ciao!")
    loaded = store.get_session(session.id)
    assert loaded is not None
    assert loaded.title == "Test"
    messages = store.list_messages(session.id)
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[1].content == "Ciao!"

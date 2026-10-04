from app.session_service import token_hash
def test_token_hash():
    raw="demo-token";hashed=token_hash(raw)
    assert hashed==token_hash(raw)
    assert raw not in hashed
    assert len(hashed)==64

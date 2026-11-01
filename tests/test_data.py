from minigit import data


def test_round_trip(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    data.init()
    oid = data.hash_object(b"hello")
    assert data.get_object(oid) == b"hello"


def test_same_content_same_hash(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    data.init()
    assert data.hash_object(b"hello") == data.hash_object(b"hello")


def test_identical_dirs_same_tree(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    data.init()
    for name in ("one", "two"):
        d = tmp_path / name
        d.mkdir()
        (d / "f.txt").write_text("hi")
    assert data.write_tree("one") == data.write_tree("two")
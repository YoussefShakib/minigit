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


def test_commits_link_through_parent(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    data.init()
    (tmp_path / "a.txt").write_text("version 1")
    first = data.commit("first")
    (tmp_path / "a.txt").write_text("version 2")
    second = data.commit("second")

    assert data.get_commit(second).parent == first
    assert data.get_commit(first).parent is None
    assert data.get_commit(second).message == "second"
    assert data.get_HEAD() == second


def test_checkout_restores_old_version(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    data.init()
    (tmp_path / "a.txt").write_text("version 1")
    first = data.commit("first")
    (tmp_path / "a.txt").write_text("version 2")
    data.commit("second")

    data.read_tree(data.get_commit(first).tree)

    assert (tmp_path / "a.txt").read_text() == "version 1"


def test_checkout_removes_files_not_in_commit(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    data.init()
    (tmp_path / "a.txt").write_text("hi")
    first = data.commit("first")
    (tmp_path / "b.txt").write_text("new file")

    data.read_tree(data.get_commit(first).tree)

    assert not (tmp_path / "b.txt").exists()
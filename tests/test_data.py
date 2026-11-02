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

def test_branch_moves_with_commits(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    data.init()
    (tmp_path / "a.txt").write_text("1")
    first = data.commit("first")
    data.create_branch("feature", first)
    (tmp_path / "a.txt").write_text("2")
    second = data.commit("second")

    assert data.current_branch() == "main"
    assert data.get_ref("refs/heads/main") == second
    assert data.get_ref("refs/heads/feature") == first


def test_tag_resolves_to_commit(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    data.init()
    (tmp_path / "a.txt").write_text("1")
    first = data.commit("first")
    data.create_tag("v1", first)
    assert data.resolve("v1") == first

def _switch(branch: str, commit_oid: str):
    data.read_tree(data.get_commit(commit_oid).tree)
    data.set_HEAD(branch, symbolic=True)


def test_merge_without_conflict(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    data.init()
    (tmp_path / "a.txt").write_text("1")
    (tmp_path / "b.txt").write_text("1")
    base = data.commit("base")
    data.create_branch("feature", base)

    (tmp_path / "a.txt").write_text("2")
    main_tip = data.commit("change a on main")

    _switch("feature", base)
    (tmp_path / "b.txt").write_text("2")
    data.commit("change b on feature")

    conflicts = data.merge(main_tip)

    assert conflicts == []
    assert (tmp_path / "a.txt").read_text() == "2"
    assert (tmp_path / "b.txt").read_text() == "2"


def test_merge_conflict_writes_markers(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    data.init()
    (tmp_path / "a.txt").write_text("base")
    base = data.commit("base")
    data.create_branch("feature", base)

    (tmp_path / "a.txt").write_text("main version")
    main_tip = data.commit("main change")

    _switch("feature", base)
    (tmp_path / "a.txt").write_text("feature version")
    data.commit("feature change")

    conflicts = data.merge(main_tip)

    assert conflicts == ["a.txt"]
    text = (tmp_path / "a.txt").read_text()
    assert "<<<<<<< ours" in text
    assert "main version" in text
    assert "feature version" in text


def test_merge_fast_forward(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    data.init()
    (tmp_path / "a.txt").write_text("1")
    first = data.commit("first")
    (tmp_path / "a.txt").write_text("2")
    second = data.commit("second")

    data.set_ref("refs/heads/main", first)
    data.read_tree(data.get_commit(first).tree)

    assert data.merge(second) == []
    assert (tmp_path / "a.txt").read_text() == "2"
    assert data.get_HEAD() == second
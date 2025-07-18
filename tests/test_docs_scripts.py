from pathlib import Path


def test_docs_have_matching_scripts():
    repo_root = Path(__file__).resolve().parents[1]
    docs_dir = repo_root / "docs"
    scripts_root = repo_root / "scripts"
    for doc in docs_dir.glob("*.md"):
        script_base = doc.stem
        dir_path = scripts_root / script_base
        assert dir_path.is_dir(), f"{dir_path} missing for {doc.name}"
        ext = ".zsh" if script_base == "open_console" else ".py"
        script_path = dir_path / f"{script_base}{ext}"
        assert script_path.is_file(), f"{script_path} missing for {doc.name}"

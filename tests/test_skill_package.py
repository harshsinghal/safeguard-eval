"""Observable installation, evidence freshness, and release-package invariants."""
import hashlib
import json
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "skills" / "safeguard-eval"
INSTALLER = runpy.run_path(str(PACKAGE / "scripts" / "install.py"))
RELEASE = runpy.run_path(str(ROOT / "tools" / "skill_release.py"))


class SkillInstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "download" / "safeguard-eval"
        shutil.copytree(PACKAGE, self.source)
        self.dest = self.root / "project" / ".agents" / "skills" / "safeguard-eval"

    def test_install_and_identical_reinstall(self):
        result = INSTALLER["install"](self.source, self.dest)
        self.assertEqual(result["status"], "installed")
        self.assertEqual(INSTALLER["verify_package"](self.dest)["version"],
                         json.loads((self.source / "release.json").read_text())["version"])
        self.assertEqual(INSTALLER["install"](self.source, self.dest)["status"], "unchanged")
        self.assertFalse((self.dest.parent.parent / "skill-backups").exists())

    def test_update_preserves_local_edits_in_backup(self):
        INSTALLER["install"](self.source, self.dest)
        edited = self.dest / "references" / "authoring.md"
        edited.write_text("My local policy-authoring notes.\n", encoding="utf-8")
        (self.dest / "my-notes.txt").write_text("Keep these notes.", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "--update"):
            INSTALLER["install"](self.source, self.dest)
        result = INSTALLER["install"](self.source, self.dest, update=True)
        backup = Path(result["backup"])
        self.assertEqual((backup / "references" / "authoring.md").read_text(), "My local policy-authoring notes.\n")
        self.assertEqual((backup / "my-notes.txt").read_text(), "Keep these notes.")
        self.assertFalse((self.dest / "my-notes.txt").exists())
        INSTALLER["verify_package"](self.dest)

    def test_tampered_download_does_not_install(self):
        (self.source / "SKILL.md").write_text("Changed instructions", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "integrity"):
            INSTALLER["install"](self.source, self.dest)
        self.assertFalse(self.dest.exists())

    def test_unrelated_directory_is_preserved(self):
        self.dest.mkdir(parents=True)
        note = self.dest / "important.txt"
        note.write_text("Keep me", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "recognized"):
            INSTALLER["install"](self.source, self.dest, update=True)
        self.assertEqual(note.read_text(), "Keep me")

    def test_symbolic_link_destination_is_not_replaced(self):
        self.dest.parent.mkdir(parents=True)
        self.dest.symlink_to(self.source, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symbolic-link destination"):
            INSTALLER["install"](self.source, self.dest, update=True)
        self.assertTrue(self.dest.is_symlink())

    def test_package_symbolic_links_are_rejected(self):
        (self.source / "unexpected-link").symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symbolic link"):
            INSTALLER["verify_package"](self.source)

    def test_manifest_cannot_reference_parent_directory(self):
        path = self.source / "manifest.json"
        data = json.loads(path.read_text())
        data["files"]["../outside.txt"] = "0" * 64
        path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Invalid manifest entry"):
            INSTALLER["verify_package"](self.source)

    def test_source_cannot_be_installed_inside_itself(self):
        with self.assertRaisesRegex(ValueError, "separate directories"):
            INSTALLER["install"](self.source, self.source / "nested")
        self.assertFalse((self.source / "nested").exists())

    def test_cli_installs_both_project_layouts(self):
        for target, directory in [("codex", ".agents"), ("claude-code", ".claude")]:
            completed = subprocess.run(
                [sys.executable, str(self.source / "scripts" / "install.py"),
                 "--target", target, "--scope", "project", "--project", str(self.root / target)],
                check=True, capture_output=True, text=True)
            data = json.loads(completed.stdout)
            expected = self.root / target / directory / "skills" / "safeguard-eval"
            self.assertEqual(Path(data["destination"]).resolve(), expected.resolve())
            INSTALLER["verify_package"](expected)

    def test_failed_final_rename_restores_previous_installation(self):
        INSTALLER["install"](self.source, self.dest)
        note = self.dest / "local.txt"
        note.write_text("Restore me", encoding="utf-8")
        real_rename = Path.rename

        def fail_staging_rename(path, target):
            if path.name.startswith(".safeguard-eval-install-"):
                raise OSError("Simulated interrupted replacement")
            return real_rename(path, target)

        with mock.patch.object(Path, "rename", fail_staging_rename):
            with self.assertRaisesRegex(OSError, "interrupted"):
                INSTALLER["install"](self.source, self.dest, update=True)
        self.assertEqual(note.read_text(), "Restore me")


class SkillReleaseTests(unittest.TestCase):
    def test_evidence_and_numeric_snapshot_are_current(self):
        RELEASE["check"]()

    def test_zip_is_reproducible_and_installable(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            first = RELEASE["build"](root / "a")
            second = RELEASE["build"](root / "b")
            self.assertEqual(hashlib.sha256(first.read_bytes()).digest(),
                             hashlib.sha256(second.read_bytes()).digest())
            with zipfile.ZipFile(first) as archive:
                self.assertTrue(all(p.startswith("safeguard-eval/") and ".." not in Path(p).parts
                                    for p in archive.namelist()))
                archive.extractall(root / "unpacked")
            extracted = root / "unpacked" / "safeguard-eval"
            INSTALLER["verify_package"](extracted)
            result = INSTALLER["install"](extracted, root / "project" / ".claude" / "skills" / "safeguard-eval")
            self.assertEqual(result["status"], "installed")

    def test_changed_evidence_and_new_studies_require_review(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            path = "published_runs/2026-01-01-fixture/README.md"
            evidence = root / path
            evidence.parent.mkdir(parents=True)
            evidence.write_text("Reviewed evidence", encoding="utf-8")

            def git(*args):
                return subprocess.check_output(["git", *args], cwd=root, stderr=subprocess.DEVNULL)

            git("init", "-q")
            git("add", ".")
            git("-c", "user.name=Skill Test", "-c", "user.email=skill-test@example.invalid",
                "commit", "-qm", "Evidence fixture")
            revision = git("rev-parse", "HEAD").decode().strip()
            release = {"evidence_revision": revision, "evidence_through": "2026-01-01",
                       "repository": "https://github.com/harshsinghal/safeguard-eval"}
            with mock.patch.dict(RELEASE["registry"].__globals__, {"ROOT": root, "SOURCES": {"fixture": path}}):
                RELEASE["registry"](release)
                evidence.write_text("Changed evidence", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "Evidence changed"):
                    RELEASE["registry"](release)
                evidence.write_text("Reviewed evidence", encoding="utf-8")
                (root / "published_runs" / "2026-01-02-new-study").mkdir()
                with self.assertRaisesRegex(ValueError, "inventory changed"):
                    RELEASE["registry"](release)


if __name__ == "__main__":
    unittest.main()

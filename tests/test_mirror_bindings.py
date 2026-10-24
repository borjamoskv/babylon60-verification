"""The public verifier must reject internally inconsistent, rehashed packages."""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).absolute().parents[1]
VERIFIER = ROOT / "verify.py"


def rewrite(root: Path, name: str, value: object) -> None:
    payload = (json.dumps(value, indent=2) + "\n").encode()
    (root / name).write_bytes(payload)
    manifest = json.loads((root / "mirror-manifest.json").read_bytes())
    entry = next(item for item in manifest["files"] if item["path"] == name)
    entry.update(bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())
    (root / "mirror-manifest.json").write_text(json.dumps(manifest))


@pytest.fixture
def package(tmp_path: Path) -> Path:
    root = tmp_path / "mirror"
    shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns(".git", ".lake", "__pycache__", ".pytest_cache"))
    release = json.loads((root / "RELEASE_MANIFEST.json").read_bytes())
    run = json.loads((root / "claims_sitrep.json").read_bytes())
    # A consistent isolated baseline, independent of the historical publication.
    release["claims_manifest_digest"] = run["claims_manifest_digest"]
    release["claims"] = {
        "total": run["total_claims"], "verified": run["verified"],
        "empirical_and_bounded": run["partial"], "experimental": run["experimental"],
        "failed": len(run["failed_claims"]),
    }
    rewrite(root, "RELEASE_MANIFEST.json", release)
    return root


def verify(root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(VERIFIER), "--root", str(root)],
        capture_output=True, text=True, check=False,
    )


def test_consistent_unsigned_package_is_integrity_only(package: Path) -> None:
    result = verify(package)
    assert result.returncode == 0, result.stderr
    assert "Signing identity: NOT VERIFIED" in result.stdout


@pytest.mark.parametrize("corruption", ["digest", "total", "verified", "partial", "experimental", "failed"])
def test_rehashed_release_cannot_describe_different_claims(package: Path, corruption: str) -> None:
    release = json.loads((package / "RELEASE_MANIFEST.json").read_bytes())
    if corruption == "digest":
        release["claims_manifest_digest"] = "0" * 64
    else:
        key = "empirical_and_bounded" if corruption == "partial" else corruption
        release["claims"][key] += 1
    rewrite(package, "RELEASE_MANIFEST.json", release)
    result = verify(package)
    assert result.returncode == 1, result.stdout
    assert "Release" in result.stderr
    assert "INTEGRITY OK" not in result.stdout


def test_claim_run_mismatch_never_prints_success(package: Path) -> None:
    run = json.loads((package / "claims_sitrep.json").read_bytes())
    run["claims_manifest_digest"] = "0" * 64
    rewrite(package, "claims_sitrep.json", run)
    result = verify(package)
    assert result.returncode == 1
    assert "INTEGRITY OK" not in result.stdout


def test_modified_bytes_are_rejected(package: Path) -> None:
    with (package / "proof/lean/AX0.lean").open("a") as stream:
        stream.write("\n-- modified without updating the inventory\n")
    result = verify(package)
    assert result.returncode == 1
    assert "Artifact integrity failure" in result.stderr

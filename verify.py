#!/usr/bin/env python3
"""Verify the mirror's bytes offline. Integrity is distinct from signing identity."""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import sys


def read_artifact(root: Path, relative: str) -> bytes:
    path = PurePosixPath(relative)
    if path.is_absolute() or path.as_posix() != relative or any(
        part in ("", ".", "..") for part in relative.split("/")
    ):
        raise ValueError(f"Unsafe artifact path: {relative}")
    target = root
    for part in path.parts:
        target = target / part
        if target.is_symlink():
            raise ValueError(f"Symlink artifact rejected: {relative}")
    fd = os.open(target, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(fd, "rb") as stream:
        return stream.read()


def verify(root: Path, expected_digest: str | None, release_key: str | None) -> None:
    raw = read_artifact(root, "mirror-manifest.json")
    digest = hashlib.sha256(raw).hexdigest()
    if expected_digest is not None and digest != expected_digest.lower():
        raise ValueError("Mirror manifest does not match the supplied SHA-256 pin")
    manifest = json.loads(raw)
    if manifest.get("schema") != "babylon60.verification-mirror/v1":
        raise ValueError("Unsupported mirror schema")
    entries = manifest["files"]
    paths = [entry["path"] for entry in entries]
    required = {"CLAIMS.toml", "claims_sitrep.json", "RELEASE_MANIFEST.json",
                "proof/lean/AX0.lean", "lean-toolchain", "lakefile.toml", "verify.py", "LICENSE"}
    if len(paths) != len(set(paths)) or not required.issubset(paths):
        raise ValueError("Incomplete or duplicate artifact inventory")
    for entry in entries:
        payload = read_artifact(root, entry["path"])
        if len(payload) != entry["bytes"] or hashlib.sha256(payload).hexdigest() != entry["sha256"]:
            raise ValueError(f"Artifact integrity failure: {entry['path']}")
    sitrep = json.loads(read_artifact(root, "claims_sitrep.json"))
    claims_digest = hashlib.sha256(read_artifact(root, "CLAIMS.toml")).hexdigest()
    if sitrep["claims_manifest_digest"] != claims_digest:
        raise ValueError("Claim run does not match the packaged CLAIMS.toml")
    release = json.loads(read_artifact(root, "RELEASE_MANIFEST.json"))
    if release.get("claims_manifest_digest") != claims_digest:
        raise ValueError("Release does not match the packaged CLAIMS.toml")
    failures = sitrep.get("failed_claims", [])
    expected_counts = {
        "total": sitrep["total_claims"],
        "verified": sitrep["verified"],
        "empirical_and_bounded": sitrep["partial"],
        "experimental": sitrep["experimental"],
        "failed": len(failures),
    }
    if release.get("claims") != expected_counts:
        raise ValueError("Release claim counts do not match the packaged claim run")
    print(f"INTEGRITY OK: {len(entries)} artifacts; manifest SHA-256 {digest}")
    print("Scope: packaged bytes and manifest bindings only. This does not re-run the runtime harness.")
    print(f"Recorded claim-run failures: {len(failures)} ({', '.join(failures) or 'none'})")
    print(f"Recorded claims: {sitrep['verified']} verified; {sitrep['partial']} bounded/partial. "
          "Historical per-row 'verified' flags may denote suite success, not proof of the property.")
    print("Secure Enclave human presence: NO_VERIFICADO by these automated tests.")
    if release_key is None:
        print("Signing identity: NOT VERIFIED. Use --release-public-key with an independently trusted key.")
        return
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    signature = release.pop("signature")
    trusted = bytes.fromhex(release_key)
    embedded = bytes.fromhex(release["signing_authority"]["public_key"])
    if len(trusted) != 32 or embedded != trusted:
        raise ValueError("Release signing key does not match the independently supplied key")
    Ed25519PublicKey.from_public_bytes(trusted).verify(
        bytes.fromhex(signature), json.dumps(release, sort_keys=True).encode("utf-8")
    )
    print("Historical release signature: VALID against the supplied key.")
    print("This signature does not attest the current dirty source tree or the mirror itself.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).absolute().parent)
    parser.add_argument("--expected-manifest-sha256")
    parser.add_argument("--release-public-key", help="Trusted Ed25519 public key (hex); requires cryptography")
    args = parser.parse_args()
    try:
        verify(args.root, args.expected_manifest_sha256, args.release_public_key)
    except Exception as error:
        print(f"VERIFICATION FAILED: {type(error).__name__}: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

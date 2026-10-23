# BABYLON-60 Verification Mirror

ES: Este paquete permite inspeccionar manifiestos e informes y compilar AX0 sin
acceso al monorepo privado. Separa integridad, identidad de firma y ejecución.
Los informes históricos se conservan con sus limitaciones, incluidos atestados
inválidos y fallos simulados. Las pruebas nuevas no los sustituyen ni los firman.

EN: Inspect manifests and reports and compile AX0 without private repository
access. Integrity, signing identity and runtime evidence are separate checks.
Historical reports retain their invalid attestations and simulated faults;
new tests neither replace nor sign those reports.

Requires Python 3.10+ for offline file verification. From the extracted directory:

```sh
python3 verify.py
```

Exit code 0 means that the artifact inventory and claims-manifest binding match.
It does not mean that every recorded test passed, that the release is current,
or that any signing identity has been verified. Read the reported failures.
For a digest obtained through a trusted channel:

```sh
python3 verify.py --expected-manifest-sha256 <trusted-mirror-manifest-sha256>
```

An attacker able to replace both files and the unsigned manifest can recompute
their hashes. A digest served alongside a download provides consistency within
that publication; it is not an independent identity anchor.

To check the historical release signature, provide an independently trusted
Ed25519 public key. This optional mode requires the Python `cryptography` package
already installed; the verifier does not install dependencies or use the network:

```sh
python3 verify.py --release-public-key <trusted-ed25519-public-key-hex>
```

To machine-check the formal authorization model with the exact Lean version in
`lean-toolchain`, install that toolchain with Elan, then run:

```sh
lake build
```

The minimal Lake project has no third-party dependencies. A first toolchain
installation needs network access; building with that toolchain installed does
not need the private monorepo. The theorem concerns the finite state model,
not correspondence with production Rust, physical energy, or hardware origin.

`CLAIMS.toml` documents reproduction commands for the complete private harness.
Those runtime sources and the operator's private keys are not in this mirror.
Software P-256 tests do not demonstrate Touch ID or human presence in Secure
Enclave. A real SIGKILL test demonstrates process death, not power-loss safety.

Source rights are defined by the included, unchanged `LICENSE`; no additional
open-source or commercial license is granted by this packaging.

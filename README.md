# BABYLON-60 Verification Mirror

ES: Este paquete permite inspeccionar manifiestos e informes y compilar AX0 sin
acceso al árbol de trabajo del autor. Separa integridad, identidad de firma y ejecución.
Los informes históricos se conservan con sus limitaciones, incluidos atestados
inválidos y fallos simulados. Las pruebas nuevas no los sustituyen ni los firman.

EN: Inspect manifests and reports and compile AX0 without the author's working
tree. Integrity, signing identity and runtime evidence are separate checks.
Historical reports retain their invalid attestations and simulated faults;
new tests neither replace nor sign those reports.

## Verificación manual / Manual verification

ES: Desde la raíz del repositorio o del paquete extraído, ejecuta:

EN: From the repository root or the extracted package, run:

```sh
./verify.sh
```

ES: Comprueba primero los hashes y después compila AX0 con `lake build`. Si los
hashes fallan, no compila. Devuelve un código distinto de cero si falla cualquiera
de las dos comprobaciones. Requiere Python 3.10+ y Elan con la versión de Lean
indicada en `lean-toolchain`.

EN: Checks hashes first, then compiles AX0 with `lake build`. A hash failure stops
the command before compilation. Either failure returns a nonzero exit code.
Requires Python 3.10+ and Elan with the Lean version specified in `lean-toolchain`.

Exit code 0 means that the artifact inventory, CLAIMS/sitrep/release digest bindings
and release/run claim counts match
and AX0 compiles. It does not mean that every recorded runtime test passed, that
the release is current, or that a signing identity has been verified. Read the
reported failures. Historical per-row `verified` flags can mean suite success;
use `status` and aggregate counts to distinguish bounded evidence.

The original release manifest is preserved at
`reports/historical-release-manifest.json`. It referred to an older CLAIMS.toml
and is not the release manifest checked against this package. Its replacement
comes from the local source tree recorded under `artifact_updates` in
`mirror-manifest.json`. It remains unsigned and does not attest the current
source tree or a new runtime run. The mirror's `generated_at` dates packaging;
the claim-run timestamp continues to identify the historical test run.
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

The minimal Lake project has no third-party dependencies. A first toolchain
installation needs network access; building with that toolchain installed does
not need the full monorepo. The theorem concerns the finite state model,
not correspondence with production Rust, physical energy, or hardware origin.

`CLAIMS.toml` documents reproduction commands for the complete runtime harness.
Those runtime sources and the operator's private keys are not in this mirror.
Software P-256 tests do not demonstrate Touch ID or human presence in Secure
Enclave. A real SIGKILL test demonstrates process death, not power-loss safety.

Source rights are defined by the included, unchanged `LICENSE`; no additional
open-source or commercial license is granted by this packaging.

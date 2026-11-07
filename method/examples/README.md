# Synthetic public records

The four positive receipts form research, engineering, document and prepared
publication records. They have no subject measurement or external delivery.
INDEX.json gives each receipt reference and expected result. The negative
source-hash receipt must fail even when its own file is correctly listed in
the repository manifest. It substitutes a source fingerprint while leaving
the actual public source bytes unchanged.

All sources are bundled here. The common method bundle is in ../v1. Run the
portable verifier from the repository root with the reference and hash in
INDEX.json. Repository MANIFEST.sha256 must include these candidate files;
maintainers regenerate it only after the intended changes are reviewed.

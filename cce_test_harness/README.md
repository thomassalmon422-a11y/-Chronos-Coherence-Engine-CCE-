# CCE hardening test harness

This directory contains a reference core and adversarial tests for the CCE calculations and in-memory SHA-256 chain.

## Run locally

```bash
python -m pip install -r requirements-test.txt
python -m pytest -v
```

## Scope and limitations

- Tests establish only the behavior asserted here; they do not validate the real-world predictive quality of risk scores or the legal status of any fees or rights.
- Float-based calculations are retained for compatibility with the prototype. Do not use this reference as a production financial ledger without adopting a documented decimal/minor-unit rounding policy and domain review.
- Hash chaining detects payload edits, broken links, and reordered records when the original chain is retained.
- A valid prefix remains valid after tail truncation, and an attacker able to rewrite every record and recompute every hash can create a new internally valid chain. These are explicit regression tests documenting the limitation.
- Production tamper evidence requires durable storage, access controls, independently retained checkpoints/signatures, and an external verification process.
- Test entries use an injected fixed timestamp for reproducibility. Normal calls generate a UTC timestamp; this alone does not prove trusted time or ordering.

This harness is an isolated testable reference. It does not silently replace or overwrite the repository's existing CCE implementation.

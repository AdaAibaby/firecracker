# RFC: A community-supported, best-effort tier, applied to Hygon (HygonGenuine) x86_64 support

## Summary

Add a small, bounded governance tier for hardware the core team's CI cannot
exercise, and use it to accept the `HygonGenuine` CPUID vendor string through
the existing AMD CPUID paths behind an **off-by-default** `hygon` cargo feature.

Two prior PRs added the Hygon mapping and were closed — not on technical grounds,
but because the project cannot test Hygon in CI and does not want to carry a
feature branch that goes stale:

- #5905 — closed: *"with our current infrastructure we are unable to test Hygon
  CPUs"*; a proposed experimental tier was declined because *"we have previously
  had feature branches but found they quickly became stale and hard to manage."*
- #6267 — closed as a duplicate of #5905's reasoning.

This RFC is written to resolve exactly those two objections (untestable, and
goes-stale), plus the safety concern implied by the CPU-templates doc's "one
vendor must not be represented as another". It asks for agreement on the
**tier** first; a reference implementation is attached but the decision being
requested is the governance model, not the diff.

## Problem (purely technical)

Hygon Dhyana / C86 report CPUID vendor `HygonGenuine`. Firecracker's x86_64
CPUID handling recognises only `GenuineIntel` and `AuthenticAMD` and rejects
anything else at two start-path gates:

1. `kvm_bindings::CpuId` → `Cpuid` conversion — `UnsupportedVendor`.
2. AMD cache-topology passthrough guard — `BadVendorId`.

So a microVM cannot start on a Hygon host. Hygon Dhyana is a **licensed AMD Zen
design**; the Linux kernel and KVM already route it through their AMD
implementation. The fix is to do the same at those two gates — a few lines.

## Why this was hard to accept, and how each objection is addressed

### 1. "We can't test it in CI."

**Provide the missing infrastructure.** The component's owners contribute a
Hygon host as a Buildkite agent and a dedicated pipeline
(`.buildkite/pipeline_hygon.py`) that runs the vendor-mapping unit test plus
boot, snapshot/restore and vsock end-to-end on real Hygon silicon. It runs only
on a `hygon` agent, at non-gating priority, and never blocks the core pipelines
or a release. The owners fund and operate it; the core fleet is unaffected.

### 2. "Feature branches go stale and are hard to manage."

**Keep it in mainline, but bound it.** This is not a feature branch — it is a
mainline component under a tier with:

- **Named owners** in `CODEOWNERS` who triage and fix it.
- **Auto-unsupported on bitrot**: if the dedicated CI is red (or absent) for 30
  days with no owner fix, the component is marked unsupported and may be removed
  per the deprecation policy. Staleness becomes a bounded, self-clearing state
  instead of silent rot.

### 3. "A vendor must not be represented as another" (safety).

**Enable the functional path; make no safety claim.** Mapping Hygon onto the AMD
paths makes a guest *run*; it is not a claim that AMD's security-relevant model
descriptions hold for Hygon silicon (microcode, errata, mitigations,
`IA32_ARCH_CAPABILITIES` may differ). Therefore the design keeps the static
CPU-template vendor check **strict and untouched**: eligibility compares the host
vendor to the template's supported vendor (`T2A` → `AuthenticAMD`), so a Hygon
host is **rejected from `T2A` by default**. Applying an AMD-derived template on
Hygon stays an explicit, per-bit-verified opt-in. The functional enablement does
not widen the security surface.

## The tier (proposed addition to MAINTAINERS.md)

"Community-supported, best-effort components" — hardware the core CI cannot
exercise:

- **Off by default** behind a cargo feature not enabled in any default/released
  build → default artifacts byte-for-byte unchanged, supported paths gain no
  runtime branch.
- **Named owners** in `CODEOWNERS`.
- **Dedicated, contributor-funded CI** on a separate, non-gating pipeline.
- **Auto-unsupported** after 30 days of red/absent CI with no owner fix.

It never blocks a release and never alters the Intel/AMD/ARM build.

## Reference implementation (attached, for discussion)

Feature `hygon`, off by default. `git diff --stat` vs `main`:

```
 src/vmm/Cargo.toml                                        |  6 +
 src/vmm/src/cpu_config/x86_64/cpuid/mod.rs                | 66 +++++++++++
 src/vmm/src/cpu_config/x86_64/cpuid/amd/normalize.rs      | 19 ++-
```

plus docs and governance:

```
 MAINTAINERS.md                              (new tier section)
 CODEOWNERS                                  (new; Hygon owners)
 .buildkite/pipeline_hygon.py                (new; owner-funded CI)
 docs/cpu_templates/hygon-support.md         (new; design + safety boundary)
 CHANGELOG.md
```

Properties:

- With the feature **off**, `HygonGenuine` is still rejected exactly like any
  other unknown vendor (asserted by `test_hygon_kvmcpuid_rejected_without_feature`).
- With the feature **on**, `HygonGenuine` maps to the AMD CPUID variant
  (`test_hygon_kvmcpuid_maps_to_amd`), and the AMD cache-topology passthrough
  accepts the Hygon host.
- The static-template vendor check is untouched → `T2A` rejected on Hygon by
  default.

## What this buys the project

- A clean way to accept hardware the core team cannot test, **without** taking on
  test burden, maintenance of stale branches, or risk to the supported paths.
- A reusable, generic mechanism: any future CPU reporting a distinct CPUID
  vendor that is architecturally equivalent to an already-supported one can be
  onboarded by the same tier — contributor CI, named owners, off-by-default
  feature, auto-unsupported safeguard — rather than case-by-case debate.
- New hardware exercising the AMD CPUID path tends to surface latent issues that
  benefit the AMD path too.

## Questions for maintainers

1. Is the best-effort tier (off-by-default feature + named owners + dedicated
   contributor CI + 30-day auto-unsupported) acceptable in principle?
2. Any additional constraints before Hygon is accepted as its first member
   (e.g. required e2e coverage on the owner pipeline, exact auto-unsupported
   window)?
3. Preferred home and format for the owner-provided CI agent registration?

## References

- `docs/cpu_templates/cpu-templates.md` (vendor/template model)
- PRs #5905, #6267 (prior attempts and the stated reasons for closing)

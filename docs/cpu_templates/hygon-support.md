# Hygon (HygonGenuine) x86_64 support — community-supported, best-effort

> [!NOTE]
>
> This is a **community-supported, best-effort** component (see
> [MAINTAINERS.md](../../MAINTAINERS.md)). It is compiled only when the `hygon`
> cargo feature is enabled, which is **off in every default and released
> build**. It is not part of the core CI-gated surface and carries no production
> guarantee. A default build is byte-for-byte unchanged by it.

## What it does

Hygon Dhyana / C86 processors report the CPUID vendor string `HygonGenuine`.
Firecracker's x86_64 CPUID handling recognises only `GenuineIntel` and
`AuthenticAMD`, and rejects anything else in two places on the start path:

1. the `kvm_bindings::CpuId` → `Cpuid` conversion
   (`CpuidTryFromKvmCpuid::UnsupportedVendor`), and
2. the AMD cache-topology passthrough guard
   (`PassthroughCacheTopologyError::BadVendorId`).

So a microVM fails to start on a Hygon host during CPUID initialisation.

Hygon Dhyana is a **licensed AMD Zen design**; the Linux kernel and KVM route it
through their AMD implementation (`arch/x86/kernel/cpu/`, KVM's AMD paths). The
`hygon` feature does the same inside Firecracker: it accepts `HygonGenuine`
**through the existing AMD CPUID paths**, as a licensed-Zen equivalent of
`AuthenticAMD`, at exactly those two gates — nothing more.

## Why it is small and low-risk

- **Minimal surface.** The mapping is a handful of lines at the two gates plus a
  feature-gated vendor constant and unit test. It adds no cross-cutting vendor
  enum and touches neither device, API, nor snapshot code.
- **Off by default, zero cost when off.** All of it is behind
  `#[cfg(feature = "hygon")]`. With the feature off the code is not compiled, so
  the Intel/AMD paths are unchanged and carry no extra runtime branch. A
  regression test (`test_hygon_kvmcpuid_rejected_without_feature`) asserts that a
  default build still rejects `HygonGenuine` like any other unknown vendor.
- **Equivalence tested on hardware.** The owners' dedicated pipeline
  (`.buildkite/pipeline_hygon.py`) runs the vendor-mapping unit test plus boot,
  snapshot/restore, and vsock end-to-end on a Hygon host.

## Safety boundary: functional enablement is not a safety claim

Mapping Hygon onto the AMD paths makes the guest **run**. It is **not** a claim
that AMD's security-relevant CPU model descriptions are correct for Hygon
silicon. Microcode, errata, speculative-execution mitigations, and the
`IA32_ARCH_CAPABILITIES` MSR are not guaranteed identical between a given Hygon
part and AMD Milan.

Per the CPU-templates documentation, a template that signals a hardware
mitigation the hardware does not actually implement can lead a guest to disable
its own software mitigation and become vulnerable. Therefore:

- **Static templates stay strict by default.** Static-template eligibility is
  decided by comparing the host vendor against the template's supported vendor
  (`T2A` → `AuthenticAMD`). The `hygon` feature deliberately does **not** touch
  that comparison, so a Hygon host (`HygonGenuine ≠ AuthenticAMD`) is **rejected
  from `T2A` by default** — no AMD static template is silently applied to Hygon.
- **Opt-in, per-bit-verified.** Applying an AMD-derived template on Hygon must
  be an explicit, owner-driven choice, and only after verifying the
  security-relevant bits (arch-capabilities, mitigation bits, cache topology) on
  the actual Hygon silicon. Until verified, treat them as unverified.
- **Snapshot migration.** Migrating snapshots between Hygon and AMD hosts is
  **not** declared safe here; it must be validated on the specific parts before
  being relied on.

This "enable the functional path, stay conservative on every safety claim"
split is deliberate: it keeps the change from quietly widening Firecracker's
security surface.

## Building with Hygon support

```bash
# vmm unit + the firecracker binary, with the feature enabled
tools/devtool build --features hygon
```

The feature is never enabled in the default build; enabling it is an explicit,
local decision by whoever operates Hygon hardware.

## Ownership and lifecycle

Owners are listed in [`CODEOWNERS`](../../CODEOWNERS) and are responsible for
triaging and fixing Hygon-only issues and for keeping
`.buildkite/pipeline_hygon.py` green on their hardware. Per the best-effort tier
rules, if that pipeline is red or absent for 30 days with no owner fix, the
component is marked unsupported and may be removed.

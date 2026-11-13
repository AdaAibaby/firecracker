# Maintainers

Firecracker is maintained by a dedicated team within Amazon:

- Egor Lazarchuk <yegorlz@amazon.co.uk>
- Ilias Stamatis <ilstam@amazon.com>
- Jack Thomson <jackabt@amazon.com>
- James Curtis <jxcurtis@amazon.com>
- Jay Chung <jaehoc@amazon.com>
- Marco Marangoni <mamarang@amazon.com>
- Michael Zoumboulakis <zoumboul@amazon.com>
- Pierre Bertholom <pbertho@amazon.com>
- Riccardo Mancini <mancio@amazon.com>
- Takahiro Itazuri <itazur@amazon.com>

## Community-supported, best-effort components

Some components target hardware the core team's CI cannot exercise. They live in
mainline behind an off-by-default build feature, are owned by named community
contributors, and are **not** part of the project's supported/CI-gated surface
or its production guarantees. They never block a release and never alter the
default (Intel/AMD/ARM) build.

Rules for this tier:

- **Off by default.** The code is behind a cargo feature that is not enabled in
  any default or released build, so default artifacts are byte-for-byte
  unchanged and the supported paths carry no added runtime branch.
- **Named owners.** Each component lists owners in `CODEOWNERS`; those owners
  triage and fix issues for it.
- **Dedicated, contributor-funded CI.** Validation runs on hardware the owners
  provide, on a separate pipeline that does not gate the core pipelines.
- **Auto-unsupported on bitrot.** If a component's dedicated CI is red (or
  absent) for 30 days with no owner fix, it is marked unsupported and may be
  removed per the deprecation policy. This keeps the tier bounded rather than
  silently stale.

Current components in this tier:

| Component | Feature flag | Docs | Owners |
| --------- | ------------ | ---- | ------ |
| Hygon (HygonGenuine) x86_64 support via the AMD paths | `hygon` | [docs/cpu_templates/hygon-support.md](docs/cpu_templates/hygon-support.md) | see `CODEOWNERS` |

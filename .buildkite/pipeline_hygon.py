#!/usr/bin/env python3
# Copyright 2026 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Dedicated, contributor-funded pipeline for the best-effort `hygon` feature.

This pipeline validates the off-by-default `hygon` build on Hygon (HygonGenuine)
hardware provided by the component's owners (see CODEOWNERS / MAINTAINERS.md).

It is intentionally separate from the core PR/main pipelines: it runs only on a
`hygon` agent, it does not gate Intel/AMD/ARM CI, and a release never waits on
it. If this pipeline is red (or has no agent) for 30 days with no owner fix, the
component is marked unsupported per the best-effort tier policy.

Build the pipeline JSON with:

    .buildkite/pipeline_hygon.py | buildkite-agent pipeline upload
"""

from common import BKPipeline

# A low, non-gating priority: this must never crowd out the core pipelines.
DEFAULT_PRIORITY = 0

# Owner-provided Hygon host. The agent tag is registered by the owners on their
# own Buildkite agent; the core fleet has no such agent, which is exactly why
# this lives in its own pipeline.
HYGON_AGENTS = {"vendor": "hygon"}

pipeline = BKPipeline(
    priority=DEFAULT_PRIORITY,
    timeout_in_minutes=45,
    # Build the vmm + firecracker with the feature actually under test.
    build_args="--features hygon",
)

# 1) The feature's own unit test: HygonGenuine maps to the AMD CPUID variant.
pipeline.add_step(
    {
        "label": "🧩 hygon: cpuid vendor mapping unit test",
        "command": "tools/devtool -y test -- "
        "-p vmm --features hygon cpu_config::x86_64::cpuid",
        "agents": HYGON_AGENTS,
    }
)

# 2) End-to-end smoke on real Hygon silicon: boot, snapshot/restore, vsock.
#    These are the behaviours the maintainers said they could not verify without
#    the hardware; running them here on an owner-provided host is what closes
#    that gap.
for suite in (
    "integration_tests/functional/test_api.py",
    "integration_tests/functional/test_snapshot_basic.py",
    "integration_tests/functional/test_vsock.py",
):
    pipeline.add_step(
        {
            "label": f"🚀 hygon e2e: {suite.split('/')[-1]}",
            "command": f"tools/devtool -y test --features hygon -- {suite}",
            "agents": HYGON_AGENTS,
        }
    )

if __name__ == "__main__":
    print(pipeline.to_json())

"""IP-SAKTI Sahayak — Member 6 integration foundation (Phase 1).

This package is the MINIMAL integration foundation for connecting the five
completed member workstreams (M1 central assistant, M2 classifier, M3 India,
M4 ABS/TK, M5 International) in Phase 2. It contains no domain knowledge of
its own and does not connect the real member implementations yet.

Layout:

    contracts.py          target contract shapes + pure-stdlib validators
                          (Plan.md §7 / MEMBER_6.md §3) + error-code mapping
    stubs.py              deterministic stub specialists/router replicating
                          each member's ACTUAL result shape (reference for
                          the Phase 2 adapters)
    assembler.py          minimal query/classify flow: validate → route →
                          dispatch → assemble QueryResponse / map errors
    member_interfaces.py  machine-readable record of the members' ACTUAL
                          entry points (Task 1 findings) + compatibility
                          findings
    live_probe.py         read-only compatibility probes that import each
                          member workstream offline and record what their
                          real code actually produces (no member is modified)
    fixtures/             golden-scenario fixtures (machine-readable)
    tests/                Phase 1 integration test harness (pytest):
                          contracts, five golden scenarios, error/fallback
                          paths, compatibility checks

Content-safety note: the stub texts in stubs.py are TEST FIXTURES. Legal
references used in them (e.g. Patents Act Section 3(p), TKDL, PCT) are real
names taken from PS.md / Research.md; the excerpts are explicit placeholders
so that no legal text is fabricated anywhere in the harness.
"""

__version__ = "0.1.0-phase1"

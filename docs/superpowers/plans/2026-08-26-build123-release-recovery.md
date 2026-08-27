# Build123 Release Recovery Implementation Plan

1. Add Build123 regression fixtures and verifier wiring for all reported behaviors.
2. Replace split settings persistence with a per-account canonical store and active-account legacy projection; move writes and archive work off the main thread.
3. Audit and reconnect every Scheduled Send and one-time-media consumer to the canonical projection.
4. Add a versioned portable message snapshot carrying entities, media, grouping, source identity, and timestamps.
5. Reuse the snapshot for deleted recovery, protected forwarding, Forward Without Author, and edit history.
6. Restore custom emoji/text-link entities and real dates in history; retain backward compatibility.
7. Correct profile glass propagation, description expansion fade, Common Groups surface, and Links layout/sizing.
8. Restore Safe/Ghost login for add-account flow and remove only the experimental group/channel Get Link control.
9. Replace legacy internal Settings/Time Machine row composition with shared Jerkgram glass components.
10. Run layer verifiers, full tests, clean Official materialization, identity checks, commit Build123, update the release branch, and start macOS CI.

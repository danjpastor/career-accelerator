# Career Accelerator v10.0.3 Release Notes

## Overview

Career Accelerator v10.0.3 fixes the last Dashboard spacing issue found on shorter or display-scaled screens. The front page still keeps every card and the complete sidebar visible without scrolling, but spare vertical space is now absorbed by the cards themselves instead of appearing as oversized blank bands between Dashboard rows.

## Dashboard layout corrections

- Dashboard row containers now wrap tightly around their cards.
- Available height is distributed through fluid metric, priority, analytics, and footer card heights.
- Responsive row spacing remains fixed at the intended 5, 7, or 10 pixels for the current density mode.
- The primary, secondary, and footer cards no longer float vertically inside enlarged invisible grid hosts.
- Windows display scaling scenarios such as a 1600×960 physical screen rendered as a 1280×768 logical Qt window now retain a continuous, intentionally grouped layout.
- The complete Dashboard and sidebar remain visible without scrolling at all supported sizes.

## Preserved v10 functionality

This update preserves the v10.0.0–v10.0.2 Exercise Pack, SQL editor, routing, Interview Problem evidence, backup, storage, and application-wide responsive layout features.

## Upgrade safety

The cumulative v10.0.3 installer can be applied to v9.6.4 or any v10 build. It validates the selected repository, backs up replaced files, skips identical files, and does not delete the local database, backups, learner submissions, generated DuckDB data, task workspaces, or custom Exercise Packs.

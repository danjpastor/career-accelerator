# Exercise Pack Quality Checklist

Use this checklist before releasing or installing a new pack.

## Identity and packaging

- [ ] `schema_version` is `1`.
- [ ] `pack_id` is lowercase, hyphenated, and stable.
- [ ] `version`, title, author, and description are current.
- [ ] The ZIP contains exactly one `manifest.json`.
- [ ] Every referenced file exists inside the pack.
- [ ] Lesson and exercise IDs are unique.
- [ ] The pack includes a learner-facing `README.md`.

## Course design

- [ ] The pack teaches one coherent concept family.
- [ ] Prerequisites are explicit and realistic.
- [ ] Lessons progress from recognition to application.
- [ ] Exercises ramp gradually rather than jumping in difficulty.
- [ ] The capstone combines previously taught skills.
- [ ] Optional stretch work does not block completion.
- [ ] Estimated minutes are realistic.

## Lesson styling

- [ ] Every lesson has one `#` title.
- [ ] Every manifest lesson entry has a calm subtitle.
- [ ] Major sections use `##`; smaller checkpoints use `###`.
- [ ] Every multi-line code sample is in a labeled fenced code box.
- [ ] Every schema, comparison, and result sample uses a Markdown table.
- [ ] No ASCII-art tables are present.
- [ ] Callouts are concise and use blockquotes.
- [ ] Two-column layouts contain short, balanced content.
- [ ] No embedded HTML/CSS attempts to override application styling.

## Exercise quality

- [ ] Every exercise has one measurable learning objective.
- [ ] The prompt states exact output requirements.
- [ ] Expected result shape includes columns, rows, ordering, and edge cases.
- [ ] Starter SQL helps without solving the task.
- [ ] Build steps are small and testable.
- [ ] Hints become progressively more specific.
- [ ] Common mistakes explain why the mistake fails.
- [ ] Reflection questions check understanding.
- [ ] The official solution has a stage-by-stage walkthrough.

## Datasets

- [ ] Tables and columns use valid `snake_case` SQL identifiers.
- [ ] Early exercises use small, mentally inspectable datasets.
- [ ] Edge cases are intentional and explained.
- [ ] One-to-many relationships are clear.
- [ ] Values are internally consistent.
- [ ] No personally identifying or confidential real-world data is included.

## Validation

- [ ] Every official solution executes successfully.
- [ ] Every official solution passes `Check Answer`.
- [ ] An obviously wrong query fails.
- [ ] Column names and ordering are correct.
- [ ] `ordered` is true only when order matters.
- [ ] Pattern rules verify the taught concept without rejecting harmless alternatives.
- [ ] Read-only SQL restrictions are respected.

## Recommendations

- [ ] `trigger_concepts` uses canonical concept names.
- [ ] Keyword fallbacks are included only where helpful.
- [ ] Suggestion reasons explain relevance clearly.
- [ ] Google course/module mappings are accurate.
- [ ] The pack remains optional and does not alter roadmap completion.

## Installation and update testing

- [ ] ZIP installation succeeds.
- [ ] Folder installation succeeds.
- [ ] The pack appears immediately in the selector and navigation.
- [ ] Lessons render without clipped or malformed content.
- [ ] Learn and Practice remain synchronized.
- [ ] SQL can run and be checked.
- [ ] A version update preserves saved SQL, notes, and completion.
- [ ] SHA-256 checksum is generated for the release archive.

# Exercise Pack Authoring Guide

This guide is the source of truth for creating optional Career Accelerator Exercise Packs that feel like one consistent learning product. It covers structure, pedagogy, visual presentation, task recommendations, SQL validation, versioning, and release testing.

Related references:

- `FORMAT.md` — exact schema and supported fields
- `STYLE_GUIDE.md` — visual and writing standards
- `QUALITY_CHECKLIST.md` — pre-release acceptance checklist
- `templates/standard-pack-template/` — copyable starting structure

## 1. Product purpose

Exercise Packs are **optional supplemental courses**. They help a learner slow down, revisit, or deepen a concept without changing the required roadmap.

Every pack should:

- Teach one coherent concept family.
- Begin at the learner’s actual prerequisite level.
- Explain what the concept is, why it is used, when it is appropriate, and how to recognize it.
- Provide small exercises that increase difficulty gradually.
- Keep Learn and Practice content synchronized.
- Use the standard course-site presentation supplied by the application.
- Be installable from a folder or one `.zip` file without editing configuration files.
- Preserve learner progress when updated under the same `pack_id`.

Do not design a pack as a loose collection of quiz questions. It should feel like a short, intentional course.

## 2. Standard application layout

The application owns the shell and visual chrome. Pack authors supply structured content.

The Exercises page permanently displays:

```text
[ Course navigation ] [ Learn card ] [ Practice card ]
```

### Course navigation

The app renders the pack title, lesson/exercise sequence, completion states, overview, and progress. Authors control the order through `manifest.json`.

### Learn card

The app renders a native course page with:

- Compact content-type pill
- Large calm title
- Subtle outlined subtitle label
- Quiet divider
- Responsive sections, code cards, callouts, and tables
- Bookmark and navigation controls

### Practice card

The app renders the exercise prompt, starter SQL, hints, execution results, answer checker, notes, solution walkthrough, and completion state from the exercise JSON.

Do not reproduce application navigation, tabs, buttons, or progress bars inside lesson Markdown.

## 3. Recommended course structure

A polished concept pack normally contains:

- 5–8 lessons
- 8–14 exercises
- 1–3 exercises per major concept
- Small datasets that can be understood without external documentation
- A capstone that combines earlier skills without introducing several new ideas at once

A reliable learning progression is:

1. **Recognize** — identify the concept and its parts.
2. **Predict** — determine result shape or behavior before running code.
3. **Complete** — fill in a nearly finished example.
4. **Construct** — write the pattern from a prompt.
5. **Compare** — distinguish related approaches and choose deliberately.
6. **Debug** — diagnose common mistakes.
7. **Apply** — solve a realistic multi-step problem.

Do not jump from a definition directly to a capstone.

## 4. Lesson blueprint

Use this order when it fits the topic:

1. `#` lesson title
2. One-paragraph plain-language definition
3. Two-column row with Learning Goals and a representative code example
4. Two-column row with Example Result and Key Idea
5. Major concept sections using `##`
6. Comparison or schema tables
7. Common mistakes or warnings
8. A short checkpoint or restatement

Example:

````markdown
# One Clear Concept

A short definition written for the learner’s current level.

:::columns
:::column
> **Learning Goals:**
> ✓ First measurable goal.
> ✓ Second measurable goal.
:::column
```sql
SELECT ...;
```
:::

:::columns
:::column
## Example Result

| column | value |
|---|---:|
| example | 10 |
:::column
> **Key Idea:** One sentence stating the mental model.
:::
````

The first screenful should orient the learner quickly. Avoid opening with a long wall of text.

## 5. Exercise blueprint

Every exercise should have one primary learning objective. Use the supported JSON fields to provide:

- Stage and subtitle
- Difficulty and estimated time
- Concepts
- Learning objective
- Recommended lesson
- Why the pattern matters
- Exact prompt
- Expected output shape
- Small construction steps
- Mental-model explanation
- Common mistakes
- Progressive hints
- Takeaways
- Reflection questions
- Optional stretch goal
- Starter SQL
- Datasets
- Official solution
- Solution explanation and walkthrough
- Result and pattern validation

The learner should understand what “done” means without opening the solution.

### Hint progression

Hints should become gradually more specific:

1. Restate the relevant mental model.
2. Name the SQL clause or relationship needed.
3. Reveal the most difficult fragment without providing the full query.

Do not make Hint 1 the complete answer.

### Solution walkthrough

Explain the query in execution or reasoning stages. A strong walkthrough answers:

- What does the starting table represent?
- What does each clause add or remove?
- What is the intermediate result shape?
- Why does the final query answer the business question?

## 6. Dataset design

Datasets should be intentionally small and educational.

Prefer:

- 4–12 rows per table for early exercises
- Clear lowercase `snake_case` columns
- Stable integer IDs
- A few deliberate edge cases
- Values that are easy to inspect mentally
- Reuse across related exercises when it reinforces a coherent model

Include edge cases only when the lesson explains them. Examples include:

- A missing foreign key
- An entity with zero related rows
- A one-to-many relationship
- A duplicate-looking but legitimate detail row
- An unmatched record on either side of a reconciliation

Avoid random synthetic noise that distracts from the concept.

## 7. Visual and content preferences

The app controls colors, fonts, borders, hover states, and responsive behavior. Pack files should use semantic Markdown rather than embedded HTML or CSS.

Non-negotiable presentation preferences:

- Every multi-line code sample goes in a fenced code block with a language label.
- Every comparison, schema, or sample result uses a Markdown table—not ASCII borders.
- Lesson headers use the app’s pill + title + subtle subtitle treatment.
- Section headers remain calm and readable; do not write entire headings in all caps.
- Use blockquotes for goals, key ideas, warnings, and checkpoints.
- Use `:::columns` only for two closely related, reasonably short pieces of content.
- Keep paragraphs short enough to scan.
- Use backticks for SQL keywords, columns, tables, aliases, and short expressions.
- Avoid decorative emoji in lesson headings; the application already supplies visual cues.

See `STYLE_GUIDE.md` for detailed examples.

## 8. Recommendation metadata

Use canonical task concepts whenever possible. They are more reliable than title keywords.

For SQL packs, common concepts include:

- `sql_joins`
- `sql_subqueries`
- `sql_ctes`
- `sql_window_functions`
- `sql_aggregations`

A pack can include task-keyword fallbacks, but exact concept tags should receive the higher score.

When a pack supports a specific Google Certificate location, add a focused rule with `google_course_any` and `google_module_any` plus the concept tag. The reason should explain why the optional pack is relevant.

Suggestions remain live and optional. They should not imply that the roadmap task is incomplete merely because the pack is unfinished.

## 9. Validation design

Result validation is the foundation. Pattern rules should verify the concept only when the exercise explicitly requires it.

Good uses:

- Require `left join` in an exercise practicing preservation.
- Require `is null` in a left anti-join exercise.
- Require two `SELECT` statements in a subquery exercise.
- Forbid `not exists` when the exercise specifically teaches the left-join anti-pattern.

Avoid overconstraining valid syntax:

- Do not require `AS` for aliases.
- Do not require one exact whitespace style.
- Do not forbid a harmless alternative unless choosing between approaches is the lesson objective.

Every official solution must pass its own checker.

## 10. Versioning and updates

- Keep `pack_id` stable forever.
- Increase `version` when content changes.
- Keep lesson and exercise IDs stable when they represent the same learner progress item.
- Add new IDs for genuinely new items.
- Do not recycle an old ID for a different skill.

The installer replaces pack content but stores SQL, notes, and progress separately. Stable IDs allow that progress to survive updates.

Suggested versioning:

- Patch: wording, styling, or answer-check fixes
- Minor: new lessons/exercises or meaningful instructional expansion
- Major: incompatible redesign of the pack’s learning sequence

## 11. Installation testing

Test both supported installation paths before release.

### ZIP test

1. Create one archive containing exactly one `manifest.json`.
2. Open **Learning → Exercises**.
3. Choose **Install Exercise Pack…**.
4. Confirm the pack appears immediately.
5. Open a lesson and exercise.
6. Run and check at least one answer.

### Folder test

1. Extract the archive.
2. Choose **Install Folder…**.
3. Select the folder containing `manifest.json`.
4. Confirm installation or update succeeds.

### Update test

1. Complete or edit an exercise.
2. Install a newer version with the same `pack_id`.
3. Confirm the new content appears.
4. Confirm saved SQL, notes, and completion state remain.

## 12. Release contents

A release should include:

- Installable `.exercise-pack.zip`
- Source folder or extractable archive
- `README.md` with install and course overview
- Version and author in `manifest.json`
- All official solutions
- Validation/test report
- SHA-256 checksum

Use `QUALITY_CHECKLIST.md` before publishing.

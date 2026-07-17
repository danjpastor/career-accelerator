# Exercise Pack Style and Layout Guide

This guide defines how authored content should look and read inside Career Accelerator. The application supplies the visual components; authors use consistent semantic Markdown and concise instructional writing.

## Header hierarchy

### Page header

The app renders:

1. Content-type pill such as **LESSON** or **GUIDED EXERCISE**
2. Large page title
3. Subtle outlined subtitle label
4. Quiet horizontal divider

Author preferences:

- Title: clear concept name, usually 3–8 words
- Subtitle: one calm sentence fragment describing the learner’s next move
- Avoid punctuation-heavy or marketing-style titles
- Avoid all-caps titles

Good:

```text
INNER JOIN: Keep the Matches
Return only rows that find a partner
```

Avoid:

```text
MASTER INNER JOINS NOW!!!
THE ULTIMATE GUIDE
```

### Section headers

- `##` for major lesson sections
- `###` for smaller stages or checkpoints
- Let the application draw the divider; do not type repeated hyphens beneath headings
- Use sentence case

## Code boxes

Every multi-line code sample must use a fenced block with an explicit language.

````markdown
```sql
SELECT customer_id, customer_name
FROM customers
ORDER BY customer_id;
```
````

The app adds:

- Code-card background
- Language label
- Line numbers
- Syntax highlighting
- Copy button

Do not use indented code, raw HTML `<pre>` tags, or plain paragraphs for multi-line SQL.

Use inline code for short identifiers and expressions:

```markdown
Match `customers.region_id` to `regions.region_id`.
```

## Tables

Use Markdown tables for schemas, comparisons, and result samples.

```markdown
| Join type | Preserved rows | Common use |
|---|---|---|
| `INNER JOIN` | Matches only | Related records |
| `LEFT JOIN` | Every left row | Complete entity list |
```

The app adds the polished header band, alternating rows, spacing, alignment, and separators.

Table preferences:

- 2–5 columns when possible
- Short cell content
- Right-align numeric columns using `---:`
- Put SQL identifiers in backticks
- Split a very wide table into two smaller tables
- Do not use ASCII borders
- Do not paste raw dataframe output as monospaced text when a table communicates it better

## Callout cards

Use a blockquote for one focused idea.

```markdown
> **Key Idea:** A `LEFT JOIN` preserves every row from the table written on the left.
```

Recommended labels:

- Learning Goals
- Key Idea
- Why It Matters
- Warning
- Debugging Checkpoint
- First Survival Rule

Keep a callout to one short paragraph or a compact checklist. Do not put the entire lesson in blockquotes.

## Two-column rows

Use the supported directive for related content that benefits from comparison.

````markdown
:::columns
:::column
> **Learning Goals:**
> ✓ Identify the preserved table.
> ✓ Predict unmatched rows.
:::column
```sql
SELECT ...
```
:::
````

Best uses:

- Learning Goals + representative code
- Result table + Key Idea
- Two short comparison cards

Avoid:

- Two long narrative sections
- Wide tables in both columns
- Deeply nested directives
- More than two columns

The layout must still make sense when the center Learn card is narrower.

## Paragraphs and lists

- Prefer 1–4 sentences per paragraph
- Use numbered lists for a sequence
- Use bullets for unordered examples
- Bold the first term when defining it
- Use one blank line between Markdown blocks
- Keep list items parallel in grammar

## Tone

Write as a calm instructor—not a textbook and not a motivational advertisement.

Preferred:

- Plain language first, terminology second
- Direct explanation of why a pattern works
- Explicit result-shape and grain language
- Realistic analyst use cases
- Honest warnings about common mistakes

Avoid:

- “Simply,” “obviously,” or language that minimizes difficulty
- Dense jargon before definition
- Large unexplained code dumps
- Trick questions
- Artificial urgency

## Exercise presentation

Exercise fields appear in the Practice card. Keep each field focused:

- `learning_objective`: one measurable skill
- `why`: one analyst-facing reason
- `prompt`: exact deliverable
- `expected_result`: columns, row count, order, and notable edge cases
- `build_steps`: 3–6 small actions
- `common_mistakes`: likely errors plus why they fail
- `hints`: progressive specificity
- `takeaways`: 1–3 durable ideas
- `reflection_questions`: explanation questions, not trivia
- `stretch_goal`: optional and clearly outside completion requirements

## Practice-question and starter-template style

- Write one direct deliverable per question.
- Put required columns, row count, ordering, and edge cases in `expected_result` rather than hiding them in hints.
- Keep question titles action-oriented and distinguish multiple questions within the same lesson.
- Use progressive hints: concept first, structure second, implementation detail last.
- Keep `starter_sql` visibly incomplete. Comments and placeholders are appropriate; completed predicates, joins, grouping, nested-query logic, and copied lesson examples are not.
- Do not use the starter editor as another teaching example. Teaching examples belong in Learn; learner construction belongs in Practice.
- Ensure the Practice card remains understandable without opening View Solution.

## Accessibility and responsiveness

- Do not rely on color alone to communicate meaning
- Use explicit labels such as Matched, Missing, or Completed
- Keep code lines reasonably short
- Avoid tables that require excessive horizontal width
- Use descriptive headings so screen scanning remains meaningful
- Do not embed tiny images containing instructional text
- Do not hard-code colors or fonts in pack content

## Visual consistency checklist

A lesson is visually ready when:

- It has one `#` title
- The manifest supplies a concise subtitle
- All multi-line code is fenced and labeled
- All tabular information is a Markdown table
- Major sections use `##`
- Callouts are brief and purposeful
- Two-column rows are balanced
- There are no embedded HTML styles
- The first screenful explains the goal and shows one concrete example

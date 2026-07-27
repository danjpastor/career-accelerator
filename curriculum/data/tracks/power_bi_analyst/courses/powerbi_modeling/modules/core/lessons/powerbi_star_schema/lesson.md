# Star and Snowflake Schemas

A **star schema** places a fact table at the center and connects it directly to descriptive dimensions. The shape is simple, which helps Power BI filter efficiently and helps analysts understand where each field belongs.

## Main idea

A **star schema** places a fact table at the center and connects it directly to descriptive dimensions. The shape is simple, which helps Power BI filter efficiently and helps analysts understand where each field belongs.

A **snowflake schema** splits a dimension into additional related tables. Snowflaking can reduce repeated descriptive data, but it also adds relationships and makes the model harder for beginners to follow. For reporting, a clean star schema is often the better starting point.

Measures should normally aggregate values from the fact table, while labels and slicers come from dimensions.

## Example

A retail model uses `Sales Lines` as the fact table and connects it to Product, Store, Customer, and Date dimensions. Quantity and line revenue stay in the fact table. Product category and brand stay in Product. A report can then group the fact values by any descriptive dimension without merging everything into one wide table.

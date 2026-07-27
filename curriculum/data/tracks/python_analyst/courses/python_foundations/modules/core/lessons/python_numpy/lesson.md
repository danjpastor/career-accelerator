# NumPy Arrays

NumPy stores numeric values in an **array**. Arrays look similar to lists, but they are designed for fast, consistent calculations across many values.

## Main idea

NumPy stores numeric values in an **array**. Arrays look similar to lists, but they are designed for fast, consistent calculations across many values.

```python
import numpy as np
scores = np.array([82, 91, 76])
score_average = scores.mean()
```

A comparison such as `scores >= 80` creates a Boolean mask. Using that mask inside brackets keeps only the matching values. This is called vectorized work because one expression operates across the whole array.

## Example

A quality analyst stores inspection measurements in an array, calculates the mean, and filters values outside the accepted range. They do not need to write a loop for each measurement. The graded exercise uses order values.

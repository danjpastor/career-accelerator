# Creating and Visualizing DataFrames

A useful chart begins with a clear question and chart-ready data. Usually you summarize or filter the DataFrame first, then plot the smaller result.

## Main idea

A useful chart begins with a clear question and chart-ready data. Usually you summarize or filter the DataFrame first, then plot the smaller result.

Bar charts compare categories, line charts show change over time, histograms show a numeric distribution, and scatter plots compare two numeric measures. Labels and sorting should help the reader understand the result without guessing.

pandas plotting returns a Matplotlib axes object. Saving that object in a variable lets you adjust labels or inspect the chart later.

## Example

A service analyst groups ticket count by channel, sorts the summary, and creates a horizontal bar chart. They use channel names as labels and ticket count as the numeric axis. The graded exercise prepares and charts regional order totals.

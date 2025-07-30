# iy
Includes functions to diagnose duplicates in adwords elements

To install:	```pip install iy```

## Overview

The `iy` package provides a suite of tools designed to help diagnose and manage duplicate entries in AdWords campaigns. It includes functions for identifying duplicates based on various criteria such as keyword text transformations (stripping, lowercasing, ASCII conversion) and grouping by attributes like match type, ad group, or campaign. The package leverages pandas and numpy for data manipulation and analysis, ensuring efficient processing of large datasets.

## Main Features

- **Keyword Duplicate Diagnosis**: Identify duplicate keywords in your AdWords data, allowing for different levels of text normalization (e.g., stripping whitespace, converting to lowercase, ASCII encoding).
- **Statistical Analysis**: Generate statistics about duplicates, including counts and ratios of duplicates, which can be broken down by type (e.g., exact, stripped, lowercase).
- **Grouping and Aggregation**: Group data by specified keys and calculate duplication metrics for these groups.
- **Unicode Handling**: Convert all keyword strings to Unicode to ensure consistency in text processing.

## Usage Examples

### Diagnosing Keyword Duplicates

To diagnose duplicates in a DataFrame containing AdWords data, you can use the `kw_dup_diagnosis` function. This function allows customization of grouping keys and duplication definitions.

```python
import pandas as pd
from iy import kw_dup_diagnosis

# Sample DataFrame
data = {
    'keyword': ['example', 'example ', 'Example', 'sample', 'sample'],
    'match_type': ['Exact', 'Exact', 'Broad', 'Broad', 'Exact'],
    'ad_group': ['Group1', 'Group1', 'Group2', 'Group1', 'Group2'],
    'campaign': ['Campaign1', 'Campaign1', 'Campaign1', 'Campaign2', 'Campaign2']
}
df = pd.DataFrame(data)

# Diagnose duplicates
dup_info = kw_dup_diagnosis(df)
print(dup_info)
```

### Generating Statistics for Duplicate Diagnosis

After diagnosing duplicates, you may want to generate general statistics to understand the extent of duplication:

```python
from iy import general_stats_for_dup_diag

# Assuming `dup_info` is obtained from `kw_dup_diagnosis`
stats = general_stats_for_dup_diag(dup_info)
print(stats)
```

### Advanced Duplicate Handling

For more complex scenarios, such as handling different types of duplicates across multiple dimensions (e.g., campaign and ad group), you can use the `get_kw_duplicates_01` function:

```python
from iy import get_kw_duplicates_01

# Get keyword duplicates with specific definitions
dup_details = get_kw_duplicates_01(df, dup_def='kw_lower', gr_keys=['match_type', 'ad_group', 'campaign'])
print(dup_details)
```

## Function Documentation

- **`kw_dup_diagnosis(df, grp_keys, grp_fun_dict, grp_id_name, grp_id_type, output_nondup_df)`**: Analyzes a DataFrame for keyword duplicates based on specified grouping keys and duplication definitions. It returns a DataFrame with duplication information or optionally a tuple containing both the DataFrame with duplicates and the DataFrame without duplicates.

- **`general_stats_for_dup_diag(diag_df, n_taps, n_broad_taps, dup_types)`**: Computes and returns a dictionary of statistics about duplicates in the provided DataFrame. It can return the statistics along with the diagnostic DataFrame if the input DataFrame was not pre-diagnosed.

- **`get_kw_duplicates_01(df, dup_def, gr_keys)`**: An older function for obtaining keyword duplicates based on a specified definition of duplication (e.g., lowercased keywords). It supports merging results from different duplication criteria.

These functions are designed to be flexible and integrate easily into data processing pipelines for digital marketing analysis, especially for managing and optimizing Google AdWords campaigns.
pip install reduce-mem-usage

import pandas as pd
from reduce_mem_usage import reduce_mem_usage

# Example: load a DataFrame
df = pd.read_csv("data.csv")

# Reduce memory usage
df = reduce_mem_usage(df)

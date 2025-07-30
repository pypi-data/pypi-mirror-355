# __init__.py

# This makes the profile_df function available directly when someone imports the package
# So they can do `from eda_profiler import profile_df`
# instead of `from eda_profiler.profiler import profile_df`

from .profiler import profile_df

# You can also define package-level metadata here
__version__ = "0.1.0"
__author__ = "Dinesh Kumar"
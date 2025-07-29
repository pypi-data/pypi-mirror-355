import sys

if sys.version_info.major < 3:
    raise ValueError("Incompatible with Python2")


version = "1.0.5"
compatible_versions = ("1.0.5",)

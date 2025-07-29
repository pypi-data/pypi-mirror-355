from os import getenv, cpu_count
from pathlib import Path
import psutil
import platform

# VIZITIG_TMP_DIR:
#   directory to store temp files, Default None
VIZITIG_TMP_DIR = getenv("VIZITIG_TMP_DIR")

# VIZITIG_PROC_NUMBER:
#   default number of shard when building index,
#   default  min(cpu_c - 1, 10) where cpu_c is the CPU_COUNT

if getenv("VIZITIG_PROC_NUMBER"):
    VIZITIG_PROC_NUMBER = int(str(getenv("VIZITIG_PROC_NUMBER")))
else:
    cpu_c = cpu_count()
    if cpu_c is not None:
        VIZITIG_PROC_NUMBER = min(cpu_c - 1, 10)
    else:
        VIZITIG_PROC_NUMBER = 4

if getenv("VIZITIG_WORK_MEM"):
    VIZITIG_WORK_MEM = int(str(getenv("VIZITIG_WORK_MEM")))
else:
    VIZITIG_WORK_MEM = int(0.6 * psutil.virtual_memory().total)


# VIZITIG_DIR:
#   directory where to store vizitig data, default ~/.vizitig

VIZITIG_DIR = Path(getenv("VIZITIG_DIR", "~/.vizitig")).expanduser()


# VIZITIG_PYTHON_ONLY:
#   use only Python types and do not try to use vizibridge, default False

VIZITIG_PYTHON_ONLY = getenv("VIZITIG_PYTHON_ONLY", False)


# VIZITIG_DEFAULT_INDEX:
#   set the default index to use in vizitig. Default False
#   if not set, vizitig will choose one.

VIZITIG_DEFAULT_INDEX = getenv("VIZITIG_DEFAULT_INDEX")

# VIZITIG_NO_TMP_INDEX:
#   if set, will build temporary index

VIZITIG_NO_TMP_INDEX = False
if getenv("VIZITIG_NO_TMP_INDEX"):
    VIZITIG_NO_TMP_INDEX = True

# VIZITIG_SHORT_TEST:
#   if set, will do less test

VIZITIG_SHORT_TEST = False
if getenv("VIZITIG_SHORT_TEST"):
    VIZITIG_SHORT_TEST = True

# VIZITIG_NO_PARALLEL_INDEX:
#   if set, do not build the index using python multiprocessing
#   default False for linux and True for the rest

VIZITIG_NO_PARALLEL_INDEX = True
if platform.system() == "Linux":
    VIZITIG_NO_PARALLEL_INDEX = False
if getenv("VIZITIG_NO_PARALLEL_INDEX"):
    VIZITIG_NO_PARALLEL_INDEX = True

from multiprocessing import cpu_count
from os import name as os_name


def get_max_threads() -> int:
    """
Returns the maximum number of threads to use for multiprocessing since multiprocessing shits itself on Windows with more
than 61 threads because for some fucking reason, three are always in use (cries in Threadripper)"""

    if cpu_count() >= 64 and os_name == "nt":
        return 61

    return cpu_count()

try:
    import pydevd_pycharm
except ImportError:
    pydevd_pycharm = None


def dbg(suspend: bool = True) -> None:
    if pydevd_pycharm is None:
        raise ImportError("pydevd_pycharm not found. Make sure you have the `pydevd-pycharm` package installed.")
    pydevd_pycharm.settrace("localhost", port=42000, stdoutToServer=True, stderrToServer=True, suspend=suspend)

from ._gunsan_formula import _compute_strength

def get_gunsan_strength(df,signal_window):
    """
    Public API to compute GunSan Strength Index.
    """
    return _compute_strength(df,signal_window)
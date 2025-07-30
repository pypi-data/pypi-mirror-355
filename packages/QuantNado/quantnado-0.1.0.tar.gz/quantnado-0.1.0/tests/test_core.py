import pandas as pd
from QuantNado.core import call_quantile_peaks

def test_call_quantile_peaks_basic():
    # Toy signal with a clear high value
    signal = pd.Series([0, 1, 5, 10, 1, 0], name="test_sample")
    chroms = pd.Series(["chr1"] * 6)
    starts = pd.Series([0, 100, 200, 300, 400, 500])
    ends = pd.Series([100, 200, 300, 400, 500, 600])

    # Call peaks with quantile that should include only the top (10)
    peaks = call_quantile_peaks(
        signal=signal,
        chroms=chroms,
        starts=starts,
        ends=ends,
        tilesize=100,
        quantile=0.95,
        min_peak_length=100,
        blacklist_file=None,
    )

    assert peaks is not None
    assert len(peaks) == 1
    peak_df = peaks.df
    assert peak_df.iloc[0]["Start"] == 300
    assert peak_df.iloc[0]["End"] == 400

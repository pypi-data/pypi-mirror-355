import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import pyranges as pr
from crested import import_bigwigs
from loguru import logger

logger.add(sys.stderr, level="INFO", format="{time} [{level}] {message}")


def call_quantile_peaks(
    signal: pd.Series,
    chroms: pd.Series,
    starts: pd.Series,
    ends: pd.Series,
    tilesize: int = 128,
    quantile: float = 0.98,
    min_peak_length: Optional[int] = None,
    blacklist_file: Optional[Path] = None,
    merge: bool = True,
) -> Optional[pr.PyRanges]:
    logger.info(f"Calling peaks for sample: {signal.name}")
    if min_peak_length is None:
        min_peak_length = 3 * tilesize
        logger.debug(
            f"No min_peak_length provided, using 3 * tilesize = {min_peak_length}"
        )

    nonzero = signal[signal > 0]
    if nonzero.empty:
        logger.warning(f"[{signal.name}] No nonzero signal values.")
        return None

    threshold = nonzero.quantile(quantile)
    logger.debug(f"[{signal.name}] Quantile {quantile} threshold = {threshold:.4f}")
    peaks = signal >= threshold

    peaks_df = pd.DataFrame(
        {
            "Chromosome": chroms,
            "Start": starts,
            "End": ends,
            "Score": signal,
            "peak": peaks.astype(int),
        }
    )
    peaks_df = peaks_df[peaks_df["peak"] == 1].drop(columns="peak")
    if peaks_df.empty:
        logger.warning(f"[{signal.name}] No peaks above threshold.")
        return None

    peaks_df = peaks_df.astype({"Start": int, "End": int, "Chromosome": str})
    peaks_df = peaks_df.sort_values(["Chromosome", "Start"]).reset_index(drop=True)

    pr_obj = pr.PyRanges(peaks_df).merge() if merge else pr.PyRanges(peaks_df)
    pr_obj = pr_obj[pr_obj.lengths() >= min_peak_length]
    logger.info(f"[{signal.name}] Retained {len(pr_obj)} peaks ≥ {min_peak_length} bp")

    if blacklist_file and blacklist_file.exists():
        logger.debug(f"[{signal.name}] Subtracting blacklist regions: {blacklist_file}")
        blacklist = pr.read_bed(str(blacklist_file))
        pr_obj = pr_obj.subtract(blacklist)
        logger.info(f"[{signal.name}] {len(pr_obj)} peaks after blacklist removal")

    return pr_obj if len(pr_obj) > 0 else None


def call_peaks_from_bigwig(
    bigwig_file: str,
    output_dir: str,
    chromsizes_file: str,
    blacklist_file: Optional[str] = None,
    tilesize: int = 128,
    quantile: float = 0.98,
    min_peak_length: Optional[int] = None,
    tmp_dir: str = "tmp",
) -> Optional[str]:
    bigwig_path = Path(bigwig_file)
    output_path = Path(output_dir)
    chromsizes_path = Path(chromsizes_file)
    blacklist_path = Path(blacklist_file) if blacklist_file else None
    tmp_path = Path(tmp_dir)

    tmp_path.mkdir(parents=True, exist_ok=True)
    output_path.mkdir(parents=True, exist_ok=True)
    sample_name = bigwig_path.name.rsplit(".", 1)[0]
    log_file = output_path / f"{sample_name}_peak_calling.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    log_sink_id = logger.add(
        log_file, level="DEBUG", format="{time} [{level}] {message}"
    )

    try:
        logger.info(f"Processing sample: {sample_name}")

        chromsizes = (
            pd.read_csv(chromsizes_path, sep="\t", names=["Chromosome", "End"])
            .query("~Chromosome.str.contains('_')", engine="python")
            .assign(Start=0)[["Chromosome", "Start", "End"]]
        )

        logger.info("Tiling genome...")
        tiled = pr.PyRanges(chromsizes).tile(tilesize)

        if blacklist_path and blacklist_path.exists():
            logger.info(f"Applying blacklist from: {blacklist_path}")
            blacklist = pr.read_bed(str(blacklist_path))
            tiled = tiled.subtract(blacklist)

        tiled_df = tiled.df.sort_values(["Chromosome", "Start"])

        tmp_regions_bed = tmp_path / f"{sample_name}_tiled.bed"
        tiled.to_bed(tmp_regions_bed)
        logger.debug(f"Tiled regions written to {tmp_regions_bed}")

        logger.info(f"Reading signal from: {bigwig_path}")
        adata = import_bigwigs(
            regions_file=str(tmp_regions_bed),
            bigwigs_folder=str(bigwig_path.parent),
            chromsizes_file=str(chromsizes_path),
            target="mean",
        )
        signal = np.log1p(adata.X[:, 0])

        pr_obj = call_quantile_peaks(
            signal=pd.Series(signal, name=sample_name),
            chroms=tiled_df["Chromosome"],
            starts=tiled_df["Start"],
            ends=tiled_df["End"],
            tilesize=tilesize,
            quantile=quantile,
            min_peak_length=min_peak_length,
            blacklist_file=blacklist_path,
        )

        if pr_obj is not None:
            output_bed = output_path / f"{sample_name}.bed"
            pr_obj.to_bed(output_bed)
            logger.success(f"[{sample_name}] Peaks written to: {output_bed}")
            return str(output_bed)
        else:
            logger.warning(f"[{sample_name}] No peaks detected.")
            return None

    except Exception as e:
        logger.exception(f"[{sample_name}] Peak calling failed due to an error: {e}")
        return None

    finally:
        logger.remove(log_sink_id)

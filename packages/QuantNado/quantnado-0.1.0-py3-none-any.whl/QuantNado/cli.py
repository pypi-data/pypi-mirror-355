import argparse
import sys

from loguru import logger

from .core import call_peaks_from_bigwig


def main():
    parser = argparse.ArgumentParser(
        description="Call quantile-based peaks from a bigWig file."
    )
    parser.add_argument("--bigwig", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--chromsizes", required=True)
    parser.add_argument("--blacklist", default=None)
    parser.add_argument("--tilesize", type=int, default=128)
    parser.add_argument("--quantile", type=float, default=0.98)
    parser.add_argument("--min-peak-length", type=int, default=None)
    parser.add_argument("--tmp-dir", default="tmp")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose (DEBUG) logging"
    )
    args = parser.parse_args()

    # 🔧 Configure loguru level
    logger.remove()
    logger.add(sys.stderr, level="DEBUG" if args.verbose else "INFO")

    result = call_peaks_from_bigwig(
        bigwig_file=args.bigwig,
        output_dir=args.output_dir,
        chromsizes_file=args.chromsizes,
        blacklist_file=args.blacklist,
        tilesize=args.tilesize,
        quantile=args.quantile,
        min_peak_length=args.min_peak_length,
        tmp_dir=args.tmp_dir,
    )

    if result:
        logger.success(f"Peak BED saved to: {result}")
    else:
        logger.warning("No peaks were called.")

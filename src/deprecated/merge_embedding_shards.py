import argparse
import glob
import os
import numpy as np


def discover_shards(input_dir: str, prefix: str):
    pattern = os.path.join(input_dir, f"{prefix}*.npy")
    shard_paths = sorted(glob.glob(pattern))
    if not shard_paths:
        raise FileNotFoundError(f"No shard files found with pattern: {pattern}")
    return shard_paths


def inspect_shards(shard_paths):
    dtype = None
    dim = None
    total_rows = 0

    for shard_path in shard_paths:
        arr = np.load(shard_path, mmap_mode="r")
        if arr.ndim != 2:
            raise ValueError(f"Shard is not 2D: {shard_path}, shape={arr.shape}")

        if dtype is None:
            dtype = arr.dtype
            dim = arr.shape[1]
        else:
            if arr.dtype != dtype:
                raise ValueError(
                    f"Inconsistent dtype in {shard_path}: {arr.dtype} != {dtype}"
                )
            if arr.shape[1] != dim:
                raise ValueError(
                    f"Inconsistent embedding dim in {shard_path}: {arr.shape[1]} != {dim}"
                )

        total_rows += arr.shape[0]

    return dtype, dim, total_rows


def merge_shards(shard_paths, output_path, dtype, dim, total_rows):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    merged = np.lib.format.open_memmap(
        output_path,
        mode="w+",
        dtype=dtype,
        shape=(total_rows, dim),
    )

    cursor = 0
    for shard_path in shard_paths:
        arr = np.load(shard_path, mmap_mode="r")
        rows = arr.shape[0]
        merged[cursor : cursor + rows] = arr
        cursor += rows

    merged.flush()


def main():
    parser = argparse.ArgumentParser(
        description="Merge sharded review embedding .npy files into one .npy file"
    )
    parser.add_argument(
        "--input-dir",
        default="data/processed",
        help="Directory containing review embedding shard files",
    )
    parser.add_argument(
        "--prefix",
        default="review_embeddings.part",
        help="Shard prefix, e.g. review_embeddings.part",
    )
    parser.add_argument(
        "--output",
        default="review_embeddings.npy",
        help="Output merged filename or absolute path",
    )
    parser.add_argument(
        "--meta-path",
        default="data/processed/meta_embeddings.npy",
        help="Optional meta embeddings path for reference checks",
    )

    args = parser.parse_args()

    output_path = (
        args.output
        if os.path.isabs(args.output)
        else os.path.join(args.input_dir, args.output)
    )

    shard_paths = discover_shards(args.input_dir, args.prefix)
    print("Found shards:")
    for p in shard_paths:
        print(f"  - {p}")

    dtype, dim, total_rows = inspect_shards(shard_paths)
    print(f"Shard dtype: {dtype}")
    print(f"Embedding dim: {dim}")
    print(f"Total review rows after merge: {total_rows}")

    merge_shards(shard_paths, output_path, dtype, dim, total_rows)

    merged = np.load(output_path, mmap_mode="r")
    print(f"Merged output: {output_path}")
    print(f"Merged shape: {merged.shape}, dtype: {merged.dtype}")

    if args.meta_path and os.path.exists(args.meta_path):
        meta = np.load(args.meta_path, mmap_mode="r")
        print(f"Meta embeddings shape: {meta.shape}, dtype: {meta.dtype}")


if __name__ == "__main__":
    main()

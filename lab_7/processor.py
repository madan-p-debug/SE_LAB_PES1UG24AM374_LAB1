import math
import re

_QUOTA_RE = re.compile(r"(\d+)\s*(MB|GB|TB)", re.ASCII)


def parse_storage_quota(quota_str):
    """
    Parses storage quota string with unit suffix into Gigabytes (GB).
    Assumes format: '<digits><2-letter unit>' (e.g. '500MB', '20GB', '2TB').
    Returns None for invalid input instead of raising.
    """
    if not isinstance(quota_str, str):
        return None
    match = _QUOTA_RE.fullmatch(quota_str.strip().upper())
    if match is None:
        return None
    value = int(match.group(1))
    unit = match.group(2)
    multipliers = {
        "MB": 0.001,
        "GB": 1.0,
        "TB": 1000.0
    }
    gb_total = value * multipliers[unit]
    return f"Quota: {gb_total:.2f} GB"


def compute_compression_ratio(size_metric_str):
    """
    Computes compression ratio: raw_bytes / compressed_bytes.
    Assumes format: 'raw_bytes:compressed_bytes' (e.g. '1024:256').
    Returns None for invalid input instead of raising.
    """
    if not isinstance(size_metric_str, str):
        return None
    parts = size_metric_str.split(':')
    if len(parts) != 2:
        return None
    try:
        raw_bytes = float(parts[0])
        comp_bytes = float(parts[1])
    except ValueError:
        return None
    if not (math.isfinite(raw_bytes) and math.isfinite(comp_bytes)):
        return None
    if raw_bytes < 0 or comp_bytes <= 0:
        return None
    ratio = raw_bytes / comp_bytes
    if not math.isfinite(ratio):
        return None
    return round(ratio, 2)


def lookup_bandwidth_tier_rate(tier_descriptor):
    """
    Looks up rate per GB for egress traffic using the first 3 letters of the tier name.
    Assumes standard tier prefix with at least 3 letters.
    Returns None for invalid or unknown tiers instead of raising.
    """
    if not isinstance(tier_descriptor, str):
        return None
    prefix = tier_descriptor.strip().upper()[:3]
    tier_rates = {
        "HOT": 0.08,
        "COL": 0.05,
        "ARC": 0.02
    }
    return tier_rates.get(prefix)


def main():
    print("==== Running parse_storage_quota ====")
    q_input = input("Enter quota (e.g. 500MB, 10GB, 2TB): ")
    result = parse_storage_quota(q_input)
    print(result if result is not None else "Invalid quota format.")

    print("\n==== Running compute_compression_ratio ====")
    c_input = input("Enter raw:compressed bytes (e.g. 1024:256): ")
    ratio = compute_compression_ratio(c_input)
    print("Compression Ratio:", ratio if ratio is not None else "Invalid input.")

    print("\n==== Running lookup_bandwidth_tier_rate ====")
    t_input = input("Enter tier descriptor (e.g. HOT_TIER, COLD, ARCHIVE): ")
    rate = lookup_bandwidth_tier_rate(t_input)
    print("Rate per GB: $", rate if rate is not None else "Unknown tier.")


if __name__ == "__main__":
    main()

import argparse
from datetime import datetime, timedelta
from .core import simulate_hmi_interaction


def parse_duration(duration_str):
    """Convert 30s, 2m, 1h into a timedelta."""
    units = {'s': 'seconds', 'm': 'minutes', 'h': 'hours'}
    try:
        value = int(duration_str[:-1])
        unit = duration_str[-1].lower()
        if unit not in units:
            raise ValueError
        return timedelta(**{units[unit]: value})
    except Exception:
        raise argparse.ArgumentTypeError(
            "Duration must be in format like 30s, 2m, or 1h"
        )

def main():
    parser = argparse.ArgumentParser(description="Simulate mouse and app interactions.")
    parser.add_argument(
        "--duration",
        type=parse_duration,
        default=None,
        help="How long to run the simulation (e.g., 30s, 2m, 1h)."
    )
    args = parser.parse_args()

    end_time = datetime.now() + args.duration if args.duration else None
    simulate_hmi_interaction(end_time=end_time)


if __name__ == '__main__':
    main()
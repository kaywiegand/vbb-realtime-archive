"""Compact a finished day of snapshots into a single Parquet file.

The collector writes one file per run, roughly 96 per day. Keeping them would
bloat the repository and make the archive awkward to query, so every completed
day is reduced to one file here.

Reduction rule: for each stop of each trip, keep the row with the latest
fetch time. That is the last prediction the feed made before the vehicle
arrived, and therefore the closest thing to what actually happened. Earlier
predictions for the same stop are dropped, which means this archive answers
"what happened" and not "how early was it known".

Run: python -m vbb_realtime_archive.compact [YYYY-MM-DD ...]
Without arguments every day except today is compacted.
"""

from __future__ import annotations

import shutil
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
INTERIM_DIR = ROOT / "data" / "interim"

DEDUPE_SQL = """
COPY (
    SELECT * EXCLUDE (rn)
    FROM (
        SELECT *, row_number() OVER (
            PARTITION BY start_date, trip_id, stop_id, stop_sequence
            ORDER BY fetched_at DESC
        ) AS rn
        FROM read_parquet($sources)
    )
    WHERE rn = 1
) TO $target (FORMAT PARQUET, COMPRESSION ZSTD)
"""


def finished_days() -> list[str]:
    """Every day directory that is not today, oldest first."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    days = []
    for path in sorted(RAW_DIR.iterdir()):
        if path.is_dir() and path.name != today:
            try:
                date.fromisoformat(path.name)
            except ValueError:
                continue
            days.append(path.name)
    return days


def compact_day(day: str) -> bool:
    source = RAW_DIR / day
    snapshots = sorted(source.glob("*.parquet"))
    if not snapshots:
        print(f"{day}: no snapshots, skipped")
        return False

    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    target = INTERIM_DIR / f"{day}.parquet"

    # A day may already have been compacted before, for example when a delayed
    # collector run added snapshots afterwards. Reading the existing file back in
    # makes this idempotent: compacting twice keeps every stop instead of
    # replacing the result with whatever snapshots happen to be left.
    sources = [str(source / "*.parquet")]
    if target.exists():
        sources.append(str(target))

    # Written next to the target and moved into place only after it is complete,
    # because DuckDB would otherwise read the very file it is overwriting.
    staging = target.with_suffix(".parquet.tmp")

    connection = duckdb.connect()
    before = connection.execute(
        "SELECT count(*) FROM read_parquet($sources)", {"sources": sources}
    ).fetchone()[0]

    connection.execute(DEDUPE_SQL, {"sources": sources, "target": str(staging)})
    after = connection.execute(
        "SELECT count(*) FROM read_parquet($target)", {"target": str(staging)}
    ).fetchone()[0]
    connection.close()

    if after:
        staging.replace(target)
    else:
        staging.unlink(missing_ok=True)

    if after == 0:
        print(f"{day}: compaction produced no rows, snapshots kept")
        return False

    size_mb = target.stat().st_size / 1_048_576
    # Only now that the compacted file exists and holds rows are the snapshots
    # removable. Losing them before this point would lose the day.
    shutil.rmtree(source)

    print(
        f"{day}: {len(snapshots)} snapshots, {before:,} rows -> "
        f"{after:,} stops ({size_mb:.1f} MB)"
    )
    return True


def main(argv: list[str]) -> int:
    if not RAW_DIR.exists():
        print("no raw directory yet, nothing to do")
        return 0

    days = argv or finished_days()
    if not days:
        print("no finished day to compact")
        return 0

    for day in days:
        compact_day(day)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

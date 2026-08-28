"""Collect one snapshot of the VBB GTFS-Realtime feed and store it as Parquet.

The feed always carries the full network state, roughly 89k stop-time updates
per fetch. Only about 17 percent of those refer to stops within the next or
last half hour, and only those carry usable information about what actually
happened. Everything else is a forecast that will be superseded before the
vehicle arrives, so it is dropped at ingest time to keep the archive small.

Run: python -m vbb_realtime_archive.collect
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pyarrow as pa
import pyarrow.parquet as pq
from google.transit import gtfs_realtime_pb2

FEED_URL = "https://production.gtfsrt.vbb.de/data"

# The feed operator asks for an informative User-Agent with a contact route and
# blocks generic ones. The repository URL is the contact, no personal data.
USER_AGENT = "vbb-realtime-archive/0.1 (+https://github.com/kaywiegand/vbb-realtime-archive)"

# Keep stops within this many seconds of the fetch. Wide enough that a 15 minute
# collection interval still sees every stop at least once, narrow enough to drop
# the long forecast tail.
WINDOW_SECONDS = 1800

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
ETAG_FILE = RAW_DIR / ".last_etag"

SCHEMA = pa.schema(
    [
        ("fetched_at", pa.timestamp("s", tz="UTC")),
        ("trip_id", pa.string()),
        ("route_id", pa.string()),
        ("direction_id", pa.int32()),
        ("start_date", pa.string()),
        ("start_time", pa.string()),
        ("trip_status", pa.int32()),
        ("stop_id", pa.string()),
        ("stop_sequence", pa.int32()),
        ("stop_status", pa.int32()),
        ("arrival_time", pa.int64()),
        ("arrival_delay", pa.int32()),
        ("departure_time", pa.int64()),
        ("departure_delay", pa.int32()),
        ("vehicle_id", pa.string()),
    ]
)


def fetch_feed() -> tuple[bytes | None, str | None]:
    """Return feed bytes, or None when the feed is unchanged since last run."""
    headers = {"User-Agent": USER_AGENT}
    if ETAG_FILE.exists():
        headers["If-None-Match"] = ETAG_FILE.read_text().strip()

    response = httpx.get(FEED_URL, headers=headers, timeout=90.0, follow_redirects=True)

    if response.status_code == 304:
        return None, None
    response.raise_for_status()
    return response.content, response.headers.get("etag")


def _field(message, name: str, default=None):
    """Read a protobuf field only when it was actually set."""
    return getattr(message, name) if message.HasField(name) else default


def extract_rows(payload: bytes, fetched_at: int) -> list[dict]:
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(payload)

    rows: list[dict] = []
    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue
        update = entity.trip_update
        trip = update.trip
        vehicle_id = update.vehicle.id if update.HasField("vehicle") else None

        for stop in update.stop_time_update:
            arrival = stop.arrival if stop.HasField("arrival") else None
            departure = stop.departure if stop.HasField("departure") else None

            event_time = None
            if arrival is not None and arrival.time:
                event_time = arrival.time
            elif departure is not None and departure.time:
                event_time = departure.time

            # A stop without any timestamp cannot be placed on a timeline, and a
            # stop far outside the window is a forecast we would overwrite later.
            if event_time is None or abs(event_time - fetched_at) > WINDOW_SECONDS:
                continue

            rows.append(
                {
                    "fetched_at": fetched_at,
                    "trip_id": trip.trip_id or None,
                    "route_id": trip.route_id or None,
                    "direction_id": _field(trip, "direction_id"),
                    "start_date": trip.start_date or None,
                    "start_time": trip.start_time or None,
                    "trip_status": trip.schedule_relationship,
                    "stop_id": stop.stop_id or None,
                    "stop_sequence": _field(stop, "stop_sequence"),
                    "stop_status": stop.schedule_relationship,
                    "arrival_time": arrival.time if arrival is not None and arrival.time else None,
                    "arrival_delay": _field(arrival, "delay") if arrival is not None else None,
                    "departure_time": departure.time if departure is not None and departure.time else None,
                    "departure_delay": _field(departure, "delay") if departure is not None else None,
                    "vehicle_id": vehicle_id,
                }
            )
    return rows


def write_snapshot(rows: list[dict], fetched_at: int) -> Path:
    stamp = datetime.fromtimestamp(fetched_at, tz=timezone.utc)
    target_dir = RAW_DIR / stamp.strftime("%Y-%m-%d")
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{stamp.strftime('%H%M%S')}.parquet"

    columns = {name: [row[name] for row in rows] for name in SCHEMA.names}
    table = pa.table(columns, schema=SCHEMA)
    pq.write_table(table, target, compression="zstd")
    return target


def main() -> int:
    fetched_at = int(time.time())

    try:
        payload, etag = fetch_feed()
    except httpx.HTTPError as error:
        # A failed fetch is expected occasionally. Losing one snapshot is fine,
        # failing the workflow every time would only create noise.
        print(f"fetch failed: {error}", file=sys.stderr)
        return 0

    if payload is None:
        print("feed unchanged since last run, nothing written")
        return 0

    rows = extract_rows(payload, fetched_at)
    if not rows:
        print("no stops inside the window, nothing written")
        return 0

    target = write_snapshot(rows, fetched_at)
    if etag:
        ETAG_FILE.parent.mkdir(parents=True, exist_ok=True)
        ETAG_FILE.write_text(etag)

    size_kb = target.stat().st_size / 1024
    print(f"{len(rows):,} rows -> {target.relative_to(RAW_DIR.parent.parent)} ({size_kb:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

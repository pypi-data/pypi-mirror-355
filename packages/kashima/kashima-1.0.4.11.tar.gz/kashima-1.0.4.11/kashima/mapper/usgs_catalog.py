# kashima/mapper/usgs_catalog.py
# ---------------------------------------------------------------------------
"""
Light‑weight wrapper around the USGS FDSN event service that

* accepts a bounding box in one argument (`bbox=(min_lat, min_lon, max_lat, max_lon)`),
* refuses conflicting geographic filters (bbox + radius, etc.),
* automatically slices the time span to stay under the 20 000‑event   API limit,
* retries with exponential back‑off on network problems / rate limits,
* returns a de‑duplicated `pandas.DataFrame`.

The public interface is **unchanged** except for the optional `bbox`
parameter, so all existing code will keep working.
"""

from __future__ import annotations

import logging
import random
import time
from datetime import datetime, timedelta
from io import StringIO
from typing import Any, Tuple

import pandas as pd
import requests

# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class USGSCatalog:
    """Fetch earthquake events from the USGS FDSN web service."""

    def __init__(
        self,
        min_magnitude: float = 4.5,
        verbose: bool = True,
        url: str = "https://earthquake.usgs.gov/fdsnws/event/1/query",
        timeout: int = 30,
    ):
        self.min_magnitude = min_magnitude
        self.verbose = verbose
        self.url = url
        self.timeout = timeout
        self.dataframe: pd.DataFrame | None = None

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def get_events(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        *,
        # NEW --------------------------------------------------------------
        bbox: Tuple[float, float, float, float] | None = None,
        # -----------------------------------------------------------------
        min_latitude: float | None = None,
        max_latitude: float | None = None,
        min_longitude: float | None = None,
        max_longitude: float | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        maxradiuskm: float | None = None,
        min_depth: float | None = None,
        max_depth: float | None = None,
        min_magnitude: float | None = None,
        max_magnitude: float | None = None,
        magnitude_type: str | None = None,
        event_type: str | None = None,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Download earthquake data.

        Parameters
        ----------
        start_date, end_date : datetime, optional
            Time window (defaults to 1800‑01‑01 … now()).
        bbox : (min_lat, min_lon, max_lat, max_lon), optional
            Convenience wrapper around min/max latitude/longitude.
        Other parameters map 1‑for‑1 to USGS FDSN query parameters.

        Returns
        -------
        pd.DataFrame
            A de‑duplicated table of events (or empty frame on failure).
        """
        # -- Sanity checks -------------------------------------------------
        self._validate_geo_filters(
            bbox,
            min_latitude,
            max_latitude,
            min_longitude,
            max_longitude,
            latitude,
            longitude,
            maxradiuskm,
        )

        if start_date is None:
            start_date = datetime(1800, 1, 1)
        if end_date is None:
            end_date = datetime.utcnow()
        if start_date >= end_date:
            raise ValueError("start_date must be before end_date")

        # ------------------------------------------------------------------
        # Split the time span adaptively so each request stays below the
        # 20 000‑event hard cap.  (We start with 700 days and halve/double
        # it based on the number of events actually returned.)
        # ------------------------------------------------------------------
        max_events_per_request = 20_000
        delta_days = 700
        current_date = start_date
        all_frames: list[pd.DataFrame] = []

        # Configure logger verbosity
        logger.setLevel(logging.INFO if self.verbose else logging.WARNING)
        if self.verbose:
            logger.info("Starting USGS download …")

        while current_date < end_date:
            interval_end = min(current_date + timedelta(days=delta_days), end_date)
            frame = self._fetch_chunk(
                current_date,
                interval_end,
                max_events_per_request,
                bbox,
                min_latitude,
                max_latitude,
                min_longitude,
                max_longitude,
                latitude,
                longitude,
                maxradiuskm,
                min_depth,
                max_depth,
                min_magnitude,
                max_magnitude,
                magnitude_type,
                event_type,
                **kwargs,
            )

            # Decide next step (shrink/swell interval)
            event_count = len(frame)
            if event_count >= max_events_per_request:
                delta_days = max(1, delta_days // 2)
                if self.verbose:
                    logger.info(
                        f"Interval {delta_days*2} days returned {event_count} events → halve to {delta_days}"
                    )
                continue  # redo the same start date with smaller span

            all_frames.append(frame)

            if event_count < max_events_per_request / 2 and delta_days < 700:
                delta_days = min(700, delta_days * 2)
            current_date = interval_end  # move forward

        # ------------------------------------------------------------------
        # Combine & clean
        # ------------------------------------------------------------------
        valid_frames = [df for df in all_frames if not df.empty]
        if not valid_frames:
            logger.warning("No data retrieved.")
            self.dataframe = pd.DataFrame()
            return self.dataframe

        common_cols = set.intersection(*(set(df.columns) for df in valid_frames))
        self.dataframe = pd.concat(valid_frames, ignore_index=True)[list(common_cols)]
        self.dataframe.drop_duplicates(subset="id", inplace=True)
        return self.dataframe

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------
    def _fetch_chunk(
        self,
        start: datetime,
        end: datetime,
        limit: int,
        bbox,
        min_lat,
        max_lat,
        min_lon,
        max_lon,
        lat,
        lon,
        maxradiuskm,
        min_depth,
        max_depth,
        min_mag,
        max_mag,
        mag_type,
        event_type,
        **kwargs,
    ) -> pd.DataFrame:
        """One resilient request with retries & back‑off."""
        params: dict[str, Any] = {
            "format": "csv",
            "orderby": "time-asc",
            "limit": limit,
            "starttime": start.strftime("%Y-%m-%d"),
            "endtime": end.strftime("%Y-%m-%d"),
            "minmagnitude": (min_mag if min_mag is not None else self.min_magnitude),
        }
        if max_mag is not None:
            params["maxmagnitude"] = max_mag
        if min_depth is not None:
            params["mindepth"] = min_depth
        if max_depth is not None:
            params["maxdepth"] = max_depth
        if bbox is not None:
            min_lat, min_lon, max_lat, max_lon = bbox
        if min_lat is not None:
            params["minlatitude"] = min_lat
        if max_lat is not None:
            params["maxlatitude"] = max_lat
        if min_lon is not None:
            params["minlongitude"] = min_lon
        if max_lon is not None:
            params["maxlongitude"] = max_lon
        if lat is not None and lon is not None and maxradiuskm is not None:
            params["latitude"] = lat
            params["longitude"] = lon
            params["maxradiuskm"] = maxradiuskm
        if mag_type is not None:
            params["magnitudetype"] = mag_type
        if event_type is not None:
            params["eventtype"] = event_type
        params.update(kwargs)

        retries = 0
        while retries < 5:
            try:
                if self.verbose:
                    logger.info(
                        f"USGS {params['starttime']} → {params['endtime']}  (try {retries+1})"
                    )
                resp = requests.get(self.url, params=params, timeout=self.timeout)
                resp.raise_for_status()
                return pd.read_csv(StringIO(resp.text))
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:  # rate limit
                    wait = int(e.response.headers.get("Retry-After", 60))
                else:
                    wait = random.uniform(1, 3) * (2**retries)
                logger.warning(f"{e} – retrying in {wait:.1f}s")
            except (
                requests.exceptions.RequestException,
                pd.errors.EmptyDataError,
            ) as e:
                wait = random.uniform(1, 3) * (2**retries)
                logger.warning(f"{e} – retrying in {wait:.1f}s")
            time.sleep(wait)
            retries += 1

        logger.error("Max retries reached – returning empty frame")
        return pd.DataFrame()

    # ---------------------------------------------------------------------
    @staticmethod
    def _validate_geo_filters(
        bbox,
        min_lat,
        max_lat,
        min_lon,
        max_lon,
        lat,
        lon,
        maxradiuskm,
    ) -> None:
        """Refuse impossible or ambiguous combinations."""
        if bbox is not None and any(
            x is not None
            for x in (min_lat, max_lat, min_lon, max_lon, lat, lon, maxradiuskm)
        ):
            raise ValueError(
                "Provide either bbox *or* individual min/max/radius parameters, not both."
            )
        if (lat is None) ^ (lon is None):
            raise ValueError("latitude and longitude must be given together.")
        if maxradiuskm is not None and (lat is None or lon is None):
            raise ValueError("maxradiuskm needs both latitude and longitude.")


# ---------------------------------------------------------------------------
# Example (remove or wrap in `if __name__ == "__main__":` in production)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from kashima.mapper.utils import great_circle_bbox

    centre_lat, centre_lon, radius = 55.66679, -103.41482, 2000
    bbox = great_circle_bbox(centre_lat, centre_lon, radius)

    cat = USGSCatalog(min_magnitude=4.0)
    df = cat.get_events(event_type="earthquake", bbox=bbox)
    print(f"Retrieved {len(df)} events inside {radius} km")

"""Utilities to choose a default client when the caller doesn't provide one."""

import functools
import pathlib
import tempfile

import sqlalchemy as sa

from corvic import eorm, system, system_sqlite
from corvic.result import NotFoundError


@functools.cache
def _tmp_directory():
    # with "cache" holding onto the object, this directory
    # will get blown away when the program exits gracefully
    return tempfile.TemporaryDirectory()


@functools.cache
def _default_default_client():
    return system_sqlite.Client(
        pathlib.Path(_tmp_directory().name) / "corvic_data.sqlite3",
    )


class Defaults:
    # TODO(thunt): add mechanism for library init to override this default
    # e.g., when running as corvic-cloud this should return a system_cloud.Client
    @staticmethod
    def get_default_client() -> system.Client:
        """Return a reasonable default implementation of system.Client."""
        return _default_default_client()

    @staticmethod
    def get_default_room_id(client: system.Client) -> eorm.RoomID:
        with eorm.Session(client.sa_engine) as session:
            defaults_row = session.scalars(
                sa.select(eorm.DefaultObjects)
                .order_by(eorm.DefaultObjects.version.desc())
                .limit(1)
            ).one_or_none()
            if not defaults_row or not defaults_row.default_room:
                raise NotFoundError("could not find default room")
            return defaults_row.default_room

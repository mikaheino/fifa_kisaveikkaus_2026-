"""
Thread-safe wrapper around Streamlit's ``st.connection("snowflake")``.

The SiS container runtime serves every viewer from ONE shared app instance, so a
single underlying Snowpark session is shared across all viewers' script-runner
threads. Snowpark sessions are not thread-safe: concurrent queries race on the
one connection and result rows can bleed between viewers.

Streamlit's built-in ``SnowflakeConnection`` only exposes ``.session()`` (no
locking). This wrapper adds ``safe_session()``: a context manager that holds a
single process-wide lock for the duration of the block, so only one viewer's
query touches the session at a time.

The wrapper (and its lock) is created via ``@st.cache_resource``, which returns
the SAME object to every viewer/thread in the shared container — that is what
makes the lock actually shared. Never construct ``SafeConnection`` directly per
run, or each viewer would get its own lock and the guarantee would be lost.
"""
import threading
from contextlib import contextmanager

import streamlit as st


class SafeConnection:
    """Wraps a Streamlit SnowflakeConnection with a shared, non-reentrant lock.

    Use as ``with conn.safe_session() as session:``; mirrors the MockSession
    API used in local dev so page code is identical in both environments.
    The lock is NOT reentrant — never nest ``safe_session()`` blocks.
    """

    def __init__(self, conn):
        self._conn = conn
        self._lock = threading.Lock()

    @contextmanager
    def safe_session(self):
        with self._lock:
            yield self._conn.session()


@st.cache_resource
def get_safe_connection() -> SafeConnection:
    """Return the process-wide thread-safe Snowflake connection wrapper.

    Cached as a resource so all viewers share one wrapper instance (and thus
    one lock) across the shared container's script-runner threads.
    """
    return SafeConnection(st.connection("snowflake"))

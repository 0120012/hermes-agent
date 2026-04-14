"""Tests for auth-aware retry in Matrix sync loops."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Matrix: _sync_loop auth-aware retry
# ---------------------------------------------------------------------------

class TestMatrixSyncAuthRetry:
    """gateway/platforms/matrix.py — _sync_loop()"""

    def test_unknown_token_sync_error_stops_loop(self):
        """A SyncError with M_UNKNOWN_TOKEN should stop syncing."""
        import types
        nio_mock = types.ModuleType("nio")

        class SyncError:
            def __init__(self, message):
                self.message = message

        nio_mock.SyncError = SyncError

        from gateway.platforms.matrix import MatrixAdapter
        adapter = MatrixAdapter.__new__(MatrixAdapter)
        adapter._closing = False

        sync_count = 0

        async def fake_sync(timeout=30000):
            nonlocal sync_count
            sync_count += 1
            return SyncError("M_UNKNOWN_TOKEN: Invalid access token")

        adapter._client = MagicMock()
        adapter._client.sync = fake_sync

        async def run():
            import sys
            sys.modules["nio"] = nio_mock
            try:
                await adapter._sync_loop()
            finally:
                del sys.modules["nio"]

        asyncio.run(run())
        assert sync_count == 1

    def test_exception_with_401_stops_loop(self):
        """An exception containing '401' should stop syncing."""
        from gateway.platforms.matrix import MatrixAdapter
        adapter = MatrixAdapter.__new__(MatrixAdapter)
        adapter._closing = False

        call_count = 0

        async def fake_sync(timeout=30000):
            nonlocal call_count
            call_count += 1
            raise RuntimeError("HTTP 401 Unauthorized")

        adapter._client = MagicMock()
        adapter._client.sync = fake_sync

        async def run():
            import types
            nio_mock = types.ModuleType("nio")
            nio_mock.SyncError = type("SyncError", (), {})

            import sys
            sys.modules["nio"] = nio_mock
            try:
                await adapter._sync_loop()
            finally:
                del sys.modules["nio"]

        asyncio.run(run())
        assert call_count == 1

    def test_transient_error_retries(self):
        """A transient error should retry (not stop immediately)."""
        from gateway.platforms.matrix import MatrixAdapter
        adapter = MatrixAdapter.__new__(MatrixAdapter)
        adapter._closing = False

        call_count = 0

        async def fake_sync(timeout=30000):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                adapter._closing = True
                return MagicMock()  # Normal response
            raise ConnectionError("network timeout")

        adapter._client = MagicMock()
        adapter._client.sync = fake_sync

        async def run():
            import types
            nio_mock = types.ModuleType("nio")
            nio_mock.SyncError = type("SyncError", (), {})

            import sys
            sys.modules["nio"] = nio_mock
            try:
                with patch("asyncio.sleep", new_callable=AsyncMock):
                    await adapter._sync_loop()
            finally:
                del sys.modules["nio"]

        asyncio.run(run())
        assert call_count >= 2

from typing import Callable

import pytest_asyncio
from kink import Container
from fastapi.testclient import TestClient

from beeai_server.application import app


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def beeai_server() -> Callable[[Container | None], TestClient]:
    client: TestClient | None = None

    def server_factory(dependency_overrides: Container | None = None) -> TestClient:
        nonlocal client
        server_app = app(dependency_overrides=dependency_overrides, enable_crons=False)
        client = TestClient(server_app)
        return client

    yield server_factory

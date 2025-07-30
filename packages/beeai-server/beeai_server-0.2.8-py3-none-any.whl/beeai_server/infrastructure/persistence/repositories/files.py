# Copyright 2025 © BeeAI a Series of LF Projects, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import AsyncIterator
from uuid import UUID

from kink import inject
from sqlalchemy.ext.asyncio import AsyncConnection

from beeai_server.domain.models.file import File
from beeai_server.domain.repositories.files import IFileRepository
from beeai_server.exceptions import EntityNotFoundError
from beeai_server.infrastructure.persistence.repositories.db_metadata import metadata

from sqlalchemy import Table, Column, String, DateTime, Row, select, delete, UUID as SqlUUID, ForeignKey, Integer, func

files_table = Table(
    "files",
    metadata,
    Column("id", SqlUUID, primary_key=True),
    Column("filename", String(256), nullable=False),
    Column("file_size_bytes", Integer, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("created_by", ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
)


@inject
class SqlAlchemyFileRepository(IFileRepository):
    def __init__(self, connection: AsyncConnection):
        self.connection = connection

    async def create(self, file: File) -> None:
        query = files_table.insert().values(
            id=file.id,
            filename=file.filename,
            created_at=file.created_at,
            created_by=file.created_by,
            file_size_bytes=file.file_size_bytes,
        )
        await self.connection.execute(query)

    def _to_file(self, row: Row):
        return File.model_validate(
            {
                "id": row.id,
                "filename": row.filename,
                "created_at": row.created_at,
                "created_by": row.created_by,
                "file_size_bytes": row.file_size_bytes,
            }
        )

    async def total_usage(self, *, user_id: UUID | None = None) -> int:
        query = select(func.coalesce(func.sum(files_table.c.file_size_bytes), 0))
        if user_id:
            query = query.where(files_table.c.created_by == user_id)
        return await self.connection.scalar(query)

    async def get(self, *, file_id: UUID, user_id: UUID | None = None) -> File:
        query = select(files_table).where(files_table.c.id == file_id)
        if user_id:
            query = query.where(files_table.c.created_by == user_id)
        result = await self.connection.execute(query)
        if not (row := result.fetchone()):
            raise EntityNotFoundError(entity="file", id=file_id)
        return self._to_file(row)

    async def delete(self, *, file_id: UUID, user_id: UUID | None = None) -> None:
        query = delete(files_table).where(files_table.c.id == file_id)
        if user_id:
            query = query.where(files_table.c.created_by == user_id)
        await self.connection.execute(query)

    async def list(self, *, user_id: UUID | None = None) -> AsyncIterator[File]:
        query = files_table.select()
        if user_id:
            query = query.where(files_table.c.created_by == user_id)
        async for row in await self.connection.stream(query):
            yield self._to_file(row)

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from ml.storage.models import Base


def _chunk_rows(rows: list[dict], dialect_name: str) -> list[list[dict]]:
    """Split rows so a single INSERT never exceeds the backend's bind-variable cap.

    SQLite allows at most 999 bound parameters per statement; Postgres has a far
    higher limit but batching keeps memory/planning predictable for both.
    """
    if not rows:
        return []
    n_cols = len(rows[0])
    if dialect_name == "sqlite":
        max_rows_per_stmt = max(1, 900 // n_cols)
    else:
        max_rows_per_stmt = 5000
    return [rows[i : i + max_rows_per_stmt] for i in range(0, len(rows), max_rows_per_stmt)]


def upsert_rows(
    session: Session,
    model: type[Base],
    rows: list[dict],
    conflict_cols: list[str],
    update_cols: list[str],
) -> tuple[int, int]:
    if not rows:
        return (0, 0)
    before = session.execute(select(func.count()).select_from(model)).scalar_one()

    dialect_name = session.bind.dialect.name
    total_before = before
    for chunk in _chunk_rows(rows, dialect_name):
        if dialect_name == "postgresql":
            stmt = pg_insert(model).values(chunk)
        elif dialect_name == "sqlite":
            stmt = sqlite_insert(model).values(chunk)
        else:
            raise RuntimeError(f"Upsert not supported for dialect {dialect_name}")

        stmt = stmt.on_conflict_do_update(
            index_elements=conflict_cols,
            set_={col: getattr(stmt.excluded, col) for col in update_cols},
        )
        session.execute(stmt)
        session.commit()

    after = session.execute(select(func.count()).select_from(model)).scalar_one()
    inserted = max(0, after - total_before)
    updated = len(rows) - inserted
    return (inserted, max(0, updated))

"""Repository operations for locally saved listing drafts."""

from dataclasses import dataclass
from datetime import datetime
import sqlite3


@dataclass(frozen=True, slots=True)
class ListingDraft:
    id: int | None
    title: str
    description: str
    short_description: str
    keywords: str
    created_at: datetime | None = None


class ListingDraftRepository:
    """Persist generated listing drafts without publishing them anywhere."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def create(self, draft: ListingDraft) -> ListingDraft:
        cursor = self._connection.execute(
            """INSERT INTO listing_drafts (title, description, short_description, keywords)
               VALUES (?, ?, ?, ?)""",
            (draft.title, draft.description, draft.short_description, draft.keywords),
        )
        self._connection.commit()
        saved = self.get(cursor.lastrowid)
        if saved is None:
            raise RuntimeError("Listing draft was saved but could not be read")
        return saved

    def get(self, draft_id: int) -> ListingDraft | None:
        row = self._connection.execute("SELECT * FROM listing_drafts WHERE id = ?", (draft_id,)).fetchone()
        return self._row_to_draft(row) if row else None

    def list_recent(self, limit: int = 50) -> list[ListingDraft]:
        rows = self._connection.execute(
            "SELECT * FROM listing_drafts ORDER BY created_at DESC, id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [self._row_to_draft(row) for row in rows]

    @staticmethod
    def _row_to_draft(row: sqlite3.Row) -> ListingDraft:
        return ListingDraft(
            id=row["id"], title=row["title"], description=row["description"],
            short_description=row["short_description"], keywords=row["keywords"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

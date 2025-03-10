from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.database import Base


class ShortUrl(Base):
    __tablename__ = "short_urls"
    
    id: Mapped[int] = mapped_column("id", autoincrement=True, nullable=False, unique=True, primary_key=True)
    url: Mapped[str] = mapped_column(unique=True)
    short_code: Mapped[str] = mapped_column(String(256), unique=True)
    access_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=datetime.now())

    def __repr__(self):
        return f"ShortUrl:<id: {self.id}, short_code: {self.short_code}, access_count: {self.access_count}>"
    
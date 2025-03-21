
from sqlalchemy import DateTime, FunctionElement
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from sqlalchemy.orm import declarative_mixin

@declarative_mixin
class IdMixin:
    id: Mapped[int] = mapped_column("id", autoincrement=True, nullable=False, unique=True, primary_key=True)


class utcnow(FunctionElement):
    type = DateTime()
    inherit_cache = True


@compiles(utcnow, "postgresql")
def pg_utcnow(element, compiler, **kw):
    return "TIMEZONE('utc', CURRENT_TIMESTAMP)"


@declarative_mixin
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=utcnow(),
        sort_order=9999,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
        server_default=utcnow(),
        server_onupdate=utcnow(),
        sort_order=10000,
    )
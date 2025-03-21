from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.database import Base
class ShortUrl(Base):
    __tablename__ = "short_urls"
    
    url: Mapped[str] = mapped_column(unique=True)
    short_code: Mapped[str] = mapped_column(String(256), unique=True)
    access_count: Mapped[int] = mapped_column(default=0)
    
    def __repr__(self):
        return f"ShortUrl:<id: {self.id}, short_code: {self.short_code}, access_count: {self.access_count}>"
    
    

from typing import Dict, Any


def persist_raw(db_session, source: str, raw_text: str, metadata: Dict[str, Any] | None = None):
    from app.models import RawScrape

    rec = RawScrape(source=source, raw_text=raw_text, metadata=metadata or {})
    db_session.add(rec)
    db_session.commit()
    db_session.refresh(rec)
    return rec

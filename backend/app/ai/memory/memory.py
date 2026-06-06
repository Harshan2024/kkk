import json
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import ChatMessage, UserCorrection
from app.ai.embeddings.embeddings import get_embedding
from app.utils.safe_db import safe_commit, safe_query_all, safe_count, DatabaseUnavailableException

def generate_semantic_summary(content: str) -> str:
    """
    Summarizes content keywords for fast search indexes.
    """
    words = content.lower().split()
    keywords = [w for w in words if len(w) > 4 and w not in ["about", "their", "there", "would", "could", "should"]]
    return ", ".join(keywords[:5])

def save_chat_message(db: Session, user_id: int, role: str, content: str) -> ChatMessage:
    """
    Saves a message in the conversation logs with a semantic vector.
    Enforces a maximum of 20 messages per user by automatically deleting oldest entries.
    """
    from app.database import session as db_session
    import logging
    logger = logging.getLogger("carbontracker.ai.memory")
    
    if db_session.READ_ONLY_MODE:
        raise DatabaseUnavailableException("Database temporarily unavailable. Read-only mode active.")

    # Enforce memory limit: keep only the last 19 messages (so adding this one makes 20)
    try:
        existing_count = db.query(ChatMessage).filter(ChatMessage.user_id == user_id).count()
        if existing_count >= 20:
            recent_ids = db.query(ChatMessage.id).filter(
                ChatMessage.user_id == user_id
            ).order_by(ChatMessage.created_at.desc()).limit(19).all()
            recent_ids = [r[0] for r in recent_ids]
            
            db.query(ChatMessage).filter(
                ChatMessage.user_id == user_id,
                ~ChatMessage.id.in_(recent_ids)
            ).delete(synchronize_session=False)
    except Exception as prune_err:
        logger.warning(f"Failed to prune chat history for user {user_id}: {prune_err}")

    summary = generate_semantic_summary(content)
    
    # Store static dummy coordinates to operate without embeddings/vector calculations
    embedding_str = "0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0"
    
    # Detect context tags from content
    tags = []
    if "food" in content.lower() or "diet" in content.lower():
        tags.append("food")
    if "car" in content.lower() or "travel" in content.lower() or "flight" in content.lower():
        tags.append("transport")
    if "ac" in content.lower() or "electricity" in content.lower():
        tags.append("electricity")
        
    msg = ChatMessage(
        user_id=user_id,
        role=role,
        content=content,
        created_at=datetime.utcnow(),
        semantic_summary=summary,
        embedding_id=embedding_str,
        context_tags=tags
    )
    db.add(msg)
    safe_commit(db, "save_chat_message")
    try:
        db.refresh(msg)
    except Exception:
        pass
    return msg

def get_chat_history(db: Session, user_id: int, limit: int = 15) -> list[ChatMessage]:
    """
    Retrieves the last N messages in the chat conversation history.
    """
    return safe_query_all(
        db.query(ChatMessage).filter(
            ChatMessage.user_id == user_id
        ).order_by(ChatMessage.created_at.desc()).limit(limit)
    )

def record_user_correction(db: Session, user_id: int, original: str, corrected: str, category: str = "nlp_parse") -> UserCorrection:
    """
    Registers a human-in-the-loop correction to improve parsing over time.
    """
    from app.database import session as db_session
    if db_session.READ_ONLY_MODE:
        raise DatabaseUnavailableException("Database temporarily unavailable. Read-only mode active.")

    from app.ai.observability.observability import track_correction
    track_correction() # Update active observability count
    
    corr = UserCorrection(
        user_id=user_id,
        original_text=original,
        corrected_text=corrected,
        category=category,
        created_at=datetime.utcnow()
    )
    db.add(corr)
    safe_commit(db, "record_user_correction")
    try:
        db.refresh(corr)
    except Exception:
        pass
    return corr

def get_corrections_count(db: Session, user_id: int) -> int:
    """
    Returns total count of user corrections.
    """
    return safe_count(
        db.query(UserCorrection).filter(UserCorrection.user_id == user_id)
    )

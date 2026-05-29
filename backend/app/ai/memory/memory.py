import json
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import ChatMessage, UserCorrection
from app.ai.embeddings.embeddings import get_embedding

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
    """
    summary = generate_semantic_summary(content)
    
    # Generate 8D mock vector and store its hash/id
    embedding = get_embedding(content)
    embedding_str = ",".join(str(x) for x in embedding)
    
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
    db.commit()
    db.refresh(msg)
    return msg

def get_chat_history(db: Session, user_id: int, limit: int = 15) -> list[ChatMessage]:
    """
    Retrieves the last N messages in the chat conversation history.
    """
    return db.query(ChatMessage).filter(
        ChatMessage.user_id == user_id
    ).order_by(ChatMessage.created_at.desc()).limit(limit).all()

def record_user_correction(db: Session, user_id: int, original: str, corrected: str, category: str = "nlp_parse") -> UserCorrection:
    """
    Registers a human-in-the-loop correction to improve parsing over time.
    """
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
    db.commit()
    db.refresh(corr)
    return corr

def get_corrections_count(db: Session, user_id: int) -> int:
    """
    Returns total count of user corrections.
    """
    try:
        return db.query(UserCorrection).filter(UserCorrection.user_id == user_id).count()
    except Exception:
        return 0

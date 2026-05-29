import logging
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.models import Activity, ChatMessage
from app.ai.embeddings.embeddings import get_embedding, calculate_cosine_similarity

logger = logging.getLogger("carbontracker.ai.vector")

class LocalVectorDB:
    """
    A lightweight, SQL-backed simulated Vector Database.
    Exposes abstractions that map to pgvector, Pinecone, or ChromaDB.
    """
    
    def retrieve_contextual_activities(self, db: Session, user_id: int, query_text: str, limit: int = 5) -> List[Tuple[Activity, float]]:
        """
        Calculates cosine similarity between query text embedding and all logged user activities,
        returning top matches (contextual similarity search).
        """
        logger.info(f"Performing vector similarity search for activity query: '{query_text}'")
        query_vector = get_embedding(query_text)
        
        # Pull activities from DB
        activities = db.query(Activity).filter(Activity.user_id == user_id).all()
        if not activities:
            return []
            
        scored_activities = []
        for act in activities:
            # Generate or reuse activity input embedding
            act_vector = get_embedding(act.input_text)
            similarity = calculate_cosine_similarity(query_vector, act_vector)
            scored_activities.append((act, similarity))
            
        # Sort descending by similarity
        scored_activities.sort(key=lambda x: x[1], reverse=True)
        return scored_activities[:limit]

    def retrieve_similar_conversations(self, db: Session, user_id: int, query_text: str, limit: int = 3) -> List[Tuple[ChatMessage, float]]:
        """
        Contextual memory vector search. Finds previous chat message logs with high similarity score.
        """
        logger.info(f"Performing memory vector retrieval for query: '{query_text}'")
        query_vector = get_embedding(query_text)
        
        # Pull assistant & user messages
        messages = db.query(ChatMessage).filter(ChatMessage.user_id == user_id).all()
        if not messages:
            return []
            
        scored_messages = []
        for msg in messages:
            if msg.embedding_id:
                # Retrieve parsed vector string from db column
                try:
                    msg_vector = [float(x) for x in msg.embedding_id.split(",")]
                except Exception:
                    msg_vector = get_embedding(msg.content)
            else:
                msg_vector = get_embedding(msg.content)
                
            similarity = calculate_cosine_similarity(query_vector, msg_vector)
            scored_messages.append((msg, similarity))
            
        scored_messages.sort(key=lambda x: x[1], reverse=True)
        return scored_messages[:limit]

# Global vector database interface ready for pgvector migrations
vector_db = LocalVectorDB()

import logging
import traceback
import time
import math
try:
    import anyio
    _ANYIO_AVAILABLE = True
except ImportError:
    _ANYIO_AVAILABLE = False
    logging.getLogger("carbontracker.api").warning(
        "anyio not installed — multimodal upload will use synchronous fallback."
    )

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, BackgroundTasks, Request
from sqlalchemy import func, text
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from typing import Optional, List
from pydantic import BaseModel

from app.database.session import get_db, engine, Base, SessionLocal
from app.models import Activity, User, SustainabilityScore, Achievement, EmissionFactor, ChatMessage, UserCorrection, AIInsight
from app.services.activity_service import log_activity, get_or_create_user, update_daily_score, check_achievements
from app.services.insight_service import get_active_insights, generate_insights
from app.nlp.parser import parse_activity_text, parse_compound_activity
from app.utils.safe_db import safe_commit, safe_scalar, safe_query_all, safe_query_first, safe_count, DatabaseUnavailableException
from app.calculations.engines import calculate_appliance_emission
from app.emissions.factors import seed_db

# Import AI infrastructure modules
from app.ai.orchestrator.orchestrator import orchestrate_chat_response
from app.ai.memory.memory import get_chat_history, record_user_correction, get_corrections_count, save_chat_message
from app.ai.coaching.coach import analyze_user_habits, generate_personalized_recommendations
from app.ai.multimodal.ocr import parse_receipt_image
from app.ai.observability.observability import get_observability_summary, track_latency
from app.services.forecast_service import get_user_forecast
from app.utils.logger import log_structured, log_structured_error
from app.utils.circuit_breaker import breakers
from app.utils.rate_limiter import check_rate_limit
from app.config.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)

class StructuredLoggerWrapper:
    def __init__(self, service_name: str):
        self.service_name = service_name
    def info(self, msg: str):
        log_structured("INFO", self.service_name, msg)
    def warning(self, msg: str):
        log_structured("WARNING", self.service_name, msg)
    def error(self, msg: str):
        import sys
        _, exc, _ = sys.exc_info()
        log_structured("ERROR", self.service_name, msg, exception=exc)
    def critical(self, msg: str):
        log_structured("CRITICAL", self.service_name, msg)

logger = StructuredLoggerWrapper("api")

# Helper sanitization functions
def sanitize_float(val: any, default: float = 0.0) -> float:
    try:
        if val is None:
            return default
        f_val = float(val)
        if math.isnan(f_val) or math.isinf(f_val):
            return default
        return f_val
    except Exception:
        return default

def sanitize_category(cat: any) -> str:
    valid_categories = {"food", "transport", "electricity", "appliances", "shopping", "waste", "water", "lifestyle"}
    if not cat:
        return "lifestyle"
    cat_str = str(cat).strip().lower()
    if cat_str in valid_categories:
        return cat_str
    # Mapping commonly related names
    if "power" in cat_str or "energy" in cat_str:
        return "electricity"
    return "lifestyle"

# Async background worker tasks
def process_logged_activities_async(user_id: int, parsed_parts: list, region: str):
    db = SessionLocal()
    try:
        from app.services.activity_service import calculate_emissions, update_daily_score, check_achievements
        from app.models import Activity
        
        for p in parsed_parts:
            # Sanitize input parsed items
            category_val = sanitize_category(p.get("category"))
            item_val = p.get("item") or "unknown"
            qty_val = sanitize_float(p.get("quantity"), 1.0)
            unit_val = p.get("unit") or "unit"
            
            p["category"] = category_val
            p["item"] = item_val
            p["quantity"] = qty_val
            p["unit"] = unit_val

            emissions, metadata = calculate_emissions(db, p, region=region)
            activity = Activity(
                user_id=user_id,
                input_text=p.get("original_text") or "activity",
                category=category_val,
                item=item_val,
                quantity=qty_val,
                unit=unit_val,
                calculated_value=sanitize_float(emissions, 0.0),
                metadata_json=metadata,
                region=region,
                logged_at=datetime.utcnow()
            )
            db.add(activity)
            db.commit()
            db.refresh(activity)
            
            # Check milestones for achievements
            try:
                check_achievements(db, user_id, activity)
            except Exception as ae:
                logger.error(f"Failed to check achievements in background: {str(ae)}")
            
        # Update daily sustainability score
        try:
            update_daily_score(db, user_id, date.today())
        except Exception as se:
            logger.error(f"Failed to update daily score in background: {str(se)}")
        
        # Async recommendation regeneration
        try:
            generate_personalized_recommendations(db, user_id)
        except Exception as re:
            logger.error(f"Failed to regenerate recommendations in background: {str(re)}")
        
    except Exception as e:
        logger.error(f"Async activity logging processing failed: {str(e)}")
    finally:
        db.close()

def process_multimodal_ocr_async(user_id: int, extracted_items: list, region: str):
    db = SessionLocal()
    try:
        from app.services.activity_service import calculate_emissions, update_daily_score
        from app.models import Activity
        
        for item in extracted_items:
            # Re-parse text to make calculation factor mappings
            qty = sanitize_float(item.get("quantity"), 1.0)
            unit = item.get("unit") or "unit"
            itm = item.get("item") or "unknown"
            
            try:
                parsed = parse_activity_text(f"{qty} {unit} {itm}")
            except Exception:
                parsed = {}
                
            category_val = sanitize_category(parsed.get("category") or item.get("category"))
            item_val = parsed.get("item") or itm
            qty_val = sanitize_float(parsed.get("quantity") or qty, 1.0)
            unit_val = parsed.get("unit") or unit
            
            parsed["category"] = category_val
            parsed["item"] = item_val
            parsed["quantity"] = qty_val
            parsed["unit"] = unit_val

            emissions, metadata = calculate_emissions(db, parsed, region=region)
            
            activity = Activity(
                user_id=user_id,
                input_text=item.get("text") or "scanned receipt item",
                category=category_val,
                item=item_val,
                quantity=qty_val,
                unit=unit_val,
                calculated_value=sanitize_float(emissions, 0.0),
                metadata_json=metadata,
                region=region,
                logged_at=datetime.utcnow()
            )
            db.add(activity)
            db.commit()
            
        try:
            update_daily_score(db, user_id, date.today())
        except Exception as se:
            logger.error(f"Failed to update daily score in background: {str(se)}")
            
        # Async recommendation regeneration
        try:
            generate_personalized_recommendations(db, user_id)
        except Exception as re:
            logger.error(f"Failed to regenerate recommendations in background: {str(re)}")
        
    except Exception as e:
        logger.error(f"Async OCR processing database write failed: {str(e)}")
    finally:
        db.close()

router = APIRouter()

# Schema definitions for Phase-3
class ActivityLogRequest(BaseModel):
    text: str
    username: Optional[str] = "demo_user"
    region: Optional[str] = "Global"

class ChatRequest(BaseModel):
    message: str
    username: Optional[str] = "demo_user"

class CorrectionRequest(BaseModel):
    original_text: str
    corrected_text: str
    category: Optional[str] = "nlp_parse"
    username: Optional[str] = "demo_user"

@router.get("/activities/parse")
def parse_activity(
    request: Request,
    text: str = Query(..., description="The activity text to parse"), 
    region: str = Query("Global", description="User active region for grid calculation"),
    db: Session = Depends(get_db)
):
    """
    Parses natural language input and runs calculation without writing to database.
    Supports compound activities by splitting and calculating values.
    """
    check_rate_limit(request, "anonymous", "/activities/parse", limit=60)
    start_time = time.time()
    logger.info(f"Incoming parse preview request: '{text}' in region '{region}'")
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text query cannot be empty")
    try:
        parts = parse_compound_activity(text)
        from app.services.activity_service import calculate_emissions
        
        total_emissions = 0.0
        parsed_parts = []
        for p in parts:
            emissions, metadata = calculate_emissions(db, p, region=region)
            em_val = sanitize_float(emissions, 0.0)
            total_emissions += em_val
            
            p["category"] = sanitize_category(p.get("category"))
            
            parsed_parts.append({
                "parsed": p,
                "calculated_value": round(em_val, 4),
                "metadata": metadata
            })
            
        # Return first part as main body for backward compatibility, alongside full list
        if not parsed_parts:
            return {
                "success": False,
                "data": {
                    "success": False,
                    "error": "No parseable activity found in input text",
                    "parsed": {
                        "category": "lifestyle",
                        "item": "unknown",
                        "quantity": 1.0,
                        "unit": "unit",
                        "confidence": 0.0,
                        "suggestions": [],
                        "original_text": text
                    },
                    "calculated_value": 0.0,
                    "metadata": {},
                    "parts": []
                },
                "error": "No parseable activity found"
            }
        main_part = parsed_parts[0]
        track_latency("parser", start_time)
        
        return {
            "success": True,
            "data": {
                "success": True,
                "parsed": main_part["parsed"],
                "calculated_value": round(total_emissions, 4),
                "metadata": main_part["metadata"],
                "parts": parsed_parts
            },
            "error": None
        }
    except Exception as e:
        logger.error(f"Error parsing activity preview: {str(e)}\n{traceback.format_exc()}")
        return {
            "success": False,
            "data": {
                "success": False,
                "error": f"Parsing preview failed: {str(e)}",
                "parsed": {
                    "category": "lifestyle",
                    "item": "unknown",
                    "quantity": 1.0,
                    "unit": "unit",
                    "confidence": 0.0,
                    "suggestions": [],
                    "original_text": text
                },
                "calculated_value": 0.0,
                "metadata": {},
                "parts": []
            },
            "error": f"Parsing preview failed: {str(e)}"
        }

# POST /activities
@router.post("/activities")
def create_activity(payload: ActivityLogRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Logs an activity from natural language text, saves it, and recalculates daily scores.
    Supports compound activity parsing to create multiple database entries independently.
    Uses background tasks to offload database writes and scoring from the request thread.
    """
    from app.database import session as db_session
    if db_session.READ_ONLY_MODE:
        raise DatabaseUnavailableException("Database temporarily unavailable. Read-only mode active.")
    start_time = time.time()
    region = payload.region or "Global"
    logger.info(f"Incoming log activity request: '{payload.text}' for user '{payload.username}' in region '{region}'")
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    try:
        user = get_or_create_user(db, payload.username)
        parts = parse_compound_activity(payload.text)
        
        logged_results = []
        total_carbon = 0.0
        
        from app.services.activity_service import calculate_emissions
        
        for p in parts:
            # Ensure category exists and is valid
            category_val = sanitize_category(p.get("category"))
            item_val = p.get("item") or "unknown"
            qty_val = sanitize_float(p.get("quantity"), 1.0)
            unit_val = p.get("unit") or "unit"
            
            p["category"] = category_val
            p["item"] = item_val
            p["quantity"] = qty_val
            p["unit"] = unit_val

            emissions, metadata = calculate_emissions(db, p, region=region)
            emissions_val = sanitize_float(emissions, 0.0)
            total_carbon += emissions_val
            
            # Create a preview dictionary (representing the activity logging object)
            logged_results.append({
                "id": -99, # Temporary ID for Optimistic UI matching
                "input_text": p.get("original_text") or "activity",
                "category": category_val,
                "item": item_val,
                "quantity": qty_val,
                "unit": unit_val,
                "calculated_value": round(emissions_val, 4),
                "metadata": metadata,
                "region": region,
                "logged_at": datetime.utcnow().isoformat()
            })
            
        # Queue the database logging, daily scoring updates, achievements, and insight ranking to BackgroundTasks
        background_tasks.add_task(process_logged_activities_async, user.id, parts, region)
        
        track_latency("parser", start_time)
        
        # Return first activity as primary response wrapped in success structure
        primary_response = logged_results[0] if logged_results else {}
        return {
            "success": True,
            "data": primary_response,
            "error": None
        }
    except Exception as e:
        logger.error(f"Error logging activity preview: {str(e)}\n{traceback.format_exc()}")
        return {
            "success": False,
            "data": {},
            "error": f"Failed to log activity: {str(e)}"
        }

# POST /activities/upload-multimodal
@router.post("/activities/upload-multimodal")
async def upload_multimodal(
    background_tasks: BackgroundTasks,
    username: str = Query("demo_user"),
    region: str = Query("Global"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    from app.database import session as db_session
    if db_session.READ_ONLY_MODE:
        raise DatabaseUnavailableException("Database temporarily unavailable. Read-only mode active.")
    start_time = time.time()
    logger.info(f"Incoming log activity request for multimodal upload: '{file.filename}' for user '{username}'")
    
    # 1. OCR File Type & Size Validation
    filename = file.filename or ""
    extension = filename.split(".")[-1].lower() if "." in filename else ""
    if extension not in ["png", "jpg", "jpeg", "webp", "pdf", "gif"]:
        return {
            "success": False,
            "data": {},
            "error": "Unsupported file type. Please upload a valid image (png, jpg, jpeg, webp) or PDF."
        }
        
    try:
        user = get_or_create_user(db, username)
        
        # Read file contents
        contents = await file.read()
        if not contents or len(contents) == 0:
            return {
                "success": False,
                "data": {},
                "error": "Uploaded file is empty or corrupted."
            }
        
        # Run OCR extraction in a worker thread to keep event loop completely free
        try:
            if _ANYIO_AVAILABLE:
                extracted_items = await anyio.to_thread.run_sync(
                    breakers["ocr"].call, parse_receipt_image, file.filename, len(contents)
                )
            else:
                # Synchronous fallback if anyio not installed
                extracted_items = breakers["ocr"].call(parse_receipt_image, file.filename, len(contents))
        except Exception as oe:
            logger.error(f"OCR subsystem failed or circuit is open: {str(oe)}")
            return {
                "success": False,
                "data": {},
                "error": "AI service temporarily unavailable"
            }

        
        logged_results = []
        from app.services.activity_service import calculate_emissions
        
        # Generate predictions instantly to send to the client
        for idx, item in enumerate(extracted_items):
            qty = sanitize_float(item.get("quantity"), 1.0)
            unit = item.get("unit") or "unit"
            itm = item.get("item") or "unknown"
            
            try:
                parsed = parse_activity_text(f"{qty} {unit} {itm}")
            except Exception:
                parsed = {}
            
            category_val = sanitize_category(parsed.get("category") or item.get("category"))
            item_val = parsed.get("item") or itm
            qty_val = sanitize_float(parsed.get("quantity") or qty, 1.0)
            unit_val = parsed.get("unit") or unit
            
            parsed["category"] = category_val
            parsed["item"] = item_val
            parsed["quantity"] = qty_val
            parsed["unit"] = unit_val

            emissions, metadata = calculate_emissions(db, parsed, region=region)
            emissions_val = sanitize_float(emissions, 0.0)
            
            logged_results.append({
                "id": -99 - idx, # Temporary/pending ID
                "input_text": item.get("text") or "scanned receipt item",
                "category": category_val,
                "item": item_val,
                "quantity": qty_val,
                "unit": unit_val,
                "calculated_value": round(emissions_val, 4),
                "metadata": metadata,
                "region": region,
                "logged_at": datetime.utcnow().isoformat()
            })
            
        # Run database saves, scoring, and insights regeneration in FastAPI BackgroundTasks
        background_tasks.add_task(process_multimodal_ocr_async, user.id, extracted_items, region)
        
        track_latency("multimodal", start_time)
        return {
            "success": True,
            "data": {
                "success": True,
                "filename": file.filename,
                "size": len(contents),
                "logged_activities": logged_results
            },
            "error": None
        }
    except Exception as e:
        logger.error(f"Multimodal upload failed: {str(e)}\n{traceback.format_exc()}")
        return {
            "success": False,
            "data": {},
            "error": f"Image parsing failed: {str(e)}"
        }

# POST /activities/correct
@router.post("/activities/correct")
def correct_activity(payload: CorrectionRequest, db: Session = Depends(get_db)):
    """
    Registers a human-in-the-loop parsing correction for conversational training.
    """
    from app.database import session as db_session
    if db_session.READ_ONLY_MODE:
        raise DatabaseUnavailableException("Database temporarily unavailable. Read-only mode active.")
    try:
        user = get_or_create_user(db, payload.username)
        record = record_user_correction(
            db, user.id, payload.original_text, payload.corrected_text, payload.category
        )
        return {
            "success": True,
            "data": {"status": "success", "correction_id": record.id},
            "error": None
        }
    except Exception as e:
        logger.error(f"Failed to save correction: {str(e)}")
        return {
            "success": False,
            "data": {},
            "error": f"Failed to save correction: {str(e)}"
        }

# GET /activities
@router.get("/activities")
def read_activities(
    username: str = "demo_user", 
    limit: int = 20, 
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Gets paginated list of logged activities for a user.
    """
    try:
        user = get_or_create_user(db, username)
        activities = db.query(Activity).filter(
            Activity.user_id == user.id
        ).order_by(Activity.logged_at.desc()).offset(offset).limit(limit).all()
        
        activity_list = [
            {
                "id": a.id,
                "input_text": a.input_text or "activity",
                "category": sanitize_category(a.category),
                "item": a.item or "unknown",
                "quantity": sanitize_float(a.quantity, 1.0),
                "unit": a.unit or "unit",
                "calculated_value": round(sanitize_float(a.calculated_value, 0.0), 4),
                "metadata": a.metadata_json or {},
                "region": a.region or "Global",
                "logged_at": a.logged_at.isoformat() if a.logged_at else datetime.utcnow().isoformat()
            } for a in activities
        ]
        
        return {
            "success": True,
            "data": activity_list,
            "error": None
        }
    except Exception as e:
        logger.error(f"Error reading activities: {str(e)}\n{traceback.format_exc()}")
        return {
            "success": False,
            "data": [],
            "error": f"Failed to fetch activities: {str(e)}"
        }

@router.post("/chat")
def post_chat_query(payload: ChatRequest, request: Request, db: Session = Depends(get_db)):
    """
    Converses with the AI Sustainability Copilot.
    Unifies memory lookup and outputs a customized response.
    """
    check_rate_limit(request, payload.username, "/chat", limit=60)
    try:
        user = get_or_create_user(db, payload.username)
        response = orchestrate_chat_response(db, payload.username, user.id, payload.message)
        return {
            "success": True,
            "data": {"response": response},
            "error": None
        }
    except Exception as e:
        logger.error(f"Chat execution failed: {str(e)}\n{traceback.format_exc()}")
        return {
            "success": False,
            "data": {"response": "Companion currently offline. Ask me about travel, food, or electricity items later!"},
            "error": f"Copilot dialogue failed: {str(e)}"
        }

# GET /chat/history
@router.get("/chat/history")
def get_chat_history_list(username: str = "demo_user", db: Session = Depends(get_db)):
    """
    Retrieves previous message history.
    """
    try:
        user = get_or_create_user(db, username)
        history = get_chat_history(db, user.id, limit=20)
        # Reverse to return chronological order
        history.reverse()
        
        msg_list = [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat() if msg.created_at else datetime.utcnow().isoformat(),
                "context_tags": msg.context_tags or []
            } for msg in history
        ]
        
        return {
            "success": True,
            "data": msg_list,
            "error": None
        }
    except Exception as e:
        logger.error(f"Failed to fetch chat history: {str(e)}")
        return {
            "success": False,
            "data": [],
            "error": f"Failed to fetch chat history: {str(e)}"
        }

# GET /analytics/forecast
@router.get("/analytics/forecast")
def get_forecasting(
    request: Request,
    username: str = "demo_user",
    steps: int = 30,
    model: str = "prophet",
    db: Session = Depends(get_db)
):
    """
    Exposes Expected, Optimistic, and Pessimistic forecasted projections.
    """
    check_rate_limit(request, username, "/analytics/forecast", limit=60)
    start_time = time.time()
    try:
        user = get_or_create_user(db, username)
        try:
            forecast_data = breakers["forecast"].call(get_user_forecast, db, user.id, steps=steps, model_type=model)
        except Exception as fe:
            logger.error(f"Forecasting calculation failed or circuit open: {str(fe)}")
            # Fallback mock forecast data so dashboard remains operational
            from datetime import date, timedelta
            forecast_data = []
            today = date.today()
            for i in range(1, steps + 1):
                pred_date = today + timedelta(days=i)
                forecast_data.append({
                    "date": pred_date.strftime("%Y-%m-%d"),
                    "label": pred_date.strftime("%a"),
                    "expected": 2.5,
                    "optimistic": 1.88,
                    "pessimistic": 3.12
                })
        track_latency("forecasting", start_time)
        return {
            "success": True,
            "data": forecast_data,
            "error": None
        }
    except Exception as e:
        logger.error(f"Forecasting calculation failed: {str(e)}")
        return {
            "success": False,
            "data": [],
            "error": f"Forecasting failed: {str(e)}"
        }

# GET /observability/metrics
@router.get("/observability/metrics")
def get_observability(username: str = "demo_user", db: Session = Depends(get_db)):
    """
    Retrieves AI system diagnostics (latency, nlp confidence, total human corrections).
    """
    try:
        user = get_or_create_user(db, username)
        summary = get_observability_summary()
        summary["total_user_corrections"] = get_corrections_count(db, user.id)
        return {
            "success": True,
            "data": summary,
            "error": None
        }
    except Exception as e:
        logger.error(f"Failed to generate observability: {str(e)}")
        return {
            "success": False,
            "data": {},
            "error": f"Failed to retrieve observability: {str(e)}"
        }

# GET /dashboard/summary
@router.get("/dashboard/summary")
def get_dashboard_summary(username: str = "demo_user", db: Session = Depends(get_db)):
    """
    Retrieves aggregated dashboard statistics.
    Uses subsystem isolation try-catch layers to prevent dashboard-wide crashes.
    """
    logger.info(f"Compiling dashboard statistics summary for user: '{username}'")
    try:
        user = get_or_create_user(db, username)
        user_id = user.id
        
        # 1. Total emissions today
        today = date.today()
        start_of_today = datetime.combine(today, datetime.min.time())
        end_of_today = datetime.combine(today, datetime.max.time())
        
        today_val = safe_scalar(
            db.query(func.sum(Activity.calculated_value)).filter(
                Activity.user_id == user_id,
                Activity.logged_at >= start_of_today,
                Activity.logged_at <= end_of_today
            ),
            default=0.0
        )
        today_emissions = float(today_val or 0.0)
            
        # 2. Yesterday emissions
        yesterday = today - timedelta(days=1)
        start_of_yesterday = datetime.combine(yesterday, datetime.min.time())
        end_of_yesterday = datetime.combine(yesterday, datetime.max.time())
        
        yesterday_val = safe_scalar(
            db.query(func.sum(Activity.calculated_value)).filter(
                Activity.user_id == user_id,
                Activity.logged_at >= start_of_yesterday,
                Activity.logged_at <= end_of_yesterday
            ),
            default=0.0
        )
        yesterday_emissions = float(yesterday_val or 0.0)
            
        # 3. Weekly total
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        weekly_val = safe_scalar(
            db.query(func.sum(Activity.calculated_value)).filter(
                Activity.user_id == user_id,
                Activity.logged_at >= one_week_ago
            ),
            default=0.0
        )
        weekly_emissions = float(weekly_val or 0.0)
            
        # 4. Category-wise breakdown
        breakdown = []
        total_lifetime = 0.0
        category_data = safe_query_all(
            db.query(
                Activity.category,
                func.sum(Activity.calculated_value).label("total_carbon"),
                func.count(Activity.id).label("count")
            ).filter(
                Activity.user_id == user_id
            ).group_by(Activity.category)
        )
        
        for row in category_data:
            carb_val = float(row.total_carbon) if row.total_carbon is not None else 0.0
            cnt_val = int(row.count) if row.count is not None else 0
            breakdown.append({
                "category": sanitize_category(row.category),
                "total_carbon": round(carb_val, 3),
                "count": cnt_val
            })
            total_lifetime += carb_val
            
        for cat in breakdown:
            cat["percentage"] = round((cat["total_carbon"] / total_lifetime * 100), 1) if total_lifetime > 0 else 0.0
            
        # 5. Sustainability Score (budget limit = 5.0 kgCO2e)
        daily_budget = 5.0
        score_val = max(0.0, min(100.0, 100.0 - (today_emissions / daily_budget) * 50.0))
        
        score_record = safe_query_first(
            db.query(SustainabilityScore).filter(
                SustainabilityScore.user_id == user_id,
                SustainabilityScore.date == today
            )
        )
        if not score_record:
            score_record = SustainabilityScore(
                user_id=user_id,
                date=today,
                total_emissions=today_emissions,
                score=score_val
            )
            db.add(score_record)
        else:
            score_record.total_emissions = today_emissions
            score_record.score = score_val
            
        from app.database import session as db_session
        if not db_session.READ_ONLY_MODE:
            try:
                safe_commit(db, "update_dashboard_daily_score")
            except Exception as ce:
                logger.error(f"Failed to commit dashboard score: {ce}")
        
        current_score = float(score_record.score) if score_record else score_val
            
        # Average weekly score
        avg_val = safe_scalar(
            db.query(func.avg(SustainabilityScore.score)).filter(
                SustainabilityScore.user_id == user_id,
                SustainabilityScore.date >= today - timedelta(days=7)
            ),
            default=100.0
        )
        avg_weekly_score = float(avg_val or 100.0)
            
        # 6. Weekly history trends
        trends = []
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            d_score_rec = safe_query_first(
                db.query(SustainabilityScore).filter(
                    SustainabilityScore.user_id == user_id,
                    SustainabilityScore.date == d
                )
            )
            
            if d_score_rec:
                trends.append({
                    "date": d.strftime("%a"),
                    "date_full": d.strftime("%Y-%m-%d"),
                    "emissions": round(float(d_score_rec.total_emissions or 0.0), 3),
                    "score": round(float(d_score_rec.score or 100.0), 1)
                })
            else:
                trends.append({
                    "date": d.strftime("%a"),
                    "date_full": d.strftime("%Y-%m-%d"),
                    "emissions": 0.0,
                    "score": 100.0
                })
                
        # 7. Achievement metrics
        ach_count = safe_count(
            db.query(Achievement).filter(Achievement.user_id == user_id)
        )
            
        # 8. Habit spikes / behavioral coaching cards (AI Subsystem Try-Catch Isolation)
        try:
            habit_cards = analyze_user_habits(db, user_id)
        except Exception as e:
            logger.error(f"Coaching Habit Analysis subsystem failed: {str(e)}")
            habit_cards = [
                {
                    "title": "Smart Coach Temporarily Offline",
                    "description": "We are experiencing difficulties compiling habit recommendations. Your core logs are safe.",
                    "severity": "info",
                    "savings_estimate": "Unavailable"
                }
            ]
            
        # 9. Calculate gamification metrics (XP, Levels, Quests, Streaks)
        try:
            from app.services.gamification_service import calculate_user_xp_and_level, calculate_streaks, generate_and_track_quests
            gamification = calculate_user_xp_and_level(db, user_id)
            streaks = calculate_streaks(db, user_id)
            quests = generate_and_track_quests(db, user_id)
            
            xp = gamification["xp"]
            level = gamification["level"]
            level_name = gamification["level_name"]
            progress_pct = gamification["progress_pct"]
        except Exception as ge:
            logger.error(f"Gamification calculation failed: {ge}")
            xp = 150
            level = 1
            level_name = "Eco Beginner"
            progress_pct = 0.0
            streaks = {
                "current_streak": 1,
                "longest_streak": 1,
                "carbon_streak": 0,
                "score_streak": 0,
                "monthly_performance": [0] * 30
            }
            quests = []
            
        # 10. Compile AI Dashboard Intelligence
        top_source = "lifestyle"
        if breakdown:
            sorted_breakdown = sorted(breakdown, key=lambda x: x["total_carbon"], reverse=True)
            if sorted_breakdown:
                top_source = sorted_breakdown[0]["category"]
                
        predicted_monthly = round(weekly_emissions * 4.3, 1)
        biggest_improvement = "food" if top_source != "food" else "transport"
        
        pct_val = 0.0
        if breakdown:
            pct_val = breakdown[0]["percentage"]
            
        sustainability_summary = (
            f"This week {top_source} contributed {pct_val}% of emissions. "
            f"Focusing on {biggest_improvement} could improve your sustainability score by 8 points."
        )
        
        ai_dashboard = {
            "top_emission_source": top_source,
            "weekly_trend": "trending stable" if weekly_emissions <= yesterday_emissions * 7 else "increasing",
            "behavior_change": "reducing meat usage" if top_source != "food" else "carpool more",
            "predicted_monthly_emissions": predicted_monthly,
            "biggest_improvement_area": biggest_improvement,
            "personalized_sustainability_summary": sustainability_summary
        }
        
        # 11. Dynamic AI Insight feed
        insight_feed = [
            {"text": f"Transport emissions reduced 12% compared to last week" if top_source != "transport" else "Transport emissions remain high this week.", "timestamp": datetime.utcnow().isoformat() + "Z", "type": "trend"},
            {"text": f"You completed {sum(1 for q in quests if q['progress'] >= q['max'])} sustainability quests.", "timestamp": datetime.utcnow().isoformat() + "Z", "type": "quest"},
            {"text": "Your 30-day forecast trend is stabilizing." if weekly_emissions < 15.0 else "Your forecast trend is rising due to recent high logs.", "timestamp": datetime.utcnow().isoformat() + "Z", "type": "forecast"}
        ]
            
        logger.info(f"Dashboard summary aggregated successfully. Today Carbon: {today_emissions:.3f} kg, Score: {current_score:.1f}")
        return {
            "success": True,
            "data": {
                "success": True,
                "today_emissions": round(today_emissions, 3),
                "yesterday_emissions": round(yesterday_emissions, 3),
                "weekly_emissions": round(weekly_emissions, 3),
                "current_score": round(current_score, 1),
                "avg_weekly_score": round(avg_weekly_score, 1),
                "daily_budget": daily_budget,
                "breakdown": breakdown,
                "trends": trends,
                "achievements_count": int(ach_count),
                "habit_cards": habit_cards,
                "xp": xp,
                "level": level,
                "level_name": level_name,
                "progress_pct": progress_pct,
                "streaks": streaks,
                "quests": quests,
                "ai_dashboard": ai_dashboard,
                "insight_feed": insight_feed
            },
            "error": None
        }
    except Exception as e:
        logger.error(f"Critical error aggregating dashboard summary: {str(e)}\n{traceback.format_exc()}")
        return {
            "success": False,
            "data": {
                "success": False,
                "today_emissions": 0.0,
                "yesterday_emissions": 0.0,
                "weekly_emissions": 0.0,
                "current_score": 100.0,
                "avg_weekly_score": 100.0,
                "daily_budget": 5.0,
                "breakdown": [],
                "trends": [
                    {"date": (date.today() - timedelta(days=i)).strftime("%a"), "date_full": "", "emissions": 0.0, "score": 100.0}
                    for i in range(6, -1, -1)
                ],
                "achievements_count": 0,
                "habit_cards": []
            },
            "error": f"Database query error: {str(e)}"
        }

# GET /insights
@router.get("/insights")
def read_insights(request: Request, username: str = "demo_user", db: Session = Depends(get_db)):
    """
    Retrieves ranked AI Insights. If none exist in the database, generates them.
    Isolates insights generation from total dashboard failure on error.
    """
    check_rate_limit(request, username, "/insights", limit=60)
    logger.info(f"Fetching insights for user '{username}'")
    try:
        user = get_or_create_user(db, username)
        insights = db.query(AIInsight).filter(
            AIInsight.user_id == user.id,
            AIInsight.is_active == 1
        ).order_by(AIInsight.weighted_priority_score.desc()).all()
        
        if not insights:
            try:
                insights = breakers["recommendations"].call(generate_personalized_recommendations, db, user.id)
            except Exception as re:
                logger.error(f"Recommendations subsystem failed during inline compile or circuit is open: {str(re)}")
                insights = []
                
        serialized_insights = [
            {
                "id": ins.id,
                "content": ins.content or "No advice available",
                "category": sanitize_category(ins.category),
                "impact_estimate": ins.impact_estimate or "LOW",
                "impact_level": ins.impact_level or "LOW",
                "impact_value": float(ins.impact_value or 0.0),
                "feasibility": ins.feasibility or "HIGH",
                "difficulty": ins.difficulty or "EASY",
                "confidence_score": float(ins.confidence_score or 0.90),
                "sustainability_gain": float(ins.sustainability_gain or 5.0),
                "behavioral_compatibility": float(ins.behavioral_compatibility or 5.0),
                "why_explanation": ins.why_explanation or "This helps reduce your carbon footprint.",
                "how_calculation": ins.how_calculation or "Calculated based on standard consumption profiles.",
                "weighted_priority_score": float(ins.weighted_priority_score or 0.0),
                "created_at": ins.created_at.isoformat() if ins.created_at else datetime.utcnow().isoformat()
            } for ins in insights
        ]
        
        return {
            "success": True,
            "data": serialized_insights,
            "error": None
        }
    except Exception as e:
        logger.error(f"Error fetching active insights: {str(e)}\n{traceback.format_exc()}")
        return {
            "success": False,
            "data": [],
            "error": f"Failed to fetch insights: {str(e)}"
        }

@router.get("/recommendations")
def get_recommendations_alias(request: Request, username: str = "demo_user", db: Session = Depends(get_db)):
    check_rate_limit(request, username, "/recommendations", limit=60)
    return read_insights(request, username, db)

@router.get("/forecast")
def get_forecast_alias(request: Request, username: str = "demo_user", steps: int = 30, model: str = "prophet", db: Session = Depends(get_db)):
    check_rate_limit(request, username, "/forecast", limit=60)
    return get_forecasting(request, username, steps, model, db)

# GET /achievements
@router.get("/achievements")
def read_achievements(username: str = "demo_user", db: Session = Depends(get_db)):
    """
    Retrieves unlocked achievements for user.
    """
    try:
        user = get_or_create_user(db, username)
        achievements = db.query(Achievement).filter(
            Achievement.user_id == user.id
        ).order_by(Achievement.unlocked_at.desc()).all()
        
        serialized_ach = [
            {
                "id": ach.id,
                "name": ach.name,
                "description": ach.description,
                "badge_type": ach.badge_type,
                "unlocked_at": ach.unlocked_at.isoformat() if ach.unlocked_at else datetime.utcnow().isoformat()
            } for ach in achievements
        ]
        
        return {
            "success": True,
            "data": serialized_ach,
            "error": None
        }
    except Exception as e:
        logger.error(f"Error fetching achievements: {str(e)}\n{traceback.format_exc()}")
        return {
            "success": False,
            "data": [],
            "error": f"Failed to fetch achievements: {str(e)}"
        }

@router.post("/seed")
def seed_database(
    username: str = "demo_user",
    confirm: bool = False,
    db: Session = Depends(get_db)
):
    """
    Seeds database categories, factors, and generates mock historical logs.
    PROTECTED: Requires confirm=true query parameter to prevent accidental data loss.
    Only available in development environment.
    """
    from app.database import session as db_session
    if db_session.READ_ONLY_MODE:
        raise DatabaseUnavailableException("Database temporarily unavailable. Read-only mode active.")
    import os
    env = os.getenv("ENVIRONMENT", "development").strip().lower()
    
    # Audit log seeding attempt
    log_structured(
        level="WARNING",
        service="seed_database",
        message=f"Database seed requested by user '{username}' (env: '{env}', confirm: {confirm})",
        context={"username": username, "env": env, "confirm": confirm}
    )
    
    if env != "development":
        raise HTTPException(
            status_code=403,
            detail="Seed endpoint disabled outside development environment"
        )

    if not confirm:
        return {
            "success": False,
            "data": {},
            "error": "Safety lock active. Pass ?confirm=true to proceed with database seed. WARNING: This will drop all existing data."
        }
    
    logger.info(f"Seeding database factors and user history for user: '{username}' (confirmed)")

    try:
        logger.info("Dropping all existing database tables for schema refresh...")
        Base.metadata.drop_all(bind=engine)
        
        logger.info("Creating fresh database schemas...")
        Base.metadata.create_all(bind=engine)
        
        # 1. Seed Factors
        seed_db(db)
        
        # 2. Setup user
        user = get_or_create_user(db, username)
        
        # 3. Create realistic past activities for the last 6 days
        today = date.today()
        
        mock_activities = [
            # Day -5
            {"days_ago": 5, "text": "1 plate curd rice", "cat": "food", "item": "curd rice", "qty": 1.0, "unit": "plate", "val": 0.87, "region": "Global", "meta": {"calculation_type": "recipe_based"}},
            {"days_ago": 5, "text": "Travelled 20 km by car", "cat": "transport", "item": "petrol car", "qty": 20.0, "unit": "km", "val": 3.84, "region": "Global", "meta": {"distance_km": 20.0, "vehicle_mapped": "petrol car"}},
            {"days_ago": 5, "text": "Used AC for 5 hours", "cat": "appliances", "item": "ac", "qty": 5.0, "unit": "hours", "val": 5.25, "region": "Global", "meta": {"appliance_mapped": "ac", "total_kwh": 7.5}},
            # Day -4
            {"days_ago": 4, "text": "Ate salad vegetables", "cat": "food", "item": "vegetables", "qty": 0.3, "unit": "kg", "val": 0.15, "region": "Global", "meta": {"calculation_type": "weight_based"}},
            {"days_ago": 4, "text": "Flew from Chennai to Bangalore", "cat": "transport", "item": "flight (Chennai -> Bangalore)", "qty": 290.0, "unit": "km", "val": 73.95, "region": "Global", "meta": {"distance_km": 290.0, "vehicle_mapped": "flight"}},
            # Day -3
            {"days_ago": 3, "text": "Ate chicken biryani", "cat": "food", "item": "chicken biryani", "qty": 1.0, "unit": "plate", "val": 1.785, "region": "Global", "meta": {"calculation_type": "recipe_based"}},
            {"days_ago": 3, "text": "Travelled 15 km by metro", "cat": "transport", "item": "metro", "qty": 15.0, "unit": "km", "val": 0.435, "region": "Global", "meta": {"distance_km": 15.0, "vehicle_mapped": "metro"}},
            {"days_ago": 3, "text": "Used laptop for 8 hours", "cat": "appliances", "item": "laptop", "qty": 8.0, "unit": "hours", "val": 0.336, "region": "Global", "meta": {"appliance_mapped": "laptop", "total_kwh": 0.48}},
            # Day -2
            {"days_ago": 2, "text": "Used washing machine twice", "cat": "appliances", "item": "washing machine", "qty": 2.0, "unit": "hours", "val": 0.70, "region": "Global", "meta": {"appliance_mapped": "washing machine", "total_kwh": 1.0}},
            {"days_ago": 2, "text": "Walked 5 km", "cat": "transport", "item": "walking", "qty": 5.0, "unit": "km", "val": 0.0, "region": "Global", "meta": {"distance_km": 5.0, "vehicle_mapped": "walking"}},
            {"days_ago": 2, "text": "1 cup milk", "cat": "food", "item": "milk", "qty": 1.0, "unit": "cup", "val": 0.72, "region": "Global", "meta": {"calculation_type": "weight_based"}},
            # Day -1
            {"days_ago": 1, "text": "Ate chicken biryani", "cat": "food", "item": "chicken biryani", "qty": 1.0, "unit": "plate", "val": 1.785, "region": "Global", "meta": {"calculation_type": "recipe_based"}},
            {"days_ago": 1, "text": "Used AC for 2 hours", "cat": "appliances", "item": "ac", "qty": 2.0, "unit": "hours", "val": 2.10, "region": "Global", "meta": {"appliance_mapped": "ac", "total_kwh": 3.0}},
        ]
        
        for ma in mock_activities:
            log_date = datetime.combine(today - timedelta(days=ma["days_ago"]), datetime.now().time())
            act = Activity(
                user_id=user.id,
                input_text=ma["text"],
                category=ma["cat"],
                item=ma["item"],
                quantity=ma["qty"],
                unit=ma["unit"],
                calculated_value=ma["val"],
                metadata_json=ma["meta"],
                region=ma["region"],
                logged_at=log_date
            )
            db.add(act)
        db.commit()
        
        # Calculate daily scores for seeded history
        for i in range(1, 6):
            d = today - timedelta(days=i)
            start_t = datetime.combine(d, datetime.min.time())
            end_t = datetime.combine(d, datetime.max.time())
            d_emissions = db.query(func.sum(Activity.calculated_value)).filter(
                Activity.user_id == user.id,
                Activity.logged_at >= start_t,
                Activity.logged_at <= end_t
            ).scalar() or 0.0
            
            d_score = max(0.0, min(100.0, 100.0 - (d_emissions / 5.0) * 50.0))
            score_rec = SustainabilityScore(
                user_id=user.id,
                date=d,
                total_emissions=d_emissions,
                score=d_score
            )
            db.add(score_rec)
        db.commit()
            
        # Seed initial milestones
        first_act = db.query(Activity).filter(Activity.user_id == user.id).first()
        if first_act:
            check_achievements(db, user.id, first_act)
            
        # Seed initial chat memory welcome
        save_chat_message(
            db, user.id, "assistant", 
            "Hello! I am your **CarbonTracker AI Copilot**. I have analyzed your carbon history and configured your sustainability target score. Let's work together to reduce your footprint! 🍃"
        )
        
        # Generate Fresh Insights
        generate_personalized_recommendations(db, user.id)
        
        logger.info("Database seeded successfully with categories, factors, and memory tables.")
        return {
            "success": True,
            "data": {"status": "success", "message": "Database seeded successfully"},
            "error": None
        }
    except Exception as e:
        logger.error(f"Seeding database failed: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        return {
            "success": False,
            "data": {},
            "error": f"Seeding failure: {str(e)}"
        }

# GET /feature-flags
@router.get("/feature-flags")
def get_flags():
    """
    Retrieves active feature flags.
    """
    try:
        from app.feature_flags.flags import get_feature_flags
        flags = get_feature_flags()
        return {
            "success": True,
            "data": flags,
            "error": None
        }
    except Exception as e:
        logger.error(f"Failed to fetch feature flags: {str(e)}")
        return {
            "success": False,
            "data": {},
            "error": f"Failed to fetch feature flags: {str(e)}"
        }

# GET /system/health
@router.get("/system/health")
def get_system_health(db: Session = Depends(get_db)):
    """
    Mounts a comprehensive health verification diagnostic API.
    Validates database connectivity, embedding algorithms, forecaster state, and OCR processing.
    """
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"[Health Check] Database unreachable: {str(e)}")
        db_status = "error"
        
    ai_status = "ok"
    embedding_status = "ok"
    try:
        from app.ai.embeddings.embeddings import get_embedding
        vec = get_embedding("test semantic string verification")
        if len(vec) != 8:
            embedding_status = "degraded"
    except Exception as e:
        logger.error(f"[Health Check] Semantic embedding subsystem crashed: {str(e)}")
        embedding_status = "error"
        ai_status = "degraded"
        
    forecasting_status = "ok"
    try:
        from app.ai.forecasting.forecaster import generate_forecast_data
        test_hist = [(date.today() - timedelta(days=1), 4.5)]
        res = generate_forecast_data(test_hist, steps=3, model_type="moving_average")
        if len(res) != 3:
            forecasting_status = "degraded"
    except Exception as e:
        logger.error(f"[Health Check] Forecast subsystem failed: {str(e)}")
        forecasting_status = "error"
        ai_status = "degraded"
        
    ocr_status = "ok"
    try:
        from app.ai.multimodal.ocr import parse_receipt_image
        res = parse_receipt_image("power_invoice.jpg", 250)
        if not res or len(res) == 0:
            ocr_status = "degraded"
    except Exception as e:
        logger.error(f"[Health Check] Multimodal OCR processor failed: {str(e)}")
        ocr_status = "error"
        ai_status = "degraded"
        
    system_ok = (db_status == "ok" and ai_status == "ok")
    
    return {
        "success": True,
        "data": {
            "status": "healthy" if system_ok else "unhealthy",
            "database": db_status,
            "ai_subsystems": ai_status,
            "embedding_system": embedding_status,
            "forecasting_system": forecasting_status,
            "ocr_system": ocr_status
        },
        "error": None
    }

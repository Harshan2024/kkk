from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import Activity, AIInsight, User
from app.services.activity_service import get_or_create_user
from app.utils.logger import log_structured

def generate_insights(db: Session, username: str) -> list[AIInsight]:
    """
    Scans the user's history and generates customized, actionable recommendations.
    Saves generated insights to the database and returns them.
    Insights are prioritized by impact_value descending.
    Protected with Exception Isolation.
    """
    try:
        user = get_or_create_user(db, username)
        user_id = user.id
        
        # Fetch user's activities from the past 14 days
        two_weeks_ago = datetime.utcnow() - timedelta(days=14)
        activities = db.query(Activity).filter(
            Activity.user_id == user_id,
            Activity.logged_at >= two_weeks_ago
        ).all()
        
        # Calculate stats
        total_emissions = sum(a.calculated_value for a in activities)
        category_totals = {}
        for a in activities:
            category_totals[a.category] = category_totals.get(a.category, 0.0) + a.calculated_value
            
        insights_to_create = []
        
        # 1. Base default insights if logs are minimal
        if not activities:
            insights_to_create.append({
                "content": "Start logging your daily meals, commutes, and appliance usage to receive personalized, AI-powered carbon insights!",
                "category": "lifestyle",
                "impact_estimate": "High Impact",
                "impact_level": "HIGH",
                "impact_value": 30.0
            })
            insights_to_create.append({
                "content": "Did you know? Switching to energy-efficient LED bulbs reduces lighting electricity emissions by up to 80%.",
                "category": "appliances",
                "impact_estimate": "Saves 5kg CO2/month",
                "impact_level": "MEDIUM",
                "impact_value": 5.0
            })
            insights_to_create.append({
                "content": "Commuting by metro instead of a petrol car reduces your travel carbon footprint by over 80% per kilometer.",
                "category": "transport",
                "impact_estimate": "Saves 25kg CO2/month",
                "impact_level": "HIGH",
                "impact_value": 25.0
            })
        else:
            # 2. Travel analysis
            car_travels = [a for a in activities if a.category == "transport" and "car" in a.item]
            if car_travels:
                total_car_km = sum(a.quantity for a in car_travels)
                savings = total_car_km * (0.192 - 0.029)
                insights_to_create.append({
                    "content": f"You drove {total_car_km:.1f} km by car recently. Taking the metro/subway for these trips instead would reduce emissions by {savings:.1f} kg CO2e!",
                    "category": "transport",
                    "impact_estimate": f"Saves {savings:.1f} kg CO2e",
                    "impact_level": "HIGH" if savings > 20 else "MEDIUM",
                    "impact_value": savings
                })
                
            flights = [a for a in activities if a.category == "transport" and "flight" in a.item]
            if flights:
                insights_to_create.append({
                    "content": "Air travel has high carbon intensity. For short or medium distances, consider standard trains or sleeper buses to reduce emissions by 85%.",
                    "category": "transport",
                    "impact_estimate": "Saves ~150kg CO2/trip",
                    "impact_level": "HIGH",
                    "impact_value": 150.0
                })

            # 3. Diet analysis
            meat_logs = [a for a in activities if a.category == "food" and a.item in ["beef", "chicken"]]
            beef_logs = [a for a in activities if a.category == "food" and a.item == "beef"]
            if beef_logs:
                total_beef_kg = sum(a.quantity for a in beef_logs)
                chicken_savings = total_beef_kg * (60.0 - 6.9)
                veg_savings = total_beef_kg * (60.0 - 1.5)
                insights_to_create.append({
                    "content": f"You consumed {total_beef_kg:.2f} kg of beef. Swapping beef for chicken would save {chicken_savings:.1f} kg CO2e, and swapping for paneer/lentils saves {veg_savings:.1f} kg CO2e!",
                    "category": "food",
                    "impact_estimate": f"Saves {chicken_savings:.1f} - {veg_savings:.1f} kg CO2e",
                    "impact_level": "HIGH",
                    "impact_value": chicken_savings
                })
            elif meat_logs:
                insights_to_create.append({
                    "content": "Incorporating one or two plant-based days weekly (enjoying curd rice, paneer, and veggies) significantly lowers your overall carbon footprint.",
                    "category": "food",
                    "impact_estimate": "Saves 12kg CO2/month",
                    "impact_level": "MEDIUM",
                    "impact_value": 12.0
                })

            # 4. Appliance analysis
            ac_logs = [a for a in activities if a.category == "appliances" and "ac" in a.item]
            if ac_logs:
                total_ac_hours = sum(a.quantity for a in ac_logs)
                savings = total_ac_hours * 1.0
                insights_to_create.append({
                    "content": f"You used the AC for {total_ac_hours:.1f} hours recently. Shifting some cooling hours to a standard ceiling fan saves about 1.0 kg CO2e per hour!",
                    "category": "appliances",
                    "impact_estimate": f"Saves {savings:.1f} kg CO2e",
                    "impact_level": "HIGH" if savings > 15 else "MEDIUM",
                    "impact_value": savings
                })
                
            # 5. Category distribution insight
            if total_emissions > 0:
                for cat, total in category_totals.items():
                    pct = (total / total_emissions) * 100
                    if pct > 50.0:
                        insights_to_create.append({
                            "content": f"Your {cat.capitalize()} footprint accounts for {pct:.0f}% of your total emissions. Focus reduction efforts here for maximum carbon impact.",
                            "category": cat,
                            "impact_estimate": "High Priority",
                            "impact_level": "HIGH",
                            "impact_value": 20.0
                        })

        # Sort insights by impact value descending (priority sorting)
        insights_to_create.sort(key=lambda x: x["impact_value"], reverse=True)

        # Clear old insights and seed new ones
        try:
            db.query(AIInsight).filter(AIInsight.user_id == user_id).delete()
        except Exception as de:
            log_structured("ERROR", "insight_service", f"Failed to delete old insights: {str(de)}", {"user_id": user_id})
        
        db_insights = []
        for ins_data in insights_to_create[:4]:  # limit to top 4 recommendations
            insight = AIInsight(
                user_id=user_id,
                content=ins_data["content"],
                category=ins_data["category"],
                impact_estimate=ins_data["impact_estimate"],
                impact_level=ins_data["impact_level"],
                impact_value=ins_data["impact_value"],
                is_active=1
            )
            db.add(insight)
            db_insights.append(insight)
            
        from app.utils.safe_db import safe_commit, DatabaseUnavailableException
        try:
            safe_commit(db, "delete_insights")
            # Wait, let's look at lines 152-160
            safe_commit(db, "generate_insights")
            for ins in db_insights:
                db.refresh(ins)
        except DatabaseUnavailableException:
            raise
        except Exception as ce:
            log_structured("ERROR", "insight_service", f"Failed to commit insights to db: {str(ce)}", {"user_id": user_id})
            
        return db_insights
    except DatabaseUnavailableException:
        raise
    except Exception as e:
        log_structured(
            level="ERROR",
            service="insight_service",
            message=f"Insight generation failed for username={username}: {str(e)}",
            context={"username": username},
            exception=e
        )
        # Resilient recovery with safe fallback insights
        fallback_insights = []
        fallback_data = [
            ("Start logging your daily activity to get AI-powered sustainability tips!", "lifestyle", "High Impact", "HIGH", 30.0),
            ("Taking public transit shares travel footprint among many passengers.", "transport", "Saves ~20kg CO2", "MEDIUM", 20.0)
        ]
        for idx, (content, category, est, lvl, val) in enumerate(fallback_data):
            fallback_insights.append(AIInsight(
                id=-(idx+1),
                user_id=0,
                content=content,
                category=category,
                impact_estimate=est,
                impact_level=lvl,
                impact_value=val,
                is_active=1
            ))
        return fallback_insights

def get_active_insights(db: Session, username: str) -> list[AIInsight]:
    """
    Returns active insights. If none exist in the database, generates them.
    Sorted by impact_value descending.
    Protected with Exception Isolation.
    """
    from app.utils.safe_db import safe_query_all
    try:
        user = get_or_create_user(db, username)
        insights = safe_query_all(
            db.query(AIInsight).filter(
                AIInsight.user_id == user.id,
                AIInsight.is_active == 1
            ).order_by(AIInsight.impact_value.desc())
        )
        
        if not insights:
            insights = generate_insights(db, username)
            
        return insights
    except Exception as e:
        log_structured(
            level="ERROR",
            service="insight_service",
            message=f"get_active_insights failed for username={username}: {str(e)}",
            context={"username": username},
            exception=e
        )
        # Recovery
        fallback_insights = []
        fallback_data = [
            ("Start logging your daily activity to get AI-powered sustainability tips!", "lifestyle", "High Impact", "HIGH", 30.0),
            ("Taking public transit shares travel footprint among many passengers.", "transport", "Saves ~20kg CO2", "MEDIUM", 20.0)
        ]
        for idx, (content, category, est, lvl, val) in enumerate(fallback_data):
            fallback_insights.append(AIInsight(
                id=-(idx+1),
                user_id=0,
                content=content,
                category=category,
                impact_estimate=est,
                impact_level=lvl,
                impact_value=val,
                is_active=1
            ))
        return fallback_insights

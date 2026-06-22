import sys
import os
from datetime import date, timedelta

# Adjust python path to include parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.habit_analysis.category_analyzer import analyze_categories
from app.habit_analysis.score_engine import calculate_sustainability_score
from app.habit_analysis.trend_engine import calculate_trend
from app.habit_analysis.risk_engine import calculate_risk
from app.habit_analysis.recommendation_engine import generate_recommendations
from app.habit_analysis.habit_analysis_service import analyze_user_habits

def run_tests():
    print("====================================================")
    print("RUNNING HABIT ANALYSIS ENGINE TEST SUITE")
    print("====================================================")
    
    # Mock data sets
    today = date.today()
    yesterday = today - timedelta(days=1)
    day_before = today - timedelta(days=2)
    
    # 1. Low footprint, stable trend
    low_emissions_activities = [
        {"category": "transport", "item": "bicycle", "calculated_value": 0.0, "logged_at": today},
        {"category": "food", "item": "salad", "calculated_value": 0.5, "logged_at": today},
        {"category": "energy", "item": "led lights", "calculated_value": 0.2, "logged_at": yesterday},
        {"category": "waste", "item": "paper recycling", "calculated_value": 0.1, "logged_at": yesterday},
    ]
    
    # 2. High footprint, increasing trend
    high_increasing_activities = [
        {"category": "transport", "item": "SUV drive", "calculated_value": 2.0, "logged_at": day_before},
        {"category": "food", "item": "chicken biriyani", "calculated_value": 3.0, "logged_at": yesterday},
        {"category": "energy", "item": "AC usage", "calculated_value": 4.0, "logged_at": yesterday},
        {"category": "transport", "item": "SUV drive 2", "calculated_value": 10.0, "logged_at": today},
        {"category": "food", "item": "mutton biriyani", "calculated_value": 6.0, "logged_at": today},
    ]
    
    # Test Category Analyzer
    print("Testing Category Analyzer...")
    cat_res = analyze_categories(low_emissions_activities)
    assert cat_res["total_emissions"] == 0.8, f"Expected 0.8, got {cat_res['total_emissions']}"
    assert cat_res["breakdown"]["food"] == 62.5, f"Expected 62.5, got {cat_res['breakdown']['food']}"
    assert cat_res["breakdown"]["energy"] == 25.0, f"Expected 25.0, got {cat_res['breakdown']['energy']}"
    print("[OK] Category Analyzer passed.")
    
    # Test Score Engine
    print("Testing Score Engine...")
    score_low = calculate_sustainability_score(low_emissions_activities)
    assert score_low["score"] == 100.0, f"Expected 100.0 score, got {score_low['score']}"
    
    score_high = calculate_sustainability_score(high_increasing_activities)
    # total emissions: day_before = 2.0, yesterday = 7.0, today = 16.0.
    # average: (2+7+16)/3 = 8.33 kg CO2.
    # score: 100 - ((8.33 - 3.0) / 12.0) * 100.0 = 55.6.
    assert 54.0 <= score_high["score"] <= 57.0, f"Expected around 55.6, got {score_high['score']}"
    print("[OK] Score Engine passed.")
    
    # Test Trend Engine
    print("Testing Trend Engine...")
    trend_low = calculate_trend(low_emissions_activities)
    assert trend_low == "stable", f"Expected stable, got {trend_low}"
    
    trend_high = calculate_trend(high_increasing_activities)
    assert trend_high == "increasing", f"Expected increasing, got {trend_high}"
    print("[OK] Trend Engine passed.")
    
    # Test Risk Engine
    print("Testing Risk Engine...")
    risk_low = calculate_risk(0.4, "stable")
    assert risk_low == "low", f"Expected low, got {risk_low}"
    
    risk_high = calculate_risk(8.33, "increasing")
    assert risk_high == "high", f"Expected high, got {risk_high}"
    
    risk_med = calculate_risk(6.0, "stable")
    assert risk_med == "medium", f"Expected medium, got {risk_med}"
    print("[OK] Risk Engine passed.")
    
    # Test Recommendation Engine
    print("Testing Recommendation Engine...")
    recs = generate_recommendations(cat_res, low_emissions_activities)
    assert len(recs) >= 1, "Expected at least one recommendation"
    print("[OK] Recommendation Engine passed.")
    
    # Test Unified Service
    print("Testing Unified Service...")
    service_res = analyze_user_habits(high_increasing_activities, "test_user")
    assert service_res["username"] == "test_user"
    assert service_res["data"]["trend"] == "increasing"
    assert service_res["data"]["risk_level"] == "high"
    assert len(service_res["data"]["recommendations"]) > 0
    assert "details" in service_res["data"]
    print("[OK] Unified Service passed.")
    
    print("\n====================================================")
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("====================================================")

if __name__ == "__main__":
    run_tests()

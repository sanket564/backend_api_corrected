# utils/leave_utils.py
from datetime import datetime

def calculate_dynamic_leave_balance(join_date_str, total_days_taken):
    today = datetime.now().date()
    join_date = datetime.strptime(join_date_str, "%Y-%m-%d").date()
    days_since_join = (today - join_date).days
    months_since_join = days_since_join // 30

    if days_since_join <= 90:
        # Probation period: 1 PL per month, must be used in probation
        total_earned = min(months_since_join, 3)
        expired = max(0, total_earned - total_days_taken)
        return {
            "stage": "Probation",
            "earned": total_earned,
            "used": total_days_taken,
            "available": max(total_earned - total_days_taken, 0),
            "note": "Unused PLs must be used within probation"
        }

    elif days_since_join >= 365:
        # After 1 year: 20 PLs per year, 5 can be carried forward
        total_earned = 20
        carry_forward = max(0, 5 - total_days_taken)
        return {
            "stage": "Annual",
            "earned": total_earned,
            "used": total_days_taken,
            "available": max(total_earned - total_days_taken, 0),
            "carry_forward_next_year": carry_forward
        }

    else:
        # Post-probation: 5 PLs per quarter
        quarters = (months_since_join - 3) // 3
        total_earned = max(quarters * 5, 0)
        return {
            "stage": "Post-Probation",
            "earned": total_earned,
            "used": total_days_taken,
            "available": max(total_earned - total_days_taken, 0)
        }

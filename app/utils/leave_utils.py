from datetime import datetime

def calculate_dynamic_leave_balance(join_date_str, leaves_taken=0):
    today = datetime.now().date()
    join_date = datetime.strptime(join_date_str, "%Y-%m-%d").date()
    days_since_join = (today - join_date).days
    months_since_join = days_since_join // 30

    # 1️⃣ Probation Period: first 3 months
    if days_since_join <= 90:
        # Max 3 PLs during probation
        pl_earned = min(months_since_join, 3)
        # Probation PLs must be used within probation
        pl_balance = max(0, pl_earned - leaves_taken)
        return {
            "type": "Probation",
            "earned": pl_earned,
            "used": leaves_taken,
            "balance": pl_balance
        }

    # 2️⃣ Annual leave (after 1 year)
    if days_since_join >= 365:
        # Every Jan 1st: 20 PLs, max 5 carry forward
        current_year = today.year
        year_start = datetime(current_year, 1, 1).date()
        if join_date < year_start:
            total_entitled = 20
        else:
            total_entitled = 0  # Joined this year, accrual logic can vary
        pl_balance = max(0, total_entitled - leaves_taken)
        carry_forward = min(pl_balance, 5)
        return {
            "type": "Annual",
            "entitled": total_entitled,
            "used": leaves_taken,
            "carry_forward": carry_forward,
            "balance": pl_balance
        }

    # 3️⃣ Post-Probation, Before 1 year: 5 PLs/quarter
    quarters = (today.month - join_date.month) // 3
    pl_earned = quarters * 5
    pl_balance = max(0, pl_earned - leaves_taken)
    return {
        "type": "Quarterly",
        "earned": pl_earned,
        "used": leaves_taken,
        "balance": pl_balance
    }

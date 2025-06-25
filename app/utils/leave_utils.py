from datetime import datetime

def calculate_dynamic_leave_balance(join_date):
    today = datetime.now().date()
    join_date = join_date.date()

    days_since_join = (today - join_date).days
    months_since_join = days_since_join // 30

    # Probation logic (first 3 months)
    if days_since_join <= 90:
        return min(months_since_join, 3)  # 1 PL per month

    # Annual leave logic (after 1 year)
    if days_since_join >= 365:
        return 20  # Fixed annual

    # Post-probation: 5 PLs per quarter
    quarters_since_join = (today.month - join_date.month) // 3
    return quarters_since_join * 5

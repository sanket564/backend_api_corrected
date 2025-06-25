def update_leave_balance():
    leave_balances = mongo.db.leave_balances
    users = mongo.db.users
    today = datetime.now().date()

    for record in leave_balances.find():
        email = record["email"]
        join_date = record["join_date"]
        probation_end = record["probation_end"].date()
        last_updated = record["last_updated"].date()
        pl = record.get("pl_balance", 0)

        months_since_last = (today.year - last_updated.year) * 12 + (today.month - last_updated.month)

        if today < probation_end:
            # Probation: 1 PL per month
            pl += months_since_last
        elif (today - join_date.date()).days >= 365:
            # After 1 year: annual credit
            if today.month == 1 and last_updated.month < 1:
                pl = min(pl + 20, 25)  # max carry forward 5
        else:
            # Post-probation: 5 PLs per quarter
            quarters_passed = (today.month - 1) // 3 - (last_updated.month - 1) // 3
            if quarters_passed > 0:
                pl += quarters_passed * 5

        leave_balances.update_one({"email": email}, {
            "$set": {
                "pl_balance": pl,
                "last_updated": datetime.now()
            }
        })

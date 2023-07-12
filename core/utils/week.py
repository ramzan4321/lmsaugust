from datetime import date, timedelta

def current_week():
    # Get the current date
    current_date = date.today()

    # Get the current week's start and end dates
    current_week_start = current_date - timedelta(days=current_date.weekday())

    # Generate the current week's days
    current_week_days = [current_week_start + timedelta(days=i) for i in range(7)]
    return {"current_week_days": current_week_days,"current_week_start": current_week_start}

def next_week(week_start_date):
    next_week_start = week_start_date + timedelta(weeks=1)

    next_week_days = [next_week_start + timedelta(days=i) for i in range(7)]
    return {"current_week_days": next_week_days,"current_week_start": next_week_start}

def pre_week(week_start_date):
    pre_week_start = week_start_date - timedelta(weeks=1)
    pre_week_days = [pre_week_start + timedelta(days=i) for i in range(7)]
    return {"current_week_days": pre_week_days,"current_week_start": pre_week_start}
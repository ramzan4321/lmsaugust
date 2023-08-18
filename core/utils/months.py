from datetime import date, timedelta

def months():
    today = date.today()
    cur_month = today.replace(day=1)
    next = prev = None
    xl = []
    xl.append(today)
    for _ in range(6):
        if not next:
            next = (cur_month + timedelta(days=32)).replace(day=1)
        if not prev:
            prev = (cur_month - timedelta(days=1))
        xl.insert(0, prev)
        xl.append(next)
        next = (next + timedelta(days=32)).replace(day=1)
        prev = (prev.replace(day=1) - timedelta(days=1))

    print(list(xl[1:]))
months()
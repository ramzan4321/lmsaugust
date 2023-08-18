from datetime import date, timedelta
import calendar
holiday_list = [date.today().replace(day=26, month=1), date.today().replace(day=15, month=8)]

class Date:
    #for get all leave dates 

    def __init__(self, _date):
        self._date = _date if _date else date.today()
    
    def get_next_working_days(self, num):
        _dates, count = [], 0
        _day = self._date
        print("_day type: ", type(_day), _day)
        while num > count:
            if self.is_weekend(_day) or self.is_holiday(_day):
                _day = _day + timedelta(days=1)
                continue
            _dates.append(_day)
            _day = _day + timedelta(days=1)
            count += 1
        return _dates

    def is_weekend(self, date_obj):
        return date_obj.strftime("%a") in ["Sat", "Sun"]

    def is_holiday(self, date_obj):
        return  date_obj in holiday_list
    
    def total_days(self):
        _date = self._date
        return calendar.monthrange(_date.year, _date.month)[1]

    def prev_month(self):
        return self._date.replace(day=1) - timedelta(days=1)
        # return calendar.monthrange(_date.year, _date.month)[1]

    def get_semesters(self):
        if self._date.month in [1,6]:
            return (self._date.replace(day=1, month=7, year= self._date.year-1),
            self._date.replace(day=31, month=12,  year=self._date.year-1))
        return (self._date.replace(day=1, month=1),
            self._date.replace(day=30, month=6))

if __name__ == "__main__":
    _date = Date()
    print(_date.get_next_working_days(20))

def months():
    today = date.today()
    cur_month = today.replace(day=1)
    next = prev = None
    twelve_months = []
    twelve_months.append(today)
    for _ in range(6):
        if not next:
            next = (cur_month + timedelta(days=32)).replace(day=1)
        if not prev:
            prev = (cur_month - timedelta(days=1))
        twelve_months.insert(0, prev)
        twelve_months.append(next)
        next = (next + timedelta(days=32)).replace(day=1)
        prev = (prev.replace(day=1) - timedelta(days=1))
    return twelve_months[1:]
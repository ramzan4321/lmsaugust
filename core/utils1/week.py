from datetime import date, timedelta, datetime
from core.utils.dates import Date, months
from hrm.models import Employee, LeaveManagement

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

def week_calendar(type=None, week=None):
    if type == None:
        current_week_days = current_week()['current_week_days']
        emp_leave_list = []
        all_emp = Employee.objects.all()
        for emp in all_emp:
            tmp_leave_list = []
            emp_leave = LeaveManagement.objects.filter(employee_id=emp,status="APPROVED")
            if emp_leave:
                for y in emp_leave:
                    y_days_in_leave = Date(y.leave_start_date).get_next_working_days(y.leave_days)

                    for day in current_week_days:

                        if day in y_days_in_leave:
                            tmp_leave_list.append(day.day)
            emp_leave_list.append({"name":emp.name, "image": emp.profile_image, "leave_list": tmp_leave_list})
        return emp_leave_list
    else:
        current_week_start = datetime.strptime(week, '%Y-%m-%d').date()
        if type == "prev":
            current_week_days = pre_week(current_week_start)['current_week_days']
            current_week_start = pre_week(current_week_start)['current_week_start']
        else:
            current_week_days = next_week(current_week_start)['current_week_days']
            current_week_start = next_week(current_week_start)['current_week_start']
        cu_week_days = [x.day for x in current_week_days]
        emp_leave_list = []
        all_emp = Employee.objects.all()
        for emp in all_emp:
            tmp_leave_list = []
            emp_leave = LeaveManagement.objects.filter(employee_id=emp,status="APPROVED")

            if emp_leave:
                for y in emp_leave:
                    y_days_in_leave = Date(y.leave_start_date).get_next_working_days(y.leave_days)
                    for day in current_week_days:
                        if day in y_days_in_leave:
                            tmp_leave_list.append(day.day)
            emp_leave_list.append({"name":emp.name, "image": str(emp.profile_image), "leave_list": tmp_leave_list})
        json_data = {
            'status': 'found',
            "emp_leave_list": emp_leave_list,
            "current_week_days": cu_week_days,
            "current_week_start": current_week_start,
            "next_date": current_week_days[-1].strftime("%b %d"),
            "prev_date": current_week_days[0].strftime("%b %d"),
        }
        return json_data
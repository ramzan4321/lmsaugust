from core.utils.dates import Date
from hrm.models import LeaveManagement, Employee
from datetime import timedelta, date

def all_leaves(employee):
    leaves = LeaveManagement.objects.filter(employee_id=employee).order_by('-id')
    tmp_list = []
    for leave in leaves:
        tmp_dict = {}
        tmp_dict["leave_reason"] = leave.leave_reason
        tmp_dict["leave_days"] = leave.leave_days
        tmp_dict["leave_start_date"] = leave.leave_start_date
        tmp_dict["leave_type"] = leave.leave_type
        tmp_dict["leave_requested_for"] = leave.leave_requested_for
        tmp_dict["status"] = leave.status
        tmp_dict["id"] = leave.id

        two_days_ago = leave.leave_start_date - timedelta(days=2)

        if date.today() > two_days_ago:
            tmp_dict["action"] = True
        else:
            tmp_dict["action"] = False

        tmp_list.append(tmp_dict)
    return tmp_list

def employee_leave_check(employee, start_date, requested_leave_days, leave_id=None):
    if leave_id:
        oldleave = LeaveManagement.objects.filter(employee_id=employee, leave_start_date__month__range=[(start_date.month-1),(start_date.month+1)]).exclude(id=leave_id)
    else:
        oldleave = LeaveManagement.objects.filter(employee_id=employee, leave_start_date__month__range=[(start_date.month-1),(start_date.month+1)]).exclude(status="REJECTED")
    for x in oldleave:
        days_in_leave = Date(x.leave_start_date).get_next_working_days(x.leave_days)
        for y in requested_leave_days:
            if y in days_in_leave:
                return {"status": True, "date": y}
            else:
                continue
    return {"status": False}

def leave_can_approve(leave):
    department = leave.employee_id.department
    employees = Employee.objects.filter(department=department)
    _date = Date(leave.leave_start_date)
    requested_leave_days = _date.get_next_working_days(leave.leave_days)
    emp_list = []
    month = []
    for day in requested_leave_days:
        if day.month not in month:
            month.append(day.month)
    print("Month: ", month)
    for employee in employees:
        for _month in month:
            leaves_in_month = LeaveManagement.objects.filter(employee_id=employee, leave_start_date__month=_month, status="APPROVED")
            for _leave in leaves_in_month:
                _date_ = Date(_leave.leave_start_date)
                _requested_leave_days = _date_.get_next_working_days(_leave.leave_days)
                for y in _requested_leave_days:
                    if y in requested_leave_days:
                        if employee.user.username not in emp_list:
                            emp_list.append(employee.user.username)
    perc = (len(emp_list)/employees.count())*100
    if perc >= 50:
        return {"status":True, "percentage": perc}
    else:
        return {"status":False, "percentage": perc}

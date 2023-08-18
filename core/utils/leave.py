from core.utils.dates import Date
from hrm.models import LeaveManagement, Employee
from datetime import timedelta, date
from django.db.models import Q

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
        oldleave = LeaveManagement.objects.filter(employee_id=employee, leave_start_date__month__range=[(start_date.month-1),(start_date.month+1)]).exclude(status="REJECTED", id=leave_id)
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
    

def leave_calculate(employee, days_in_month, month):
    total_leave_days = 0
    full_day = 0
    half_day = 0
    employee_leave = LeaveManagement.objects.filter(employee_id=employee, status="APPROVED", leave_type="UNPAID", leave_start_date__month=month)
    print("EMPLOYEE: ", employee, total_leave_days, employee_leave)
    for leave in employee_leave:
        if leave.leave_start_date.month == month:
            if leave.leave_requested_for == "F":
                full_day += 1
                total_leave_days += leave.leave_days*1
            else:
                half_day += 1
                total_leave_days += leave.leave_days*0.5
    days_payable = days_in_month-total_leave_days
    return {
        "full_day": full_day,
        "half_day": half_day,
        "total_leave_days": total_leave_days,
        "days_payable": days_payable,
    }


def leave_create(emp, leave_reason, leave_days, leave_requested_for, leave_type, start_date, leave_id=None):
    _date = Date(start_date)
    requested_leave_days = _date.get_next_working_days(int(leave_days))
    if leave_id:
        leave_check = employee_leave_check(emp, start_date, requested_leave_days, leave_id)
    else:
        leave_check = employee_leave_check(emp, start_date, requested_leave_days)
    if leave_check["status"] == True:
        return {"status": False, "message": f"Leave for '{leave_check['date']}', is already requested."}

    if  leave_type == "PAID" or emp.get_all() >= int(leave_days) :
        if requested_leave_days[-1].month > 6:
            employee_paid_leave = LeaveManagement.objects.filter(Q(employee_id=emp) & ((Q(status="APPROVED") | Q(status="PENDING")) & Q(leave_type="PAID")))
            leave_can_take = 12
        else:
            employee_paid_leave = LeaveManagement.objects.filter(Q(employee_id=emp) & ((Q(status="APPROVED") | Q(status="PENDING")) & Q(leave_type="PAID")) & Q(leave_start_date__month__range=[1,6]))
            leave_can_take = 6
        requested_paid_leave = int(leave_days)
        total_paid_leave = 0
        for leave in employee_paid_leave:
            total_paid_leave = total_paid_leave + leave.leave_days*1 if leave.leave_requested_for == 'F' else leave.leave_days*0.5

        if leave_can_take >= total_paid_leave + requested_paid_leave:
            create_leave = LeaveManagement.objects.create(
                employee_id = emp,
                leave_reason = leave_reason,
                leave_days = leave_days,
                leave_start_date = start_date,
                leave_type = leave_type,
                leave_requested_for = leave_requested_for,
                status = "APPROVED"
            )
            create_leave.save()
            if create_leave:
                return {"status": True, "message": f"Leave has been submitted. You have {leave_can_take -(total_paid_leave+requested_paid_leave)} paid leaves left."}
            else:
                return {"status": False, "error": "Sorry, some thing went wrong."}
        else:
            return {"status": False, "error": "Sorry, You can only take 6 Paid leave during 'January to June' and [6 + remaining] Paid leave  during 'July to December'."}
    else:
        create_leave = LeaveManagement.objects.create(
            employee_id = emp,
            leave_reason = leave_reason,
            leave_days = leave_days,
            leave_start_date = start_date,
            leave_type = leave_type,
            leave_requested_for = leave_requested_for,
            status = "APPROVED"
        )
        create_leave.save()
        if create_leave:
            return {"status": True, "message": "Leave has been submitted."}
        else:
            return {"status": False, "error": "Sorry, some thing went wrong."}


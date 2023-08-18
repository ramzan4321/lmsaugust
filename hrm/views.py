import json
import os
import math
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import CreateView
from hrm.models import HolidayList, Employee, EmployeeManager, EmployeeBankDetail, PaySlip, LeaveManagement, Designations, Departments
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth import authenticate
from core.utils.dates import Date, months
from core.utils.leave import all_leaves as get_all_leaves, employee_leave_check, leave_can_approve, leave_calculate, leave_create
from datetime import date, datetime, timedelta
from core.utils.payslip_pdf import generate_pdf
from core.utils.numtoword import numtowords, fix_to_two_digit
from core.utils.week import current_week, next_week, pre_week, week_calendar
import calendar
from django.contrib import messages
from django.db.models import Sum
from django.db.models import Q
from .forms import LeaveManagementForm, UserRegisterForm, UserEditForm, EmployeeProfileEditForm, AdminEmployeeProfileEditForm, EmployeeBankDetailsEditForm, EmailForm ,SignUpForm, HolidayForm
from django.views.generic import CreateView
from django.shortcuts import get_object_or_404
from hrm.choice import USER_ROLE
from core.utils.mailer import Mailer


class login_user(View):
    template_name = 'hrm/login.html'
    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None: # if user exist
            login(request, user)
            return redirect('/') #re routes to login page upon unsucessful login
        else:
            messages.add_message(request, messages.ERROR, "Please enter correct credentials.")
            return render(request, 'hrm/login.html', {})

class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('/')
    

class EditRegisterUserView(LoginRequiredMixin ,View):
    def post(self, request, *args, **kwargs):
        if request.user.is_superuser:
            user_id = request.POST.get('user-edit-id')
            user = User.objects.get(pk=user_id)
            form = UserEditForm(request.POST)
            if form.is_valid():
                username = form.cleaned_data['username']
                if user.username == username:
                    user.email = form.cleaned_data['email']
                    user.set_password(form.cleaned_data['password1'])
                    user.save()
                else:
                    chk_user_exist = User.objects.filter(username=username).exists()
                    if chk_user_exist:
                        messages.add_message(request, messages.WARNING, "Username already exist.")
                        return redirect('employees')
                    else:
                        user.username = username
                        user.email = form.cleaned_data['email']
                        user.set_password(form.cleaned_data['password1'])
                        user.save()
                request.session['emp_edit_id'] = user.pk
                messages.add_message(request, messages.SUCCESS, "User detail updated successfully.")
                return redirect('employees')
            else:
                error_list = " "
                for field, errors in form.errors.items():
                    if field != 'password2':
                        for error in errors:
                            error_list += error+', '
                error_list = error_list[:-2] +"."
                messages.add_message(request, messages.WARNING, error_list)
                return redirect('employees')
        messages.add_message(request, messages.WARNING, "Only admin access.")
        return redirect('/')



class registerView(CreateView):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect("profile")
        form = UserRegisterForm()
        e_form = EmailForm()
        context = {
            "form": form,
            "e_form": e_form,
        }
        return render(request, "hrm/registration.html", context)

    def post(self, request, *args, **kwargs):
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            userinfo = User.objects.get(username=form.cleaned_data['username'])
            if request.user.is_superuser:
                request.session['emp_edit_id'] = userinfo.pk
                messages.add_message(request, messages.SUCCESS, f"New user has successfully registered.")
                return redirect('employees')
            username = form.cleaned_data.get("username")
            raw_password = form.cleaned_data.get("password1")
            user = authenticate(request, username=username, password=raw_password)
            if user is not None:
                login(request, user)
            messages.add_message(request, messages.SUCCESS, f"Welcome! {user}, You have successfully registered.")
            return redirect('./')
        else:
            error_list = " "
            for field, errors in form.errors.items():
                if field != 'password2':
                    for error in errors:
                        error_list += error+', '
            error_list = error_list[:-2] +"."
            if request.user.is_superuser:
                messages.add_message(request, messages.WARNING, error_list)
                return redirect('employees')
            messages.add_message(request, messages.WARNING, error_list)
            return render(request, 'hrm/registration.html')


# this is for leave management
class LeaveRequestView(View):
    def get(self, request, days=None, start=None, week=None, pk=None, leave_id=None):
        id = request.GET.get('id')
        if request.user.is_superuser:
            if pk:
                employee = get_object_or_404(Employee, pk= pk)
                all_leaves = LeaveManagement.objects.filter(employee_id = employee).order_by('-id')
                paginator = Paginator(all_leaves, 5)

                page_number = request.GET.get('page')
                try:
                    page = paginator.page(page_number)
                except PageNotAnInteger:
                    # If page_number is not an integer, show the first page
                    page = paginator.page(1)
                except EmptyPage:
                    # If page_number is out of range, show the last page
                    page = paginator.page(paginator.num_pages)
                context = {
                    "page":page,
                    "all_leave":all_leaves,
                    "emp":employee,
                    "next_date": current_week()['current_week_days'][-1].strftime("%b %d"),
                    "prev_date": current_week()['current_week_days'][0].strftime("%b %d"),
                    "emp_leave_list": week_calendar(),
                    "current_week_days": current_week()['current_week_days'],
                    "current_week_start": current_week()['current_week_start'].strftime('%Y-%m-%d')
                }
                if request.user.is_superuser and (request.GET.get('q') == "next" or request.GET.get('q') == "prev"):
                    jsondata = week_calendar(request.GET.get('q'), week)
                    if jsondata['status'] == 'found':
                        return JsonResponse(jsondata)
                return render(request, 'admin/emp_leave.html', context)
            pending_leaves = LeaveManagement.objects.filter(status = "PENDING").select_related('employee_id')
            
            if request.user.is_superuser and (request.GET.get('q') == "next" or request.GET.get('q') == "prev"):
                jsondata = week_calendar(request.GET.get('q'), week)
                if jsondata['status'] == 'found':
                    return JsonResponse(jsondata)
            context = {
                "next_date": current_week()['current_week_days'][-1].strftime("%b %d"),
                "prev_date": current_week()['current_week_days'][0].strftime("%b %d"),
                "emp_leave_list": week_calendar(),
                "current_week_days": current_week()['current_week_days'],
                "current_week_start": current_week()['current_week_start'].strftime('%Y-%m-%d'),
                "leaves":pending_leaves
            }
            return render(request, 'admin/leave.html', context)
        try:
            employee = request.user.user_employee

            # Fetching out teammates already on leave during selected period of time.
            if employee.role == 'EMPLOYEE' and request.GET.get('q') == "ajax":
                days_in_leave = Date(datetime.strptime(start, '%Y-%m-%d').date()).get_next_working_days(days)
                emply_list = []
                all_emplys = Employee.objects.filter(department=employee.department, role="EMPLOYEE")
                for x in all_emplys:
                    emplys = LeaveManagement.objects.filter(employee_id=x,status="APPROVED").select_related('employee_id')
                    if emplys:
                        for y in emplys:
                            y_days_in_leave = Date(y.leave_start_date).get_next_working_days(y.leave_days)
                            for day in days_in_leave:
                                if day in y_days_in_leave:
                                    emply_list.append({"name":y.employee_id.name, "image": str(y.employee_id.profile_image)})
                unique_list = []
                [unique_list.append(x) for x in emply_list if x not in unique_list]

                if len(emply_list) > 0:
                    jsondata = {
                        'employees': unique_list,
                    }
                else:
                    jsondata = {
                        'employees': "Not found",
                    }
                return JsonResponse(jsondata)

            # Updating weekly leave shared calendar employee.role == 'EMPLOYEE' and 
            if employee.role == 'EMPLOYEE' and (request.GET.get('q') == "next" or request.GET.get('q') == "prev"):
                jsondata = week_calendar(request.GET.get('q'), week)
                if jsondata['status'] == 'found':
                    return JsonResponse(jsondata)
                
            if employee.role == 'EMPLOYEE' and (id or leave_id):
                if id:
                    get_leave_info = LeaveManagement.objects.get(id=id)
                    return JsonResponse({
                        "status": "success",
                        "get_leave_info": {
                            "leave_id": get_leave_info.id,
                            "leave_reason": get_leave_info.leave_reason,
                            "leave_days": get_leave_info.leave_days,
                            "leave_start_date": get_leave_info.leave_start_date,
                            "leave_requested_for": get_leave_info.leave_requested_for,
                            "leave_type": get_leave_info.leave_type
                        }
                    })
                else:
                    LeaveManagement.objects.get(id=leave_id).delete()
                    return redirect('leave')

            if employee.role == 'EMPLOYEE':
                employee_paid_leave = LeaveManagement.objects.filter(Q(employee_id=employee) & ((Q(status="APPROVED") | Q(status="PENDING")) & Q(leave_type="PAID")))
                total_paid_leave = 0
                for leave in employee_paid_leave:
                    _leave_day = leave.leave_days*1 if leave.leave_requested_for == 'F' else leave.leave_days*0.5
                    print("Leave day : ", _leave_day)
                    total_paid_leave = total_paid_leave + _leave_day

                balance_paid_leave = 12 - total_paid_leave
                if balance_paid_leave < 0:
                    balance_paid_leave = 0
                form = LeaveManagementForm()
                all_leaves = get_all_leaves(employee) # LeaveManagement.objects.filter(employee_id = employee).order_by('-id')
                today = date.today()
                formatted_date = today.strftime('%Y-%m-%d')
                paginator = Paginator(all_leaves, 5)
                page_number = request.GET.get('page')
                try:
                    page = paginator.page(page_number)
                except PageNotAnInteger:
                    # If page_number is not an integer, show the first page
                    page = paginator.page(1)
                except EmptyPage:
                    # If page_number is out of range, show the last page
                    page = paginator.page(paginator.num_pages)

                context = {
                    'page': page,
                    "l_form":form,
                    "all_leave":all_leaves,
                    "emp":employee,
                    "date":formatted_date,
                    "bpl":int(balance_paid_leave) if ".0" in str(balance_paid_leave) else balance_paid_leave,
                    "next_date": current_week()['current_week_days'][-1].strftime("%b %d"),
                    "prev_date": current_week()['current_week_days'][0].strftime("%b %d"),
                    "emp_leave_list": week_calendar(),
                    "current_week_days": current_week()['current_week_days'],
                    "current_week_start": current_week()['current_week_start'].strftime('%Y-%m-%d'),
                }
                return render(request, 'hrm/emp_leave.html', context)
            
        except Exception as e:
            messages.add_message(request, messages.INFO, "Only employee is allowed."+str(e))
        return redirect('/')

    def post(self, request):
        if request.user.is_superuser:
            leave = LeaveManagement.objects.get(pk=int(request.POST.get('leave')))
            if request.POST.get('action') == "approve":
                can_approve_leave_request = leave_can_approve(leave)
                if can_approve_leave_request["status"] == True:
                    messages.add_message(request, messages.WARNING, f"Sorry leave request couldn't approve, {can_approve_leave_request['percentage']}% employee already on leave during selected period..")
                    return redirect("/leave/")
                else:
                    leave.approve_leave()
                    messages.add_message(request, messages.INFO, "Requested leave has been approved.")
                    return redirect("/leave/")
            elif request.POST.get('action') == "reject":
                leave.reject_leave()
                messages.add_message(request, messages.INFO, "Requested leave has been rejected.")
                return redirect("/leave/")
        form = LeaveManagementForm(request.POST, instance=None)
        emp  = EmployeeManager.objects.get(user=request.user)
        if form.is_valid() and emp.role == "EMPLOYEE":
            leave_reason = form.cleaned_data["leave_reason"]
            leave_requested_for = form.cleaned_data["leave_requested_for"]
            leave_type = form.cleaned_data["leave_type"]
            leave_days = form.cleaned_data["leave_days"]
            start_date = form.cleaned_data["leave_start_date"]
            leave_id = request.POST.get("leave_id")
            
            if leave_id:
                create_leave = leave_create(emp, leave_reason, int(leave_days), leave_requested_for, leave_type, start_date, leave_id)
            else:
                create_leave = leave_create(emp, leave_reason, int(leave_days), leave_requested_for, leave_type, start_date)
            if create_leave['status'] == True:
                messages.add_message(request, messages.SUCCESS, create_leave['message'])
                return redirect('./')
            else:
                messages.add_message(request, messages.WARNING, create_leave['error'])
                return redirect('./')
        else:
            error_list = " "
            for field, errors in form.errors.items():
                for error in errors:
                    error_list += error+' ,'
            error_list = error_list[:-1]
            messages.add_message(request, messages.WARNING, error_list)
        return redirect(request.path)

#this we use to get all employee
class EmployeesListAdmin(View):
    def get(self, request):
        emp_id = ""
        all_employee = Employee.objects.filter(role ="EMPLOYEE")
        not_employees = User.objects.filter(user_employee__isnull=True)
        desig_list = Designations.objects.all()
        depart_list = Departments.objects.all()

        if 'emp_edit_id' in request.session:
            emp_id = request.session.get('emp_edit_id')
            request.session.pop('emp_edit_id', None)
        return render(request, 'admin/employees.html', {"employee":all_employee, "users":not_employees, "designations": desig_list, "departments": depart_list, "emp_id": emp_id})

    def post(self, request):
        empuser = User.objects.get(id=request.POST['user'])
        form = AdminEmployeeProfileEditForm(request.POST)
        if form.is_valid():
            emp = Employee.objects.create(
                user = empuser,
                designation = form.cleaned_data['designation'],
                department = form.cleaned_data['department'],
                salary = form.cleaned_data['salary'],
                role = form.cleaned_data['role'],
            )
            emp.save()
            messages.add_message(request, messages.SUCCESS, "User's detail updated successfully.")
        else:
            error_list = " "
            for field, errors in form.errors.items():
                for error in errors:
                    error_list += error+' ,'
            error_list = error_list[:-1]
            messages.add_message(request, messages.WARNING, error_list)
        return redirect('./')

#this is for employee bank detail
class EmpBankDetail(View):
    def get(self, request, pk=None):
        if request.user.is_superuser:
            employee = Employee.objects.get(user = pk)
            bank_detail = EmployeeBankDetail.objects.filter(employee_bankdetail=employee).first()
            return render(request, 'admin/emp_bank.html', { 'bank_detail':bank_detail,'emp':employee})
        try:
            employee = Employee.objects.get(user = request.user )
            bank_detail = EmployeeBankDetail.objects.filter(employee_bankdetail=employee).first()
            return render(request, 'hrm/emp_bank.html',  { 'bank_detail':bank_detail, 'emp':employee})
        except Exception as e:
            messages.add_message(request, messages.INFO, "Only employee is allowed.")
        return redirect('/')

    def post(self, request, pk=None):
        if request.user.is_superuser:
            employee = Employee.objects.get(user = pk)
        else:
            employee = Employee.objects.get(user = request.user)
        form = EmployeeBankDetailsEditForm(request.POST, instance=None)
        if form.is_valid():
            form.save(employee)
            bank_detail = EmployeeBankDetail.objects.filter(employee_bankdetail=employee).first()
            messages.add_message(request, messages.SUCCESS, "Bank details updated successfully.")
        else:
            error_list = " "
            for field, errors in form.errors.items():
                for error in errors:
                    error_list += error+' ,'
            error_list = error_list[:-1]
            messages.add_message(request, messages.WARNING, error_list)
            if request.user.is_superuser:
                return redirect(f'./{pk}')
            else:
                return redirect('./')
        if request.user.is_superuser:
            return render(request, 'admin/emp_bank.html', { 'bank_detail':bank_detail,'emp':employee})
        return redirect('./')

class EmployeeProfileView(LoginRequiredMixin, View):
    def get(self, request, pk=None):
        if request.user.is_superuser:
            employee = Employee.objects.get(user = pk)
            manager = Employee.objects.filter(department=employee.department)
            desig_list = Designations.objects.all()
            depart_list = Departments.objects.all()
            return render(request, 'admin/employee-edit-profile.html', {'emp':employee, 'manager': manager, "designations": desig_list, "departments": depart_list})
        try:
            employee = Employee.objects.get(user = request.user )
            return render(request, 'hrm/employee-edit-profile.html', {'emp':employee})
        except Exception as e:
            messages.add_message(request, messages.INFO, "Only employee is allowed.")
        return redirect('/')

    def post(self, request, pk=None):
        if request.user.is_superuser:
            employee = Employee.objects.get(user = pk)
            form = AdminEmployeeProfileEditForm(request.POST, instance=None)
            if form.is_valid():
                manager = request.POST.get('manager')
                form.save(pk, manager)
                messages.add_message(request, messages.SUCCESS, "Profile updated successfully.")
            else:
                error_list = " "
                for field, errors in form.errors.items():
                    for error in errors:
                        error_list += error+' ,'
                error_list = error_list[:-1]
                messages.add_message(request, messages.WARNING, error_list)
            return redirect('employees', pk=pk)
        else:
            form = EmployeeProfileEditForm(request.POST, request.FILES, instance=None)
            employee = Employee.objects.get(user = request.user)
            if form.is_valid() and employee.role == "EMPLOYEE":
                form.save(request.user)
                messages.add_message(request, messages.SUCCESS, "Profile updated successfully.")
            else:
                error_list = " "
                for field, errors in form.errors.items():
                    for error in errors:
                        error_list += error+' ,'
                error_list = error_list[:-1]
                messages.add_message(request, messages.WARNING, error_list)
            return redirect('./')

#this is for admin and employee profile
class ProfileListView(LoginRequiredMixin, View):
    def post(self, request):
        if self.request.user.is_superuser == True:
            form = HolidayForm(request.POST)
            if form.is_valid():
                holiday_name = form.cleaned_data['holiday_name']
                holiday_date = form.cleaned_data['holiday_date']

                HolidayList.objects.create(
                    holiday_name = holiday_name,
                    holiday_date = holiday_date
                )
                messages.add_message(request, messages.SUCCESS, "Holiday created successfully.")
            else:
                error_list = " "
                for field, errors in form.errors.items():
                    for error in errors:
                        error_list += error+' ,'
                error_list = error_list[:-1]
                messages.add_message(request, messages.WARNING, error_list)
            return redirect('./')

        else:
            form = LeaveManagementForm(request.POST)
            if form.is_valid() and Employee.objects.get(user=request.user).role == 'EMPLOYEE':
                employee = Employee.objects.get(user=request.user)
                leave_reason = form.cleaned_data.get('leave_reason')
                leave_days = form.cleaned_data.get('leave_days')
                start_date = form.cleaned_data.get('leave_start_date')
                leave_type = form.cleaned_data.get('leave_type')

                LeaveManagement.objects.create(
                    employee_id = employee,
                    leave_reason = leave_reason,
                    leave_days = leave_days,
                    leave_start_date = start_date,
                    leave_type = leave_type,
                    status = "PENDING"
                )
                messages.add_message(request, messages.SUCCESS, "Leave created successfully.")
            else:
                error_list = " "
                for field, errors in form.errors.items():
                    for error in errors:
                        error_list += error+' ,'
                error_list = error_list[:-1]
                messages.add_message(request, messages.WARNING, error_list)
            return redirect("./")

    def get(self, request):
        holiday = HolidayList.objects.all()
        if self.request.user.is_superuser == True:
            return render(request, 'admin/admin_base.html',  {"holidaylist":holiday})
        else:
            try:
                employee = Employee.objects.get(user=request.user)
                return render(request, 'hrm/profile.html',  { "holidaylist":holiday, "emp":employee})
            except Employee.DoesNotExist:
                employee = None
                return render(request, 'hrm/profile.html',  { "holidaylist":holiday})


# for manage employee and admin payroll
class PayRollView(LoginRequiredMixin, View):
    global PRE_MONTH, TOTAL_DAYS, DATE_OBJECT, SALARY_MONTH, MONTH_LIST
    #-----------here we are calculating all months detail------------------------------
    today = datetime.now().date()
    month, year = (today.month-1, today.year) if today.month != 1 else (12, today.year-1)
    PRE_MONTH = today.replace(day=1, month=month, year=year)
    TOTAL_DAYS = calendar.monthrange(PRE_MONTH.year, PRE_MONTH.month)[1]
    DATE_OBJECT = datetime.strptime(PRE_MONTH.strftime('%m-%Y'), '%m-%Y')
    SALARY_MONTH = DATE_OBJECT.strftime("%B %Y").upper()
    MONTH_LIST = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    def get(self, request, month=None, year=None):
        if self.request.user.is_superuser == True:
            _today  = date.today()
            if not month: month = _today.month
            if not year: year = _today.year
            payslip = PaySlip.objects.filter(
                dispatch_date__month=1 if month == 12 else month+1,
                dispatch_date__year=year+1 if month == 12 else year,
                ).select_related('employee_payslip')
            _today = _today.replace(month=month, year=year, day=1)

            current_year = _today.year
            all_years = sorted([current_year - i for i in range(1, 2)] + [current_year + i for i in range(0, 7)])
            if request.GET.get('employee_id'):
                payslip = PaySlip.objects.filter(
                employee_payslip = request.GET.get('employee_id'),
                dispatch_date__month=1 if month == 12 else month+1,
                dispatch_date__year=year+1 if month == 12 else year
                ).select_related('employee_payslip').first()
                jsondata = {
                    'payslip':payslip.path if payslip else "Not found",
                    'month_list':MONTH_LIST,
                }
                return JsonResponse(jsondata)

            context = {
                'salary_month_name':_today,
                'effectiveworks': Date(_today).total_days(),
                'total_leave_days':0,
                'payslips':payslip,
                'dispatched_payslip': False if payslip.filter(dispatched_payslip=False) else True,
                'admin_confirmation':False if payslip.filter(admin_confirmation=False) else True,
                'month_list':MONTH_LIST,
                'total_employees':
                 Employee.objects.count(),
                'employees': Employee.objects.filter(role="EMPLOYEE"),
                'months':months(),
                'cur': date.today(),
                'curr_year':date.today().year,
                'year': all_years,
                'earning': payslip.aggregate(earning=Sum('earning')),
                 }
            return render(request, 'admin/payroll_expense.html', context)
        else:
            _today  = date.today()
            if not month: month = _today.month
            if not year: year = _today.year
            try:
                employee = Employee.objects.get(user = request.user )
                payslip = PaySlip.objects.filter(employee_payslip = employee,
                                    dispatch_date__month=1 if month == 12 else month+1,
                                    dispatch_date__year=year+1 if month == 12 else year,
                                    admin_confirmation=True
                                    ).select_related('employee_payslip').first()
                if not payslip and request.GET.get('q') != "ajax":
                    get_payslip = PaySlip.objects.filter(employee_payslip = employee, admin_confirmation=True).select_related('employee_payslip')
                    if get_payslip:
                        payslip = get_payslip.last()

                year = [_today.year-1,_today.year,_today.year+1]
                data = {'emp':employee,
                        'payslip':payslip if payslip else "Not found",
                        'month': payslip.dispatch_date.month-1 if payslip else 0,
                        'curr_year':date.today().year,
                        'year':year,
                        'salary_month_name':_today,
                        'month_list':MONTH_LIST,
                        }
                if request.GET.get('q') == "ajax":
                    jsondata = {
                        'payslip':payslip.path if payslip else "Not found",
                        'month_list':MONTH_LIST,
                    }
                    return JsonResponse(jsondata)
                return render(request, 'hrm/emp_payroll.html', data)
            except Employee.DoesNotExist:
                employee = None
                holiday = HolidayList.objects.all()
                messages.add_message(request, messages.INFO, "Only employee is allowed.")
                return render(request, 'hrm/profile.html',  { "holidaylist":holiday})


    def post(self, request):
        request.GET.get('q') == "ajax"
        if self.request.user.is_superuser == True:
            selected_employee = request.POST.get("selected_employee")
            if selected_employee != "ALL":
                gererate_payslip = InitializePayslip.pay_slip_initialize(selected_employee)
            else:
                gererate_payslip = InitializePayslip.pay_slip_initialize()
            if gererate_payslip['status']==True:
                messages.add_message(request, messages.SUCCESS, "Salary Slip is generated.")
                return redirect("/payroll_expenses/")
            else:
                messages.add_message(request, messages.WARNING, gererate_payslip['Error'])
                return redirect("/payroll_expenses/")
        else:
            return HttpResponse("Only admin can Access..")

class ProceedToGeneratePayslip(LoginRequiredMixin, View):
    def get(self, request):
        if self.request.user.is_superuser == True:
            payslips = PaySlip.objects.filter(dispatch_date__month=date.today().month, admin_confirmation=False).select_related('employee_payslip')
            for payslip in payslips:
                employee = Employee.objects.get(user=payslip.employee_payslip.user)
                #--------------------find each employee bank detail---------------------------
                emp_bankdetail = EmployeeBankDetail.objects.get(employee_bankdetail=employee)
                base_data ={
                    'total_earn': payslip.earning,
                    'effectiveworks': payslip.effective_work_days,
                    'losspayday': fix_to_two_digit(payslip.loss_pay_days),
                    'totalpaydays': fix_to_two_digit(payslip.total_pay_days),
                    'leave_deduction': (payslip.salary+payslip.addition_amount)-(payslip.earning+payslip.deduction_amount),
                    'additional_title': payslip.addition_title,
                    'additional_amount': payslip.addition_amount,
                    'deduction_title': payslip.deduction_title,
                    'deduction_amount': payslip.deduction_amount,
                    'earning_in_words': numtowords(payslip.earning),
                    'salary_month_name': payslip.salary_month_name,
                    'employee_joining_date':employee.user.date_joined.date(),
                    'filepath':payslip.path,
                }
                extra_line = False
                if int(base_data["additional_amount"]) != 0 or int(base_data["deduction_amount"]) != 0:
                    extra_line = True
                #----generate pdf only if old pdf not register for old month-------------
                context = {'employee':employee, 'base_data':base_data, 'bank_detail':emp_bankdetail, 'extra_line': extra_line}
                if os.path.exists(base_data['filepath']):
                    os.remove(base_data['filepath'])
                generate_pdf(context, send_email=True)
            payslips.update(admin_confirmation=True)
            messages.add_message(request, messages.SUCCESS, "Salary have sent to Employee.")
            return redirect("/payroll_expenses/")
        else:
            return HttpResponse("Only admin can Access..")

class StopPayslip(LoginRequiredMixin, View):
    def get(self, request):
        if self.request.user.is_superuser == True:
            PaySlip.objects.filter(dispatch_date__month=date.today().month, admin_confirmation=False).delete()
            messages.add_message(request, messages.SUCCESS, "Salary Slip Deleted.")
            return redirect("/payroll_expenses/")
        else:
            return HttpResponse("Only admin can Access..")

class SendPayslip(LoginRequiredMixin, View):
    def get(self, request):
        if self.request.user.is_superuser == True:
            all_employee = Employee.objects.filter(role="EMPLOYEE").select_related('user')
            #---check pdf is generated or not---------------
            payslip_exist = PaySlip.objects.filter(dispatch_date__month=date.today().month, admin_confirmation=True, dispatched_payslip=False)
            month = (datetime.now() - timedelta(days=5)).strftime('%B')
            if payslip_exist:
                for employee in all_employee:
                    payslip = PaySlip.objects.get(employee_payslip=employee, dispatch_date__month=date.today().month)
                    filename = payslip.payslip_name
                    #--- Define Filepath where PDF Save -----------------------------------
                    filedir = 'media/pdf_file/'
                    filepath = os.path.join(filedir,filename)
                    emailTo = [employee.user.email]
                    Mailer(
                        subject=f"{'Your Payslip for month '}{month}",
                        message="Here is your payslip",
                        email_to = emailTo
                    ).send(filepath)
                    payslip.dispatched_payslip = True
                    payslip.dispatch_date = date.today()
                    payslip.save()
                messages.add_message(request, messages.SUCCESS, "Payslip has been sent to Employee.")
                return redirect("/payroll_expenses/")
            else:
                messages.add_message(request, messages.WARNING, "Either Payslip not generated or admin not confirm the payslip.")
                return redirect("/payroll_expenses/")
        else:
            return HttpResponse("Only admin can Access..")


class InitializePayslip(View):
    def pay_slip_initialize(user=None):
        if user:
            all_employee = Employee.objects.filter(user__username=user).select_related('user')
        else:
            all_employee = Employee.objects.filter(role="EMPLOYEE").select_related('user')
        ok_flag = True
        payslip_flag = False
        if all_employee:
            for employee in all_employee:
                if not (employee.name and employee.department and employee.designation and employee.salary and EmployeeBankDetail.objects.filter(employee_bankdetail=employee).exists()):
                    ok_flag = False
                    break
            if ok_flag == True:
                for employee in all_employee:
                    employee_leaves = leave_calculate(employee, TOTAL_DAYS, PRE_MONTH.month)
                    employee_total_earning = int(employee_leaves["days_payable"]*(employee.salary/TOTAL_DAYS))
                    earning_in_words = numtowords(employee_total_earning)

                #----creating unique pdf name---------------------------
                    do = DATE_OBJECT.strftime("%B%Y").upper()
                    pdf_name=f"{do}{employee.user.username}.pdf"

                #--- Define Filepath where PDF Save -----------------------------------
                    filedir = 'media/pdf_file/'
                    filepath = os.path.join(filedir,pdf_name)
                    
                #---this is base_data that will be change by month----------------------
                    base_data ={'total_earn': employee_total_earning,
                                'effectiveworks': TOTAL_DAYS,
                                'losspayday': employee_leaves["total_leave_days"],
                                'totalpaydays': employee_leaves["days_payable"],
                                'earning_in_words': earning_in_words,
                                'salary_month_name': SALARY_MONTH,
                                'employee_joining_date': employee.user.date_joined.date(),
                                'filepath': filepath,
                                }
                #---check pdf is generated or not---------------
                    oldpayslip = PaySlip.objects.filter(employee_payslip = employee, payslip_name = pdf_name)
                #---create new payslip object-------------------
                    if not oldpayslip:
                        create_payslip = PaySlip.objects.create(
                            employee_payslip = employee,
                            path = filepath,
                            dispatch_date = date.today(),
                            leave_taken = employee_leaves["total_leave_days"],
                            full_day = employee_leaves["full_day"],
                            half_day = employee_leaves["half_day"],
                            salary = employee.salary,
                            payslip_name = pdf_name,
                            earning = base_data['total_earn'],
                            effective_work_days = base_data['effectiveworks'],
                            loss_pay_days = base_data['losspayday'],
                            total_pay_days = base_data['totalpaydays'],
                            salary_month_name = base_data['salary_month_name']
                            )
                        create_payslip.save()
                        payslip_flag = True
                    else:
                        if user:
                            return {"status": False, "Error": f"Salary slip already requested for {employee.name}."}
                        else:
                            continue
                if payslip_flag:
                    return {"status": True}
                else:
                    return {"status": False, "Error": "Salary slip already requested for all employee."}
            else:
                return {"status": False, "Error": f"Either employee name, department, designation, salary and Bank Details or anyone of these is missing for user, {employee.user}. Please provide it first."}
        else:
            return {"status": False, "Error": "No Employee"}

#---------- Here allows to update payroll details --------------------------- 
class PayRollUpdate(LoginRequiredMixin, View):
    def get(self, request, id=None):
        if self.request.user.is_superuser:
            if request.GET.get("payroll_id"):
                payslip = PaySlip.objects.select_related('employee_payslip').get(id=request.GET.get("payroll_id"))
            else:
                payslip = PaySlip.objects.select_related('employee_payslip').get(id=id)
            jsondata = {
                'employee': payslip.employee_payslip.name,
                'department': payslip.employee_payslip.department,
                'full_day': payslip.full_day,
                'half_day': payslip.half_day,
                'deduction': payslip.deduction,
                'salary': payslip.salary,
                'earning': payslip.earning,
                'effective_work_days': payslip.effective_work_days,
                'loss_pay_days': payslip.loss_pay_days,
                'total_pay_days': payslip.total_pay_days,
                'leave_taken': payslip.leave_taken,
                'addition_title': payslip.addition_title,
                'addition_amount': payslip.addition_amount,
                'deduction_title': payslip.deduction_title,
                'deduction_amount': payslip.deduction_amount,
            }
            return JsonResponse(jsondata)
        
    def post(self, request):
        if self.request.user.is_superuser:
            payroll_id = request.POST.get("payroll_id")
            employee_name = request.POST.get("emp_name")
            department = request.POST.get("department")
            full_day = int(request.POST.get("full_day"))
            half_day = int(request.POST.get("half_day"))
            addition_title = request.POST.get("addition_title")
            addition_amount = int(request.POST.get("addition_amount"))
            deduction_title = request.POST.get("deduction_title")
            deduction_amount = int(request.POST.get("deduction_amount"))
            salary = int(request.POST.get("salary"))
            earning = salary - (((full_day*1) + (half_day*0.5)) * (salary / TOTAL_DAYS)) + addition_amount - deduction_amount
            effective_work_days = request.POST.get("effective_work_days")
            loss_pay_days = request.POST.get("loss_pay_days")
            total_pay_days = request.POST.get("total_pay_days")

            if addition_title == None or addition_title.strip() == "" and addition_amount != 0:
                messages.add_message(request, messages.WARNING, "Please define additional title and additional amount both.")
                return redirect('payroll_expense')
            if deduction_title == None or deduction_title.strip() == "" and deduction_amount != 0:
                messages.add_message(request, messages.WARNING, "Please define deduction title and deduction amount both.")
                return redirect('payroll_expense')

            payroll = PaySlip.objects.get(id=payroll_id)
            if payroll.employee_payslip.name == employee_name and payroll.employee_payslip.department == department:
                emp  = EmployeeManager.objects.get(user__username=payroll.employee_payslip.user)
                leave_reason = request.POST.get("leave_reason")
                leave_type = request.POST.get("leave_type")
                leave_requested_for = request.POST.get("leave_requested_for")
                leave_days = request.POST.get("leave_days")
                start_date = request.POST.get("leave_start_date")
                
                payroll.full_day = full_day
                payroll.half_day = half_day
                payroll.earning = earning
                payroll.effective_work_days = effective_work_days
                payroll.loss_pay_days = loss_pay_days
                payroll.total_pay_days = total_pay_days
                payroll.addition_title = addition_title
                payroll.addition_amount = addition_amount
                payroll.deduction_title = deduction_title
                payroll.deduction_amount = deduction_amount
                payroll.dispatched_payslip = False
                payroll.admin_confirmation = False
                
                if leave_reason != "" and leave_days != "" and start_date != "":
                    start_date = datetime.strptime(request.POST.get("leave_start_date"), '%Y-%m-%d').date()
                    create_leave = leave_create(emp, leave_reason, int(leave_days), leave_requested_for, leave_type, start_date)
                    if create_leave['status'] == True:
                        payroll.save()
                        messages.add_message(request, messages.SUCCESS, "Leave and Payroll has been updated.")
                        return redirect('payroll_expense')
                    else:
                        messages.add_message(request, messages.WARNING, create_leave['error'])
                        return redirect('payroll_expense')
                else:
                    messages.add_message(request, messages.SUCCESS, "Payroll has been updated.")
                    payroll.save()
            return redirect('payroll_expense')
        return HttpResponse("Only admin can Access..")


class EmployeeProfileAdmin(View):
    def get(self, request, pk=None):
        if self.request.user.is_superuser==True:
            emps = Employee.objects.exclude(role='ADMIN')
            year = datetime.now().year
            emp = Employee.objects.select_related('user').get(id = pk)
            reporting = Employee.objects.filter(department=emp.department)
            date_joined = emp.user.date_joined
            joining_date = date_joined.date().strftime("%d-%m-%Y")
            context = {
                'emp':emp,
                'emps':emps,
                'joining_date':joining_date,
                'reporting':reporting,
            }
            return render(request, 'admin/employee-about.html', context)
        else:
            context = {
                'msg':"Only Admin Access."
            }
            return context

class AdminEmpPayroll(View):
    def get(self, request,  month=None, year=None, pk=None):
        if self.request.user.is_superuser==True:
            _today  = date.today()
            if not month: month = _today.month
            if not year: year = _today.year
            employee = Employee.objects.get(user = pk )
            payslip = PaySlip.objects.filter(employee_payslip = employee,
                                dispatch_date__month=1 if month == 12 else month+1,
                                dispatch_date__year=year+1 if month == 12 else year
                                ).first()

            if not payslip and request.GET.get('q') != "ajax":
                get_payslip = PaySlip.objects.filter(employee_payslip = employee)
                if get_payslip:
                    payslip = get_payslip.last()

            year = [_today.year-1,_today.year,_today.year+1]
            month_list = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
            data = {'emp':employee,
                    'payslip':payslip if payslip else "Not found",
                    'curr_year':_today.year,
                    'month': payslip.dispatch_date.month-1 if payslip else 0,
                    'year':year,
                    'month_list': month_list,
                    }
            if request.GET.get('q') == "ajax":
                jsondata = {
                    'payslip':payslip.path if payslip else "Not found",
                }
                return JsonResponse(jsondata)
            return render(request, 'admin/emp_payroll.html', data)

class HolidayView(View):
    def post(self, request):
        form = HolidayForm(request.POST)
        if form.is_valid():
            holiday, created = HolidayList.objects.get_or_create(
                id = request.POST.get('holiday_id'),
                defaults={
                    "holiday_name": form.cleaned_data['holiday_name'],
                    "holiday_date": form.cleaned_data['holiday_date']
                }
            )
            if not created:
                holiday.holiday_date = form.cleaned_data['holiday_date']
                holiday.holiday_name = form.cleaned_data['holiday_name']
                holiday.save()
            messages.add_message(request, messages.SUCCESS, "Holiday created successfully.")
        else:
            error_list = " "
            for field, errors in form.errors.items():
                for error in errors:
                    error_list += error+' ,'
            error_list = error_list[:-1]
            messages.add_message(request, messages.WARNING, error_list)
        return redirect(reverse("profile"))
    
    def get(self, request, pk=None):
        if pk == None:
            id = request.GET.get('id')
            print("Holiday id: ", id)
            holiday = HolidayList.objects.get(id=id)
            holiday_dict = {
                "holiday_id": holiday.id,
                "holiday_name": holiday.holiday_name,
                "holiday_date": holiday.holiday_date
            }
            return JsonResponse({"status": "success", "holiday": holiday_dict})
        else:
            HolidayList.objects.get(id=pk).delete()
            return redirect(reverse("profile"))

class EmployeeAboutView(View):
    def get(self, request, pk=None):
        if self.request.user.is_superuser==True:
            employee = Employee.objects.get(user = pk )
            return render(request, 'admin/employee-about.html',  { "emp":employee})
        else:
            employee = Employee.objects.get(user = request.user )
            return render(request, 'hrm/employee-about.html',  { "emp":employee})
        

class AddDesignation(LoginRequiredMixin, View):
    def get(self, request):
        if self.request.user.is_superuser:
            designation = self.request.GET.get('designation')

            check_desig_availability = Designations.objects.filter(name=designation).exists()

            if check_desig_availability:
                jsondata = {
                    "status": "failed",
                    "error": "Designation already exist.",
                }
                return JsonResponse(jsondata)
            else:
                Designations(name=designation).save()
                jsondata = {
                    "status": "success",
                    "designation": designation,
                }
                return JsonResponse(jsondata)
            

class EditDesignation(LoginRequiredMixin, View):
    def get(self, request):
        if self.request.user.is_superuser:
            designation = self.request.GET.get('designation')
            currentDesig = self.request.GET.get('currentDesig')

            get_desig = Designations.objects.get(name=currentDesig)
            get_desig.name = designation
            get_desig.save()

            jsondata = {
                "status": "success",
                "designation": designation,
            }
            return JsonResponse(jsondata)
        

class AddDepartment(LoginRequiredMixin, View):
    def get(self, request):
        if self.request.user.is_superuser:
            department = self.request.GET.get('department')

            check_depart_availability = Departments.objects.filter(name=department).exists()

            if check_depart_availability:
                jsondata = {
                    "status": "failed",
                    "error": "Department already exist.",
                }
                return JsonResponse(jsondata)
            else:
                Departments(name=department).save()
                jsondata = {
                    "status": "success",
                    "department": department,
                }
                return JsonResponse(jsondata)
            

class EditDepartment(LoginRequiredMixin, View):
    def get(self, request):
        if self.request.user.is_superuser:
            department = self.request.GET.get('department')
            currentDepart = self.request.GET.get('currentDepart')

            get_depart = Departments.objects.get(name=currentDepart)
            get_depart.name = department
            get_depart.save()

            jsondata = {
                "status": "success",
                "department": department,
            }
            return JsonResponse(jsondata)
        

class UserInfo(LoginRequiredMixin, View):
    def get(self, request):
        if self.request.user.is_superuser:
            userid = self.request.GET.get('userid')
            user_info = User.objects.get(id=userid)


            jsondata = {
                "status": "success",
                "username": user_info.username,
                "email": user_info.email,
                "user_id": user_info.pk,
            }
            return JsonResponse(jsondata)


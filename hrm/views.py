import datetime
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
from hrm.models import HolidayList, Employee, EmployeeManager, EmployeeBankDetail, PaySlip, LeaveManagement
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth import authenticate
from core.utils.dates import Date, months
from datetime import date, datetime
from core.utils.payslip_pdf import generate_pdf
from core.utils.numtoword import numtowords
from core.utils.week import current_week, next_week, pre_week
import calendar
from django.contrib import messages
from django.db.models import Sum
from django.db.models import Q
from .forms import LeaveManagementForm, UserRegisterForm, EmployeeProfileEditForm, AdminEmployeeProfileEditForm, EmployeeBankDetailsEditForm, EmailForm ,SignUpForm, HolidayForm
from django.views.generic import CreateView

class login_user(View):
    template_name = 'hrm/login.html'
    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        # if request.method == 'POST': #if someone fills out form , Post it
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:# if user exist
            login(request, user)
            # messages.add_message(request, messages.INFO, "YOU ARE NOW LOGIN")
            return redirect('/') #re routes to login page upon unsucessful login
        else:
            messages.add_message(request, messages.INFO, "Please enter correct credentials.")
            return render(request, 'hrm/login.html', {})

class LogoutView(View):
    def get(self, request):
        logout(request)
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
                for error in errors:
                    error_list += error+' ,'
            error_list = error_list[:-1]
            messages.add_message(request, messages.WARNING, error_list)
            return render(request, 'hrm/registration.html')


from django.shortcuts import get_object_or_404
from hrm.choice import USER_ROLE
# this is for leave management
class LeaveRequestView(View):
    def get(self, request, days=None, start=None, week=None, pk=None):
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
                return render(request, 'admin/emp_leave.html',  {"page":page, "all_leave":all_leaves, "emp":employee})
            pending_leaves = LeaveManagement.objects.filter(status = "PENDING")
            return render(request, 'admin/leave.html', {"leaves":pending_leaves})
        try:
            employee = request.user.user_employee

            # Fetching out teammates already on leave during selected period of time.
            if employee.role == 'EMPLOYEE' and request.GET.get('q') == "ajax":
                days_in_leave = Date(datetime.strptime(start, '%Y-%m-%d').date()).get_next_working_days(days)
                emply_list = []
                all_emplys = Employee.objects.filter(department=employee.department, role="EMPLOYEE")
                for x in all_emplys:
                    emplys = LeaveManagement.objects.filter(employee_id=x,status="APPROVED")
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

            # Updating weekly leave shared calendar
            if employee.role == 'EMPLOYEE' and (request.GET.get('q') == "next" or request.GET.get('q') == "prev"):
                current_week_start = datetime.strptime(week, '%Y-%m-%d').date()
                if request.GET.get('q') == "prev":
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
                jsondata = {
                    'status': 'found',
                    "emp_leave_list": emp_leave_list,
                    "current_week_days": cu_week_days,
                    "current_week_start": current_week_start,
                    "next_date": current_week_days[-1].strftime("%b %d"),
                    "prev_date": current_week_days[0].strftime("%b %d"),
                }
                return JsonResponse(jsondata)

            if employee.role == 'EMPLOYEE':
                employee_paid_leave = LeaveManagement.objects.filter(Q(employee_id=employee) & (Q(status="APPROVED") | Q(status="PENDING") & Q(leave_type="PAID")))
                total_paid_leave = 0
                for leave in employee_paid_leave:
                    total_paid_leave = total_paid_leave+leave.leave_days

                bpl = 12 - total_paid_leave

                form = LeaveManagementForm()
                all_leaves = LeaveManagement.objects.filter(employee_id = employee).order_by('-id')
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

                # Creating weekly leave shared calendar
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

                context = {
                    'page': page,
                    "l_form":form,
                    "all_leave":all_leaves,
                    "emp":employee,
                    "date":formatted_date,
                    "bpl":bpl,
                    "next_date": current_week()['current_week_days'][-1].strftime("%b %d"),
                    "prev_date": current_week()['current_week_days'][0].strftime("%b %d"),
                    "emp_leave_list": emp_leave_list,
                    "current_week_days": current_week()['current_week_days'],
                    "current_week_start": current_week()['current_week_start'].strftime('%Y-%m-%d'),
                }
                return render(request, 'hrm/emp_leave.html', context)
        except Exception as e:
            messages.add_message(request, messages.INFO, "Only employee is allowed.")
        return redirect('/')

    def post(self, request):
        if request.user.is_superuser:
            leave = LeaveManagement.objects.get(pk=int(request.POST.get('leave')))
            if request.POST.get('action') == "approve":
                leave.approve_leave()
                messages.add_message(request, messages.INFO, "Requested leave has been approved.")
            elif request.POST.get('action') == "reject":
                leave.reject_leave()
                messages.add_message(request, messages.INFO, "Requested leave has been rejected.")
            return redirect("/leave/")

        form = LeaveManagementForm(request.POST, instance=None)
        emp  = EmployeeManager.objects.get(user=request.user)
        if form.is_valid() and emp.role == "EMPLOYEE":
            leave_reason = form.cleaned_data["leave_reason"]
            leave_type = form.cleaned_data["leave_type"]
            leave_requested_for = form.cleaned_data["leave_requested_for"]
            leave_days = form.cleaned_data["leave_days"]
            start_date = form.cleaned_data["leave_start_date"]
            _date = Date(start_date)
            requested_leave_days = _date.get_next_working_days(leave_days)

            oldleave = LeaveManagement.objects.filter(employee_id=emp, leave_start_date__month__range=[(start_date.month-1),(start_date.month+1)]).exclude(status="REJECTED")
            for x in oldleave:
                days_in_leave = Date(x.leave_start_date).get_next_working_days(x.leave_days)
                for y in requested_leave_days:
                    if y in days_in_leave:
                        messages.add_message(request, messages.WARNING, f"Leave for '{y}', is already requested.")
                        return redirect('/leave/')
                    else:
                        continue

            if  leave_type == "PAID" or emp.get_all() >= int(request.POST.get("leave_days")) :
                if requested_leave_days[-1].month > 6:
                    employee_paid_leave = LeaveManagement.objects.filter(Q(employee_id=emp) & (Q(status="APPROVED") | Q(status="PENDING") & Q(leave_type="PAID")))
                    leave_can_take = 12
                else:
                    employee_paid_leave = LeaveManagement.objects.filter(Q(employee_id=emp) & (Q(status="APPROVED") | Q(status="PENDING") & Q(leave_type="PAID")) & Q(leave_start_date__month__range=[1,6]))
                    leave_can_take = 6
                requested_paid_leave = int(leave_days)
                total_paid_leave = 0
                for leave in employee_paid_leave:
                    total_paid_leave = total_paid_leave+leave.leave_days

                if leave_can_take >= total_paid_leave + requested_paid_leave:
                    LeaveManagement.objects.create(
                    employee_id = emp,
                    leave_reason = leave_reason,
                    leave_days = leave_days,
                    leave_start_date = start_date,
                    leave_type = leave_type,
                    leave_requested_for = leave_requested_for,
                    status = "PENDING"
                    )
                    messages.add_message(request, messages.SUCCESS, f"Leave has been submitted. You have {leave_can_take -(total_paid_leave+requested_paid_leave)} paid leaves left.")
                    return redirect('/leave/')
                else:
                    messages.add_message(request, messages.WARNING, "Sorry, You can only take 6 Paid leave during 'January to June' and 6 Paid leave during 'July to December'.")
                    return redirect(request.path)
            else:
                LeaveManagement.objects.create(
                    employee_id = emp,
                    leave_reason = leave_reason,
                    leave_days = leave_days,
                    leave_start_date = start_date,
                    leave_type = leave_type,
                    leave_requested_for = leave_requested_for,
                    status = "PENDING"
                )
                messages.add_message(request, messages.SUCCESS, "Leave has been submitted.")
                return redirect("./")
        else:
            error_list = " "
            for field, errors in form.errors.items():
                for error in errors:
                    error_list += error+' ,'
            error_list = error_list[:-1]
            print(error_list)
            messages.add_message(request, messages.WARNING, error_list)
        return redirect(request.path)

#this we use to get all employee
class EmployeesListAdmin(View):
    def get(self, request):
        all_employee = Employee.objects.filter(role ="EMPLOYEE")
        not_employees = User.objects.filter(user_employee__isnull=True)
        return render(request, 'admin/employees.html', {"employee":all_employee, "users":not_employees})

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
            form = EmployeeBankDetailsEditForm(request.POST, instance=None)
            if form.is_valid():
                bank_name = form.cleaned_data['bank_name']
                branch = form.cleaned_data['branch']
                bank_account_no = form.cleaned_data['bank_account_no']
                account_holder_name = form.cleaned_data['account_holder_name']
                ifsc_code = form.cleaned_data['ifsc_code']
                pan_no = form.cleaned_data['pan_no']

                bank_detail, created = EmployeeBankDetail.objects.get_or_create(
                employee_bankdetail = employee,
                defaults={
                    'bank_name': bank_name,
                    'branch': branch,
                    'bank_account_no': bank_account_no,
                    'account_holder_name': account_holder_name,
                    'ifsc_code': ifsc_code,
                    'pan_no': pan_no,
                    }
                )
                if not created:
                    bank_detail.bank_name = bank_name
                    bank_detail.branch = branch
                    bank_detail.bank_account_no = bank_account_no
                    bank_detail.account_holder_name = account_holder_name
                    bank_detail.ifsc_code = ifsc_code
                    bank_detail.pan_no = pan_no
                    bank_detail.save()
                bank_detail = EmployeeBankDetail.objects.filter(employee_bankdetail=employee).first()
                messages.add_message(request, messages.SUCCESS, "Bank details updated successfully.")
            else:
                error_list = " "
                for field, errors in form.errors.items():
                    for error in errors:
                        error_list += error+' ,'
                error_list = error_list[:-1]
                messages.add_message(request, messages.WARNING, error_list)
                return redirect(f'./{pk}')
            return render(request, 'admin/emp_bank.html', { 'bank_detail':bank_detail,'emp':employee})

        else:
            employee = Employee.objects.get(user = request.user)
            form = EmployeeBankDetailsEditForm(request.POST, instance=None)
            if form.is_valid():
                bank_name = form.cleaned_data['bank_name']
                branch = form.cleaned_data['branch']
                bank_account_no = form.cleaned_data['bank_account_no']
                account_holder_name = form.cleaned_data['account_holder_name']
                ifsc_code = form.cleaned_data['ifsc_code']
                pan_no = form.cleaned_data['pan_no']

                bank_detail, created = EmployeeBankDetail.objects.get_or_create(
                employee_bankdetail = employee,
                defaults={
                    'bank_name': bank_name,
                    'branch': branch,
                    'bank_account_no': bank_account_no,
                    'account_holder_name': account_holder_name,
                    'ifsc_code': ifsc_code,
                    'pan_no': pan_no,
                    }
                )
                if not created:
                    bank_detail.bank_name = bank_name
                    bank_detail.branch = branch
                    bank_detail.bank_account_no = bank_account_no
                    bank_detail.account_holder_name = account_holder_name
                    bank_detail.ifsc_code = ifsc_code
                    bank_detail.pan_no = pan_no
                    bank_detail.save()
                messages.add_message(request, messages.SUCCESS, "Bank details updated successfully.")
            else:
                error_list = " "
                for field, errors in form.errors.items():
                    for error in errors:
                        error_list += error+' ,'
                error_list = error_list[:-1]
                messages.add_message(request, messages.WARNING, error_list)
            return redirect('./')

class EmployeeProfileView(LoginRequiredMixin, View):
    def get(self, request, pk=None):
        if request.user.is_superuser:
            employee = Employee.objects.get(user = pk)
            return render(request, 'admin/employee-edit-profile.html', {'emp':employee})
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
                designation = form.cleaned_data['designation']
                role = form.cleaned_data['role']
                department = form.cleaned_data['department']
                salary = form.cleaned_data['salary']
                emp_detail, created = Employee.objects.get_or_create(
                user = pk,
                defaults={
                    'designation': designation,
                    'role': role,
                    'department': department,
                    'salary': salary,
                    }
                )
                if not created:
                    emp_detail.designation = designation
                    emp_detail.role = role
                    emp_detail.department = department
                    emp_detail.salary = salary
                    emp_detail.save()
                employee = Employee.objects.get(user = pk)
                messages.add_message(request, messages.SUCCESS, "Profile updated successfully.")
            else:
                error_list = " "
                for field, errors in form.errors.items():
                    for error in errors:
                        error_list += error+' ,'
                error_list = error_list[:-1]
                print(error_list)
                messages.add_message(request, messages.WARNING, error_list)
            return render(request, 'admin/employee-edit-profile.html', {'emp':employee})
        else:
            form = EmployeeProfileEditForm(request.POST, request.FILES, instance=None)
            employee = Employee.objects.get(user = request.user)
            if form.is_valid() and employee.role == "EMPLOYEE":
                name = form.cleaned_data['name']
                profile_image = form.cleaned_data['profile_image']
                gender = form.cleaned_data['genderselect']
                dob = form.cleaned_data['dob']
                mobile = form.cleaned_data['mobile']
                address = form.cleaned_data['address']
                pincode = form.cleaned_data['pincode']
                city = form.cleaned_data['city']
                state = form.cleaned_data['state']
                emp_detail, created = Employee.objects.get_or_create(
                user = request.user,
                defaults={
                    'name': name,
                    'profile_image': profile_image,
                    'gender': gender,
                    'dob': dob,
                    'mobile': mobile,
                    'address': address,
                    'pincode': pincode,
                    'city': city,
                    'state': state,
                    }
                )
                if not created:
                    emp_detail.name = name
                    emp_detail.profile_image = profile_image
                    emp_detail.gender = gender
                    emp_detail.dob = dob
                    emp_detail.mobile = mobile
                    emp_detail.address = address
                    emp_detail.pincode = pincode
                    emp_detail.city = city
                    emp_detail.state = state
                    emp_detail.save()
                messages.add_message(request, messages.SUCCESS, "Profile updated successfully.")
            else:
                error_list = " "
                for field, errors in form.errors.items():
                    for error in errors:
                        error_list += error+' ,'
                error_list = error_list[:-1]
                print(error_list)
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

#for manage employee and admin payroll
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
                )
            _today = _today.replace(month=month, year=year, day=1)

            current_year = _today.year
            all_years = sorted([current_year - i for i in range(1, 2)] + [current_year + i for i in range(0, 7)])
            if request.GET.get('employee_id'):
                payslip = PaySlip.objects.filter(
                employee_payslip = request.GET.get('employee_id'),
                dispatch_date__month=1 if month == 12 else month+1,
                dispatch_date__year=year+1 if month == 12 else year
                ).first()
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
                'month_list':MONTH_LIST,
                'total_employees':
                 Employee.objects.count(),
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
                                    dispatch_date__year=year+1 if month == 12 else year
                                    ).first()
                if not payslip and request.GET.get('q') != "ajax":
                    get_payslip = PaySlip.objects.filter(employee_payslip = employee)
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
        if request.user.is_superuser == True:
            #--find all register employee and there data---------------------------------
            all_employee = Employee.objects.filter(role="EMPLOYEE")
            ok_flag = True
            if all_employee:
                for employee in all_employee:
                    if not (employee.name and employee.department and employee.designation and employee.salary and EmployeeBankDetail.objects.filter(employee_bankdetail=employee).exists()):
                        ok_flag = False
                        break
                if ok_flag == True:
                    for employee in all_employee:
                        total_leave_days = 0
                        full_day = 0
                        half_day = 0
                        employee_leave = LeaveManagement.objects.filter(employee_id=employee, status="APPROVED", leave_type="UNPAID", leave_start_date__month=PRE_MONTH.month)
                        print("EMPLOYEE: ", employee, total_leave_days, employee_leave)
                        for leave in employee_leave:
                            if leave.leave_start_date.month == PRE_MONTH.month:
                                if leave.leave_requested_for == "F":
                                    full_day += 1
                                    total_leave_days += leave.leave_days*1
                                else:
                                    half_day += 1
                                    total_leave_days += leave.leave_days*0.5
                        effective_working_day = TOTAL_DAYS-total_leave_days

                        employee_total_earning = int(effective_working_day*(employee.salary/TOTAL_DAYS))
                        earning_in_words = numtowords(employee_total_earning)

                    #----creating unique pdf name---------------------------
                        do = DATE_OBJECT.strftime("%B%Y").upper()
                        pdf_name=f"{do}{employee.user.username}.pdf"

                    #--------------------find each employee bank detail---------------------------
                        emp_bankdetail = EmployeeBankDetail.objects.get(employee_bankdetail=employee)

                    #--- Define Filepath where PDF Save -----------------------------------
                        filedir = 'media/pdf_file/'
                        filepath = os.path.join(filedir,pdf_name)

                    #---this is base_data that will be change by month----------------------
                        base_data ={'total_earn': employee_total_earning,
                                    'effectiveworks':TOTAL_DAYS,
                                    'losspayday': int(math.ceil(total_leave_days)),
                                    'totalpaydays': int(effective_working_day),
                                    'earning_in_words':earning_in_words,
                                    'salary_month_name':SALARY_MONTH,
                                    'employee_joining_date':employee.user.date_joined.date(),
                                    'filepath':filepath,
                                    }
                    #---check pdf is generated or not---------------
                        oldpayslip = PaySlip.objects.filter(employee_payslip = employee, payslip_name = pdf_name)
                    #---create new payslip object----------------
                        if not oldpayslip:
                            create_payslip = PaySlip.objects.create(
                                employee_payslip = employee,
                                path = filepath,
                                dispatch_date = date.today(),
                                leave_taken = total_leave_days,
                                full_day = full_day,
                                half_day = half_day,
                                salary=employee.salary,
                                payslip_name= pdf_name,
                                earning=base_data['total_earn'])
                            create_payslip.save()
                    #----generate pdf only if old pdf not register for old month-------------
                            context = {'employee':employee, 'base_data':base_data, 'bank_detail':emp_bankdetail}
                            generate_pdf(context, send_email=True)
                        else:
                            messages.add_message(request, messages.INFO, f"{SALARY_MONTH} salary is already generated.")
                            return redirect("/payroll_expenses/")
                    messages.success(request, f'{SALARY_MONTH} salary generated successfully')
                    return redirect("/payroll_expenses/")
                else:
                    messages.add_message(request, messages.WARNING, f"Either employee name, department, designation, salary and Bank Details or anyone of these is missing for user, {employee.user}. Please provide it first.")
                    return redirect("/payroll_expenses/")
            else:
                messages.add_message(request, messages.INFO, "There is no Employee.")
                return redirect("/payroll_expenses/")
        else:
            return HttpResponse("Only admin Access..")

#this is we show aemployee profile we show for admin still need to update
class EmployeeProfileAdmin(View):
    def get(self, request, pk=None):
        if self.request.user.is_superuser==True:
            emps = Employee.objects.exclude(role='ADMIN')
            year = datetime.now().year
            emp = Employee.objects.get(id = pk)
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
            form.save()
            messages.add_message(request, messages.SUCCESS, "Holiday created successfully.")
        else:
            error_list = " "
            for field, errors in form.errors.items():
                for error in errors:
                    error_list += error+' ,'
            error_list = error_list[:-1]
            messages.add_message(request, messages.WARNING, error_list)
        return redirect(reverse("profile"))

class EmployeeAboutView(View):
    def get(self, request, pk=None):
        if self.request.user.is_superuser==True:
            employee = Employee.objects.get(user = pk )
            return render(request, 'admin/employee-about.html',  { "emp":employee})
        else:
            employee = Employee.objects.get(user = request.user )
            return render(request, 'hrm/employee-about.html',  { "emp":employee})

from datetime import datetime, date
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Sum
from django.urls import reverse
import itertools 
from core.utils.dates import Date

from hrm.choice import GENDER_CHOICES,  USER_ROLE, LEAVE_TYPES, STATUS_CHOICE
from core.models.models import SystemField
from django.contrib.auth.hashers import make_password
from core.utils.mailer import Mailer
from django.template.loader import render_to_string
from django.conf import settings



class CompanyDetail(SystemField):
    """
    Company Detail modeal help to save company deatils and we can use it for pay slip
    """

    company_name = models.CharField(max_length=100, null=False, blank=False)
    address = models.CharField(max_length=100, null=False, blank=False)
    pincode = models.IntegerField()
    city = models.CharField(max_length=100, null=False, blank=False)
    state = models.CharField(max_length=100, null=False, blank=False)

    def __str__(self):
        return self.company_name

    def get_absolute_url(self):
        return reverse("student_detail", args=[str(self.id)])

# class EmployeeManager:

class Employee(SystemField):
    """
    Employees Detail modeal help create profile of user Where we will also define role of user
    that will be helpful for create payslip
    """

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="user_employee"
    )
    profile_image = models.ImageField(upload_to='media/',default='media/defaultprofile.jpeg' )
    role = models.CharField(
        max_length=12, choices=USER_ROLE, default="GENERAL_USER")
    name = models.CharField(max_length=70, null=True, blank=True)
    gender = models.CharField(
        max_length=6, null=True, blank=True, choices=GENDER_CHOICES
    )
    dob = models.DateField(null=True, blank=True)
    mobile = models.CharField(
        max_length=10, null=False, blank=False, default="9999999999"
    )
    address = models.CharField(max_length=70, null=True, blank=True)
    pincode = models.IntegerField(default=208023)
    city = models.CharField(max_length=70, null=True, blank=True)
    state = models.CharField(max_length=70, null=True, blank=True)
    department = models.CharField(max_length=70, null=True, blank=True)
    designation = models.CharField(max_length=70, null=True, blank=True)
    about = models.TextField()
    manager = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True)
    salary = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.user.username

    def get_absolute_url(self):
        return reverse("student_detail", args=[str(self.id)])

    def get_username(self):
        return getattr(self, self.user)

class EmployeeManager(Employee):

    def get_all(self):
        self._date = Date(date.today().replace(month=7))
        self.joining_date = self.user.date_joined.date
        x = self.cary_forward_leaves()

        self._date = Date(self._date.get_semesters()[0])

        y = self.cary_forward_leaves()
        return x + y
    
    def cary_forward_leaves(self):
        start_semester, end_semester = self._date.get_semesters()
        carry = 0
        if self.user.date_joined.date() < date.today().replace(day=1, month=10, year=2022):
            carry = 6 - (self.leaves.filter(
                leave_type="PAID", 
                status = "APPROVED",
                leave_start_date__gte = start_semester, 
                leave_start_date__lte = end_semester).aggregate(
                    leaves = Sum('leave_days')
            )["leaves"] or 0)
        if carry:
            if carry >= 3: 
                if start_semester.month == 1:
                    return carry
                return 3
            return carry 
        return 0

    class Meta:
        proxy = True
class EmployeeBankDetail(SystemField):
    """
    It's Employee bank details, We will save only one bank details for each employee
    we will use this bank details for send salary for each month 
    """

    employee_bankdetail = models.OneToOneField(
        Employee, on_delete=models.CASCADE, related_name="employee_bank_detail"
    )
    bank_name = models.CharField(max_length=70, null=True, blank=True)
    account_holder_name = models.CharField(
        max_length=70, null=True, blank=True)
    branch = models.CharField(max_length=70, null=True, blank=True)
    bank_account_no = models.CharField(max_length=70, null=True, blank=True)
    ifsc_code = models.CharField(max_length=70, null=True, blank=True)
    pan_no = models.CharField(max_length=70, null=True, blank=True)
    pf_no = models.CharField(max_length=70, null=True, blank=True)
    pf_uan = models.CharField(max_length=70, null=True, blank=True)

    def get_username(self):
        return self.employee_bankdetail

class PaySlip(SystemField):
    """
    here we will create payslip for user and save it for each month with basic details
    """

    employee_payslip = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="employee_payslip"
    )
    payslip_name = models.CharField(max_length=250, null=False, blank=False)
    path = models.FilePathField(max_length=250, path="media", null=False, blank=False)
    dispatch_date = models.DateField()
    salary = models.IntegerField(default=0)
    earning = models.IntegerField(default=0)

    def __str__(self) -> str:
        return f"{self.employee_payslip}"

    def get_username(self):
        return self.employee_payslip

    @property
    def deduction(self):
        return self.salary - self.earning

    def notify_admin(self):
        import pdb;pdb.set_trace()
        self.process_email(
            "Leave Request",
            self.leave_request_template(),
            settings.SUPER_ADMIN_EMAILS 
        )
class LeaveManagement(models.Model):
    """
    we will track leave for all employee
    once leave will be counted we can evaluate salary for user 
    """
    employee_id = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='leaves')
    leave_reason = models.TextField()
    leave_days = models.IntegerField()
    leave_start_date = models.DateField()
    leave_type = models.CharField(max_length=10, choices=LEAVE_TYPES)
    status = models.CharField(
        max_length=10, null=True, blank=True, default='PENDING', choices=STATUS_CHOICE)

    def __str__(self):
        return str(self.employee_id)+" "+str(self.leave_days)+" "+self.leave_type

    def curr(self):
        return self.leave_start_date.date.days

    def create_leave(self, _nxt):
        self.pk = None
        self.leave_days = _nxt.__len__()
        self.leave_start_date = _nxt[0]
        self.save()
        print("I am creating another leave")

    def save(self, *args, **kwargs):
        if not self.pk:
            self.notify_admin()
        _date = Date(self.leave_start_date)
        days = _date.get_next_working_days(self.leave_days)
        _nxt = [*itertools.dropwhile(lambda x : x.month == self.leave_start_date.month, days)]
        self.leave_days = self.leave_days - _nxt.__len__()
        instance = super().save(*args, **kwargs)
        if _nxt: 
            self.create_leave(_nxt)
        return instance

    def get_username(self):
        return self.employee_id

    def leave_request_template(self):
        return render_to_string("leave_request_email.html", {"obj":self})

    def notify_admin(self):
        self.process_email(
            "Leave Request",
            self.leave_request_template(),
            settings.SUPER_ADMIN_EMAILS 
        )

    def process_email(self, subject, message, email_to):
        Mailer(
            subject=subject, 
            message=message,
            email_to= email_to,
        ).send()

    def notify_user(self, action):
        self.process_email(
            f"Leave Request  {action}",
            self.leave_request_template(),
            [self.employee_id.user.email],
        )
     
    def approve_leave(self): 
        self.status = "APPROVED"
        self.save()
        self.notify_user(self.status)

    def reject_leave(self): 
        self.status = "REJECTED"
        self.save()
        self.notify_user(self.status)

class HolidayList(models.Model):
    holiday_name = models.CharField(max_length=200, blank=True, null=True)
    holiday_date = models.DateField()

    def __str__(self):
        return str(self.holiday_name)
    
    

from typing import Any, Dict
from django import forms
from django.core.exceptions import ValidationError
import re
from datetime import datetime
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User
from hrm.models import Employee, LeaveManagement, HolidayList, EmployeeBankDetail, PaySlip
from PIL import Image


class UserEditForm(forms.Form):
    email = forms.EmailField(required=True)
    username = forms.CharField(required=True)
    password1 = forms.CharField(widget=forms.PasswordInput, label='Password')
    password2 = forms.CharField(widget=forms.PasswordInput, label='Confirm Password')

    def clean(self):
        username = self.cleaned_data.get('username')
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        email = self.cleaned_data.get('email')

        if password1 == None or not (any(c.isalpha() for c in password1) and any(c.isdigit() for c in password1) and not password1.isalnum()):
            self._errors['password1'] = self.error_class(['Password must contain the combination of letter, number and special character'])
        if len(username) < 8:
            self._errors['username'] = self.error_class(['Username must be minimum of 8 characters in length'])

        if len(password1) < 8:
            self._errors['password1'] = self.error_class(['Password length should not be less than 8 characters'])

        if password1 != password2 :
            self._errors['password1'] = self.error_class(['Password and confirm password are not same'])
        return self.cleaned_data

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_username(self):
        # Bypass username existence checking
        return self.cleaned_data.get('username')

    def save(self, commit=True):
        user = super(UserRegisterForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

    def clean(self):
        super(UserRegisterForm, self).clean()

        # getting username and password from cleaned_data
        username = self.cleaned_data.get('username')
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        email = self.cleaned_data.get('email')

        if password1 == None or not (any(c.isalpha() for c in password1) and any(c.isdigit() for c in password1) and not password1.isalnum()):
            self._errors['password1'] = self.error_class(['Password must contain the combination of letter, number and special character'])
        if len(username) < 8:
            self._errors['username'] = self.error_class(['Username must be minimum of 8 characters in length'])

        if len(password1) < 8:
            self._errors['password1'] = self.error_class(['Password length should not be less than 8 characters'])

        if password1 != password2 :
            self._errors['password1'] = self.error_class(['Password and confirm password are not same'])
        return self.cleaned_data

class EmailForm(forms.Form):
    to = forms.EmailField()
    subject = forms.CharField()
    message = forms.CharField(widget=forms.Textarea)


class UserUpdateForm(forms.ModelForm):
    dob = forms.DateField(widget=forms.TextInput(attrs={"type": "date"}))

    class Meta:
        model = Employee
        exclude = ["name", "user", "salary", "paid_days"]


class EmployeeProfileForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ["profile_image"]

class EmployeeProfileEditForm(forms.ModelForm):
    genderselect = forms.CharField()
    profile_image = forms.ImageField()
    class Meta:
        model = Employee
        fields = ["name", "profile_image", "dob", "gender", "mobile", "address", "pincode", "city", "state"]

    def clean(self):
        super(EmployeeProfileEditForm, self).clean()
        name = self.cleaned_data.get('name')
        profile_image = self.cleaned_data.get('profile_image')
        gender = self.cleaned_data.get('genderselect')
        dob = self.cleaned_data.get('dob')
        mobile = str(self.cleaned_data.get('mobile'))
        address = self.cleaned_data.get('address')
        pincode = str(self.cleaned_data.get('pincode'))
        city = self.cleaned_data.get('city')
        state = self.cleaned_data.get('state')

        if name == None or not name.replace(" ", "").isalpha():
            self._errors['name'] = self.error_class(["Employee name only accept alpha characters and should not be empty."])
        if not address:
            self._errors['address'] = self.error_class(["Address is required."])
        if not  city.replace(" ", "").isalpha():
            self._errors['city'] = self.error_class(["City only accept alpha characters and should not be empty."])
        if not state.replace(" ", "").isalpha():
            self._errors['state'] = self.error_class(["State only accept alpha characters and should not be empty."])
        if gender not in ["MALE", "FEMALE"]:
            self._errors['gender'] = self.error_class(["Please select gender."])
        if not (pincode.isdigit() and int(pincode) > 0):
            self._errors['pincode'] = self.error_class(["Pincode only accept numbers and should not be empty or Zero."])
        if not (mobile.isdigit() and int(mobile) > 0 and len(mobile) == 10 ):
            self._errors['mobile'] = self.error_class(["Mobile only accept numbers and should be equal to 10 digit."])

        if not dob == None:
            try:
                dob_ = dob.strftime("%Y-%m-%d")
                datetime.strptime(dob_, '%Y-%m-%d')
            except ValueError:
                self._errors['dob'] = self.error_class(["D.O.B date is not a valid date"])
        else:
            self._errors['dob'] = self.error_class(["Please enter date of birth."])

        if profile_image:
            # Get the file extension
            file_ext = profile_image.name.split('.')[-1]

            # Check the file extension
            if file_ext.lower() not in ['jpg', 'jpeg', 'png']:
                self._errors['profile_image'] = self.error_class(['File type not supported. Please upload a JPEG, JPG or PNG file.'])

            # Check if the file is a valid image file
            try:
                with Image.open(profile_image) as image:
                    image.verify()
            except:
                self._errors['profile_image'] = self.error_class(['File is not a valid image file.'])
        else:
            self._errors['profile_image'] = self.error_class(["Please choose Profile Image of supported type JPEG, JPG or PNG"])
        return self.cleaned_data
    
    def save(self, user=None, commit=True):
        name = self.cleaned_data['name']
        profile_image = self.cleaned_data['profile_image']
        gender = self.cleaned_data['genderselect']
        dob = self.cleaned_data['dob']
        mobile = self.cleaned_data['mobile']
        address = self.cleaned_data['address']
        pincode = self.cleaned_data['pincode']
        city = self.cleaned_data['city']
        state = self.cleaned_data['state']
        emp_detail, created = Employee.objects.get_or_create(
        user = user,
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
        return emp_detail

class AdminEmployeeProfileEditForm(forms.ModelForm):
    role = forms.CharField()
    class Meta:
        model = Employee
        fields = ["designation", "department", "role", "salary"]

    def clean(self):
        super(AdminEmployeeProfileEditForm, self).clean()
        designation = self.cleaned_data.get('designation')
        department = self.cleaned_data.get('department')
        role = self.cleaned_data.get('role')
        salary = str(self.cleaned_data.get('salary'))

        if designation == None or not designation.replace(" ", "").isalpha():
            self._errors['designation'] = self.error_class(["Designation only accept alpha characters and should not be empty."])
        if department == None or not department.replace(" ", "").isalpha():
            self._errors['department'] = self.error_class(["Department only accept alpha characters and should not be empty."])
        if role not in ["ADMIN", "EMPLOYEE", "GENERAL_USER"]:
            self._errors['role'] = self.error_class(["Please select a role."])
        if not (salary.isdigit() and int(salary) > 0):
            self._errors['salary'] = self.error_class(["Salary only accept numbers and should not be empty or Zero."])
        return self.cleaned_data
    
    def save(self, pk, manager, commit=True):
        designation = self.cleaned_data['designation']
        role = self.cleaned_data['role']
        department = self.cleaned_data['department']
        salary = self.cleaned_data['salary']
        manager_instance = Employee.objects.get(user=manager)
        emp_detail, created = Employee.objects.get_or_create(
        user = pk,
        defaults={
            'designation': designation,
            'role': role,
            'department': department,
            'salary': salary,
            'manager': manager_instance,
            }
        )
        if not created:
            emp_detail.designation = designation
            emp_detail.role = role
            emp_detail.department = department
            emp_detail.salary = salary
            emp_detail.manager = manager_instance
            emp_detail.save()
        return emp_detail

class EmployeeBankDetailsEditForm(forms.ModelForm):
    class Meta:
        model = EmployeeBankDetail
        fields = ["bank_name", "branch", "bank_account_no", "account_holder_name", "ifsc_code", "pan_no"]
    def clean(self):
        super(EmployeeBankDetailsEditForm, self).clean()
        bank_name = self.cleaned_data['bank_name']
        branch = self.cleaned_data['branch']
        bank_account_no = self.cleaned_data['bank_account_no']
        account_holder_name = self.cleaned_data['account_holder_name']
        ifsc_code = self.cleaned_data['ifsc_code']
        pan_no = self.cleaned_data['pan_no']
        if bank_name == None or not bank_name.replace(" ", "").isalpha():
            self._errors['bank_name'] = self.error_class(["Bank name only accept alpha characters and should not be empty."])
        if branch == None or not branch.replace(" ", "").isalnum():
            self._errors['branch'] = self.error_class(["Branch name only accept alpha characters and should not be empty."])
        if not (bank_account_no.isdigit() and len(bank_account_no) > 0):
            self._errors['bank_account_no'] = self.error_class(["Account number should be number only and should not be empty."])
        if account_holder_name == None or not account_holder_name.replace(" ", "").isalpha():
            self._errors['account_holder_name'] = self.error_class(["Account holder name only accept alpha characters and should not be empty."])
        if ifsc_code == None or not (ifsc_code.isalnum() and any(c.isalpha() for c in ifsc_code) and any(c.isdigit() for c in ifsc_code)):
            self._errors['ifsc_code'] = self.error_class(["IFSC code should be combined of letters and numbers and should not be empty."])
        if pan_no == None or not (pan_no.isalnum() and any(c.isalpha() for c in pan_no) and any(c.isdigit() for c in pan_no)):
            self._errors['pan_no'] = self.error_class(["PAN number should be combined of letters and numbers and should not be empty."])
        return self.cleaned_data
    
    def save(self, employee, commit=True):
        bank_name = self.cleaned_data['bank_name']
        branch = self.cleaned_data['branch']
        bank_account_no = self.cleaned_data['bank_account_no']
        account_holder_name = self.cleaned_data['account_holder_name']
        ifsc_code = self.cleaned_data['ifsc_code']
        pan_no = self.cleaned_data['pan_no']

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
        return bank_detail

class LeaveManagementForm(forms.ModelForm):
    class Meta:
        model = LeaveManagement
        fields = ("leave_reason", "leave_days", "leave_start_date", "leave_type", "leave_requested_for")
        exclude = ["employee_id", "status"]
        widgets = {
        'leave_start_date': forms.DateInput(attrs={'class':'form-control', 'placeholder':'Select a date', 'type':'date'}),
    }
    def clean(self):
        super(LeaveManagementForm, self).clean()
        leave_reason = self.cleaned_data.get('leave_reason')
        leave_days = str(self.cleaned_data.get('leave_days'))
        start_date = self.cleaned_data.get('leave_start_date')
        leave_type = self.cleaned_data.get('leave_type')
        leave_requested_for = self.cleaned_data.get('leave_requested_for')

        if not leave_requested_for == None or not leave_requested_for:
            if leave_requested_for not in ["F", "FH", "SH"]:
                self._errors['leave_requested_for'] = self.error_class(["Please select leave requested for"])

        if not leave_reason:
            self._errors['leave_reason'] = self.error_class(["Leave reason is required"])
        if not (leave_days.isdigit() and int(leave_days) > 0) :
            self._errors['leave_days'] = self.error_class(['Number of leave days should be in number and greater than Zero'])

        if not start_date == None:
            try:
                start_date_ = start_date.strftime("%Y-%m-%d")
                datetime.strptime(start_date_, '%Y-%m-%d')
            except ValueError:
                self._errors['start_date'] = self.error_class(["Leave start date is not a valid date"])
        else:
            self._errors['start_date'] = self.error_class(["Please enter leave start date."])

        if leave_type not in ["PAID", "UNPAID"]:
            self._errors['leave_type'] = self.error_class(["Please select leave type"])
        return self.cleaned_data
    
    def save(self, leave_id, employee, commit=True):
        leave_reason = self.cleaned_data["leave_reason"]
        leave_type = self.cleaned_data["leave_type"]
        leave_requested_for = self.cleaned_data["leave_requested_for"]
        leave_days = self.cleaned_data["leave_days"]
        start_date = self.cleaned_data["leave_start_date"]
        leave_record, created = LeaveManagement.objects.get_or_create(
            id = leave_id,
            defaults={
                "employee_id": employee,
                "leave_reason": leave_reason,
                "leave_days": leave_days,
                "leave_start_date": start_date,
                "leave_type": leave_type,
                "leave_requested_for": leave_requested_for,
                "status": "PENDING"
            }
        )
        if not created:
            leave_record.leave_reason = leave_reason
            leave_record.leave_days = leave_days
            leave_record.leave_start_date = start_date
            leave_record.leave_requested_for = leave_requested_for
            leave_record.leave_type = leave_type
            leave_record.status = "PENDING"
            leave_record.save()
        return leave_record

class SignUpForm(UserCreationForm):
    email = forms.EmailField(label="", widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Email Address'}), )
    first_name = forms.CharField(label="", max_length=100, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'First Name'}))
    last_name = forms.CharField(label="", max_length=100, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Last Name'}))


    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2',)


class HolidayForm(forms.ModelForm):
    class Meta:
        model = HolidayList
        fields = "__all__"
    def clean(self):
        super(HolidayForm, self).clean()
        holiday_date = self.cleaned_data.get('holiday_date')
        holiday_name = self.cleaned_data.get('holiday_name')

        if not holiday_name:
            self._errors['holiday_name'] = self.error_class(['Holiday name is required'])

        if not holiday_date == None:
            try:
                holiday_date_ = holiday_date.strftime("%Y-%m-%d")
                datetime.strptime(holiday_date_, '%Y-%m-%d')
            except ValueError:
                self._errors['holiday_date'] = self.error_class(['Holiday date is not a valid date'])
        else:
            self._errors['holiday_date'] = self.error_class(['Please enter holiday date.'])
        return self.cleaned_data





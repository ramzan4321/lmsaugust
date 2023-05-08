from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from hrm.models import Employee, LeaveManagement, HolidayList


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

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
        

        # validating the username and password
        if len(username) < 5:
            self._errors['username'] = self.error_class(['A minimum of 5 characters is required'])

        if len(password1) < 8:
            self._errors['password1'] = self.error_class(['Password length should not be less than 8 characters'])
            
        if password1 != password2 :
            self._errors['password1'] = self.error_class(['Password DOES NOT match with password1'])
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

class  LeaveManagementForm(forms.ModelForm):
    class Meta:
        model = LeaveManagement
        fields = ("leave_reason", "leave_days", "leave_start_date", "leave_type")
        exclude = ["employee_id", "status"]
        widgets = {
        'leave_start_date': forms.DateInput(attrs={'class':'form-control', 'placeholder':'Select a date', 'type':'date'}),
    }

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
from django.contrib import admin
from hrm.models import (CompanyDetail, Employee, EmployeeBankDetail, PaySlip,
                        LeaveManagement, EmployeeManager, HolidayList)


class UserCompanyDetail(admin.ModelAdmin):
    list_display = ('company_name', 'address', 'pincode', 'city', 'state')

# class PaySlipInline(admin.TabularInline):
#     model = PaySlip
#     fk_name = "employee_payslip"

class EmployeeBankDetailInline(admin.TabularInline):
    model = EmployeeBankDetail
    fk_name = "employee_bankdetail"

class UserDetail(admin.ModelAdmin):
    list_display = ('name', 'gender', 'dob', 'mobile',
                    'department', 'designation', 'salary')
    fields = ('user', 'name', 'role', 'profile_image', 'gender', 'dob', 'mobile', 'address', 'pincode',
              'state', 'department', 'designation', 'about', 'salary')
    raw_id_fields = ('user', 'manager',)
    inlines = [ EmployeeBankDetailInline]



class EmployeePaySlip(admin.ModelAdmin):
    list_display = ('employee_payslip','salary', 'earning', 'dispatch_date','payslip_name')
    readonly_fields = ['path']
    raw_id_fields = ('employee_payslip',)
    list_filter = ('dispatch_date',)


class EmpBankDetail(admin.ModelAdmin):
    list_display = ('bank_name', 'account_holder_name',
                    'branch', 'bank_account_no', 'ifsc_code')
    fields = ('employee_bankdetail', 'bank_name', 'account_holder_name', 'branch',
              'bank_account_no', 'ifsc_code', 'pan_no', 'pf_no', 'pf_uan')
    raw_id_fields = ('employee_bankdetail', )


class EmpLeaveManagement(admin.ModelAdmin):
    list_display = ('employee_id', 'leave_reason', 'leave_days', 'leave_start_date', 'leave_type', 'status')
    # raw_id_fields = ('employee_id', )
    list_filter = ('employee_id','leave_type')
    def get_readonly_fields(self, request, obj):
        if not request.user.is_superuser:
            return ("status",)
        return super().get_readonly_fields(request, obj)

class HolidayListAdmin(admin.ModelAdmin):
    list_display = ('holiday_name', 'holiday_date')
    fields = ('holiday_name', 'holiday_date')

admin.site.register(CompanyDetail, UserCompanyDetail)
admin.site.register(Employee, UserDetail)
admin.site.register(EmployeeManager )
admin.site.register(PaySlip, EmployeePaySlip)
admin.site.register(EmployeeBankDetail, EmpBankDetail)
admin.site.register(LeaveManagement, EmpLeaveManagement)
admin.site.register(HolidayList, HolidayListAdmin)

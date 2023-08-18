from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from hrm import views

# app_name = "hrm"

urlpatterns = [
    path('login/', views.login_user.as_view(), name ='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('register/', views.registerView.as_view(), name='register'),
    path('edit_registered_user/', views.EditRegisterUserView.as_view(), name='edit_registered_user'),
    path('', views.ProfileListView.as_view(), name='profile'),
    path('leave/', views.LeaveRequestView.as_view(), name='leave'),
    path('leave/<int:days>/<str:start>/', views.LeaveRequestView.as_view(), name='leave'),
    path('week/<str:week>/', views.LeaveRequestView.as_view(), name='week'),
    path('leave/<int:pk>', views.LeaveRequestView.as_view(), name='leave'),
    path('accounts/profile/', views.ProfileListView.as_view(), name='profile'),
    path('profile/<int:pk>', views.EmployeeProfileAdmin.as_view(), name='emp_profile'),
    path('employees/', views.EmployeesListAdmin.as_view(), name='employees'),
    path('edit_profile/<int:pk>', views.EmployeeProfileView.as_view(), name='employees'),
    path('emp_payroll', views.PayRollView.as_view(), name='emp_payroll'),
    path('payroll_expenses/', views.PayRollView.as_view(), name='payroll_expense'),
    path('empbank/', views.EmpBankDetail.as_view(), name='empbank'),
    path('empbank/<int:pk>', views.EmpBankDetail.as_view(), name='empbank'),
    path('empprofile/', views.EmployeeProfileView.as_view(), name='empprofile'),
    path('empabout/<int:pk>', views.EmployeeAboutView.as_view(), name='empabout'),
    path('empabout/', views.EmployeeAboutView.as_view(), name='empabout'),
    path('adminemppayroll/<int:pk>', views.AdminEmpPayroll.as_view(), name='adminemppayroll'),
    path('adminemppayroll/<int:pk>/<int:month>/<int:year>/', views.AdminEmpPayroll.as_view(), name='adminemppayroll'),
    path('payroll_expenses/<int:month>/<int:year>/',views.PayRollView.as_view(), name='payroll_expense'),
    path('holiday/',views.HolidayView.as_view(), name='holiday'),
    path('get_holiday/', views.HolidayView.as_view(), name="get_holiday"),
    path('delete_holiday/<int:pk>', views.HolidayView.as_view(), name="delete_holiday"),
    path('get_leave_info/', views.LeaveRequestView.as_view(), name="get_leave_info"),
    path('delete_leave/<int:leave_id>', views.LeaveRequestView.as_view(), name="delete_leave"),
    path('get_payroll_info/', views.PayRollUpdate.as_view(), name="get_payroll_info"),
    path('proceed_salary/', views.ProceedToGeneratePayslip.as_view(), name="proceed_to_generate_payslip"),
    path('stop_payslip/', views.StopPayslip.as_view(), name="stop_payslip"),
    path('send_payslip/', views.SendPayslip.as_view(), name="send_payslip"),

    path('add_designation/', views.AddDesignation.as_view(), name="add_designation"),
    path('edit_designation/', views.EditDesignation.as_view(), name="edit_designation"),

    path('add_department/', views.AddDepartment.as_view(), name="add_department"),
    path('edit_department/', views.EditDepartment.as_view(), name="edit_department"),

    path('get_user_info/', views.UserInfo.as_view(), name="get_user_info"),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from hrm import views

# app_name = "hrm"

urlpatterns = [
    path('login/', views.login_user.as_view(), name ='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('register/', views.registerView.as_view(), name='register'),
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

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

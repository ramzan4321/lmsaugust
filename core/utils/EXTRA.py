from hrm.models import *
x = EmployeeManager.objects.get(pk=1)
x.get_all()
x.cary_forward_leaves()

from django.utils.translation import gettext_lazy as _
from model_utils import Choices

GENDER_CHOICES = Choices(
    ("MALE", "male", _("Male")),
    ("FEMALE", "female", _("female")),
)

USER_ROLE = Choices(
    ("ADMIN", "admin", _("Admin")),
    ("EMPLOYEE", "employee", _("Employee")),
    ("GENERAL_USER", "general_user", _("General_User")),
)

LEAVE_TYPES = Choices(
    ("PAID", "paid", _("Paid")),
    ("UNPAID", "unpaid", _("Unpaid")),
)

STATUS_CHOICE = Choices(
    ("APPROVED", "approved", _("Approved")),
    ("REJECTED", "rejected", _("Rejected")),
    ("PENDING", "pending", _("Pending")),
)

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

LEAVE_FOR = Choices(
    ("F", "Full day", _("Full day")),
    ("FH", "First half", _("First half")),
    ("SH", "Second half", _("Second half")),
)

STATUS_CHOICE = Choices(
    ("APPROVED", "approved", _("Approved")),
    ("REJECTED", "rejected", _("Rejected")),
    ("PENDING", "pending", _("Pending")),
)

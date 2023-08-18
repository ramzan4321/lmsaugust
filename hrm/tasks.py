from celery import shared_task
from celery.utils.log import get_task_logger
from datetime import datetime
from hrm.views import pay_slip_pdf_generate, send_pay_slip_to_employee

logger = get_task_logger(__name__)


@shared_task()
def send_review_email_task():
    day = datetime.now().day
    if day != 1:
        return "Payslip only generate on 1st day of everymonth"
    else:
        logger.info("Sent Payslip email")
        return pay_slip_pdf_generate()
    

@shared_task()
def send_payslip_to_employee():
    day = datetime.now().day
    if day != 3:
        return "Payslip only send on 3rd day of everymonth to employee"
    else:
        return send_pay_slip_to_employee()

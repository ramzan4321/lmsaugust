import os
from django.http import FileResponse
from datetime import  date
from django.core.files.storage import FileSystemStorage
from reportlab.pdfgen import canvas
from reportlab.platypus import Image
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from hrm.models import PaySlip
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from core.utils.mailer import Mailer
from django.conf import settings

def generate_pdf(*args,**kwargs):
    employee = args[0]['employee']
    bank_detail = args[0]['bank_detail']
    base_data = args[0]['base_data']
    extra_line = args[0]['extra_line']

    pdfmetrics.registerFont(TTFont('LSB', os.path.join('media/font', 'LiberationSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('LSR', os.path.join('media/font', 'LiberationSerif-Regular.ttf')))
    pdfmetrics.registerFont(TTFont('LSRI', os.path.join('media/font', 'LiberationSerif-Italic.ttf')))
    pdfmetrics.registerFont(TTFont('LSBI', os.path.join('media/font', 'LiberationSerif-BoldItalic.ttf')))

    #---------------------------- Generate Payslip PDF ------------------------------------------
    c = canvas.Canvas(base_data['filepath'], pagesize=letter)
    width, height = letter
    c.setFont('LSB',11)
    c.setStrokeColor('grey')
    
    c.setLineWidth(1)
    c.setStrokeColor('black')
    if extra_line:
        c.rect(0.6*inch, 6.75*inch, 7.3*inch, 3.65*inch,fill=0,stroke=True)
        c.line(0.6*inch, 9.6*inch, 7.9*inch, 9.6*inch)
        c.line(0.6*inch, 8.3*inch, 7.9*inch, 8.3*inch)
        c.line(0.6*inch, 8.05*inch, 7.9*inch, 8.05*inch)
        c.line(0.6*inch, 7.8*inch, 7.9*inch, 7.8*inch)
        c.line(0.6*inch, 7.55*inch, 7.9*inch, 7.55*inch)
        c.line(0.6*inch, 7.3*inch, 7.9*inch, 7.3*inch)
        c.line(4.2*inch, 9.6*inch, 4.2*inch, 7.3*inch)
    else:
        c.rect(0.6*inch,7*inch,7.3*inch,3.4*inch,fill=0,stroke=True)
        c.line(0.6*inch,9.6*inch,7.9*inch,9.6*inch)
        c.line(0.6*inch,8.3*inch,7.9*inch,8.3*inch)
        c.line(0.6*inch,8.05*inch,7.9*inch,8.05*inch)
        c.line(0.6*inch,7.8*inch,7.9*inch,7.8*inch)
        c.line(0.6*inch,7.55*inch,7.9*inch,7.55*inch)
        c.line(4.2*inch,9.6*inch,4.2*inch,7.55*inch)

    # To create horizontal line set margin-top same.
    # To create vertical line set margin-left same.
    # Example of drawing a line : c.line( margin-top , margin-left , margin-top , margin-left)

    
    
    im = Image('media/01.png', 0.57*inch ,0.62*inch, hAlign="CENTER")   
    im.wrapOn(c, width, height)           
    im.drawOn(c,0.8*inch, 9.7*inch)
    

    c.drawString(3.5*inch,10.17*inch,'Triodec Solutions LLP')
    c.setFont('LSR',7)
    c.drawString(3.1*inch,10.01*inch,'PRAHLADNAGAR, AHMEDABAD, GUJARAT -')
    c.setFont('LSR',8)
    c.drawString(5.2*inch,10.01*inch,'380015')
    c.setFont('LSB',12)
    c.drawString(3.3*inch,9.75*inch, f"PAYSLIP {base_data['salary_month_name']}")
    
    c.setFont('LSR',9)
    c.drawString(0.65*inch,9.45*inch,'Employee Name:')
    c.drawString(0.65*inch,9.27*inch,'Joining Date:')
    c.drawString(0.65*inch,9.09*inch,'Designation:')
    c.drawString(0.65*inch,8.91*inch,'Department:')
    c.drawString(0.65*inch,8.72*inch,'Effective Work Days:')
    c.drawString(0.65*inch,8.54*inch,'Loss of Pay Days:')
    c.drawString(0.65*inch,8.36*inch,'Days Payable:')


    c.setFont('LSR',9)
    if employee.name:
        c.drawString(2.25*inch,9.45*inch, employee.name)
    else:
        c.drawString(2.25*inch,9.45*inch, '-')
    c.drawString(2.25*inch,9.27*inch, str(base_data['employee_joining_date']))
    c.drawString(2.25*inch,9.09*inch, employee.designation)
    c.drawString(2.25*inch,8.91*inch, employee.department)
    c.drawString(2.25*inch,8.72*inch, str(base_data['effectiveworks']))
    c.drawString(2.25*inch,8.54*inch, str(base_data['losspayday']))
    c.drawString(2.25*inch,8.36*inch, str(base_data['totalpaydays']))

    c.setFont('LSR',9)
    c.drawString(4.25*inch,9.45*inch,'Employee No:')
    c.drawString(4.25*inch,9.27*inch,'Bank Name:')
    c.drawString(4.25*inch,9.09*inch,'Bank Account No:')
    c.drawString(4.25*inch,8.91*inch,'IFSC Code:')
    c.drawString(4.25*inch,8.72*inch,'PAN Number:')
    c.drawString(4.25*inch,8.54*inch, 'PF No:')
    c.drawString(4.25*inch,8.36*inch,'PF UAN:')

    c.setFont('LSR',9)
    c.drawString(6.05*inch,9.45*inch,str(employee.pk))
    c.drawString(6.05*inch,9.27*inch, str(bank_detail.bank_name))
    c.drawString(6.05*inch,9.09*inch, str(bank_detail.bank_account_no))
    c.drawString(6.05*inch,8.91*inch, str(bank_detail.ifsc_code))
    c.drawString(6.05*inch,8.72*inch, str(bank_detail.pan_no))
    c.drawString(6.05*inch,8.54*inch, str(bank_detail.pf_no if bank_detail.pf_no != None else '-'))
    c.drawString(6.05*inch,8.36*inch, str(bank_detail.pf_uan if bank_detail.pf_no != None else '-'))

    if extra_line:
        c.setFont('LSB',10)
        c.drawString(0.65*inch,8.1*inch,'Earnings')
        c.setFont('LSR',9)
        c.drawString(0.65*inch,7.85*inch,'Basic')

        if base_data['additional_title'] == None:
            additional_title = "-"
            additional_amount = "-"
        else:
            additional_title = base_data['additional_title']
            additional_amount = base_data['additional_amount']

        if base_data['deduction_title'] == None:
            deduction_title = "-"
            deduction_amount = "-"
        else:
            deduction_title = base_data['deduction_title']
            deduction_amount = base_data['deduction_amount']

        c.drawString(0.65*inch,7.6*inch,additional_title)
        c.drawString(0.65*inch,7.35*inch,'Total Earning:')

        c.setFont('LSB',10)
        c.drawString(2.5*inch,8.1*inch,'Actual')
        c.setFont('LSR',9)
        c.drawRightString(2.85*inch,7.85*inch, str(employee.salary))
        c.drawRightString(2.85*inch,7.6*inch, '-')
        c.drawRightString(2.85*inch,7.35*inch, str(employee.salary))

        c.setFont('LSB',10)
        c.drawString(3.5*inch,8.1*inch,'Earned')
        c.setFont('LSR',9)
        c.drawRightString(3.9*inch,7.85*inch, str(employee.salary-base_data['leave_deduction']))
        c.drawRightString(3.9*inch,7.6*inch, str(additional_amount))
        c.drawRightString(3.9*inch,7.35*inch, str((employee.salary-base_data['leave_deduction'])+base_data['additional_amount']))

        c.setFont('LSB',10)
        c.drawString(4.25*inch,8.1*inch,'Deduction')
        c.setFont('LSR',9)
        c.drawString(4.25*inch,7.85*inch, 'Prof. Tax')
        c.drawString(4.25*inch,7.6*inch, deduction_title)
        c.drawString(4.25*inch,7.35*inch,'Total Deduction:')

        c.setFont('LSB',10)
        c.drawString(7.15*inch,8.1*inch,'Amount')
        c.setFont('LSR',9)
        c.drawRightString(7.6*inch,7.85*inch, '0')
        c.drawRightString(7.6*inch,7.6*inch, str(deduction_amount))
        c.drawRightString(7.6*inch,7.35*inch, str(base_data['deduction_amount']))

        c.drawString(0.65*inch,7.11*inch,'Net Pay For The Month ( Total Earnings - Total Deductions):')
        c.setFont('LSB',10)
        c.drawString(3.8*inch,7.11*inch, str(base_data['total_earn']))
        c.setFont('LSB',10)
        c.drawString(0.65*inch,6.87*inch, "Amount in words :")
        c.setFont('LSRI',9)
        c.drawString(1.8*inch,6.87*inch, base_data['earning_in_words']+" Only.")

        c.setFont('LSB',10)
        c.drawString(0.6*inch,6.6*inch,'**Note')
        c.setFont('LSR',9)
        c.drawString(1*inch,6.6*inch,' : All amounts displayed in this payslip are in')
        c.setFont('LSB',10)
        c.drawString(3.3*inch,6.6*inch,'INR.')
        c.setFont('LSR',9)
        c.drawString(0.6*inch,6.4*inch,'*This is computer generated statement, does not require signature.')
        c.save()
    else:
        c.setFont('LSB',10)
        c.drawString(0.65*inch,8.1*inch,'Earnings')
        c.setFont('LSR',9)
        c.drawString(0.65*inch,7.85*inch,'Basic')
        c.drawString(0.65*inch,7.6*inch,'Total Earning:')

        c.setFont('LSB',10)
        c.drawString(2.5*inch,8.1*inch,'Actual')
        c.setFont('LSR',9)
        c.drawString(2.55*inch,7.85*inch, str(int(employee.salary)))
        c.drawString(2.55*inch,7.6*inch, str(int(employee.salary)))

        c.setFont('LSB',10)
        c.drawString(3.5*inch,8.1*inch,'Earned')
        c.setFont('LSR',9)
        c.drawString(3.55*inch,7.85*inch, str(base_data['total_earn']))
        c.drawString(3.55*inch,7.6*inch, str(base_data['total_earn']))

        c.setFont('LSB',10)
        c.drawString(4.25*inch,8.1*inch,'Deduction')
        c.setFont('LSR',9)
        c.drawString(4.25*inch,7.85*inch,'Prof. Tax')
        c.drawString(4.25*inch,7.6*inch,'Total Deduction:')

        c.setFont('LSB',10)
        c.drawString(7.15*inch,8.1*inch,'Amount')
        c.setFont('LSR',9)
        c.drawString(7.25*inch,7.85*inch, '0')
        c.drawString(7.25*inch,7.6*inch, '0')

        c.drawString(0.65*inch,7.3*inch,'Net Pay For The Month ( Total Earnings - Total Deductions):')
        c.setFont('LSB',10)
        c.drawString(3.8*inch,7.3*inch, str(base_data['total_earn']))
        c.setFont('LSB',10)
        c.drawString(0.65*inch,7.05*inch, "Amount in words :")
        c.setFont('LSRI',9)
        c.drawString(1.8*inch,7.05*inch, base_data['earning_in_words']+" Only.")

        c.setFont('LSB',10)
        c.drawString(0.6*inch,6.8*inch,'**Note')
        c.setFont('LSR',9)
        c.drawString(1*inch,6.8*inch,' : All amounts displayed in this payslip are in')
        c.setFont('LSB',10)
        c.drawString(3.3*inch,6.8*inch,'INR.')
        c.setFont('LSR',9)
        c.drawString(0.6*inch,6.6*inch,'*This is computer generated statement, does not require signature.')
        c.save()

    fs = FileSystemStorage('')
    file = FileResponse(fs.open(base_data['filepath'], 'rb'))
    if kwargs.get("send_email"):
        emailTo = []
        for admin_email in settings.SUPER_ADMIN_EMAILS:
            emailTo.append(admin_email)
        Mailer(
            subject=f"{'Your Payslip for month'}{base_data['salary_month_name']}",
            message="Here is your payslip",
            email_to = emailTo
        ).send(base_data['filepath'])
    return file 

    #----------------------------- End Generate Payslip pdf -------------------------------------

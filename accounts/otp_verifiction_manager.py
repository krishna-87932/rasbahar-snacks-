

from django.core.mail import send_mail

def send_gmail_otp(otp_subject:str,consumer:str, user_otp:str):
    send_mail(
        subject=f'OTP verification for {otp_subject}',
        message=f'Your verification otp is: {user_otp}',
        from_email='matrix202440@gmail.com',
        recipient_list=[consumer],
        fail_silently=False,
    )
    return "OTP sent Successfuly"
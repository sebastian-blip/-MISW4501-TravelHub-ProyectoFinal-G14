import resend
from .template_html import html_template


def send_email_notification(email, message):

    message = html_template.replace("{{mensaje}}", message)
    params: resend.Emails.SendParams = {
        "from": "Acme <travelhub-notification@notification.travel-hub.tech>",
        "to": [email],
        "subject": 'notification',
        "html": message,
    }

    email = resend.Emails.send(params)
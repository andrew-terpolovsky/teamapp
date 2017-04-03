from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.utils.html import strip_tags
from django.template import RequestContext
from django.template import Context


def send_email(subject, email, template, context, tags=list(),
               metadata=list(), request=None, reply_to=settings.DEFAULT_FROM_EMAIL, send_at=None):
    """
    Renders template blocks and sends an email.

    :param subject:
    :param email:
    :param template:
    :param context:
    :param tags:
    :param metadata:
    :param request:
    :param reply_to:
    :param send_at:
    :return:
    """
    context.update({
        'STATIC_URL': settings.STATIC_URL,
        'domain': settings.HOSTNAME
    })
    if request:
        context = RequestContext(request, context)

    template = get_template(template)
    html_content = template.render(Context(context))

    text_content = strip_tags(html_content)
    kwargs = dict(
        subject=subject,
        body=text_content.strip(),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email],
        reply_to=[reply_to],
    )
    message = EmailMultiAlternatives(**kwargs)
    message.attach_alternative(html_content, 'text/html')

    # Email tags
    message.tags = tags
    # Email metadata
    message.metadata = metadata

    # datetime.now(utc) + timedelta(hours=1)
    if send_at:
        message.send_at = send_at

    message.async = settings.EMAIL_ASYNC
    message.track_clicks = True
    message.track_opens = True

    message.send(fail_silently=True)

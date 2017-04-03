"""
DoIQApp URL Configuration
"""
from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic import TemplateView

urlpatterns = [
    url(r'^admin-panel/', admin.site.urls),
    url(r'^api/', include('doiq.accounts.urls', namespace='accounts')),
    url(r'^api/', include('doiq.tasks.urls', namespace='tasks')),
    url(r'^api/', include('doiq.core.urls', namespace='core')),
    url(r'^api/', include('doiq.filemanager.urls', namespace='filemanager')),
    url(r'^api/', include('doiq.channel.urls', namespace='channel')),
    url(r'^api/', include('doiq.chat.urls', namespace='chat')),

    url(r'(^.*/$|^$)', TemplateView.as_view(template_name='base.html'), name="angular")
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

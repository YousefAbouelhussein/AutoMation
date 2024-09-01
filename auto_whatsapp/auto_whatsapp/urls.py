from django.contrib import admin
from django.urls import path

from scraper.views import send_messages, send_messages_view, interested_responses

urlpatterns = [
    path('admin/', admin.site.urls),
    path('send_messages/', send_messages, name='send_messages'),
    path('send_messages_page/', send_messages_view, name='send_messages_page'),
    path('interested_responses/', interested_responses, name='interested_responses'),
]


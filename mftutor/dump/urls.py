from django.conf.urls import patterns, url
from mftutor.tutor.auth import tutorbest_required
from mftutor.dump.views import TutorDumpView, RusDumpView, EventsDumpView

urlpatterns = patterns('',
    url(r'^tutor/$', tutorbest_required(TutorDumpView.as_view()), name='dump_tutor'),
    url(r'^rus/$', tutorbest_required(RusDumpView.as_view()), name='dump_rus'),
    url(r'^events/$', tutorbest_required(EventsDumpView.as_view()), name='dump_events'),
)

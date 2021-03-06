# encoding: utf-8

import re
import textwrap

import django
from django.views.generic import ListView, DetailView, FormView
from django.views.generic.base import TemplateResponseMixin
from django.http import HttpResponseRedirect
import django.core.urlresolvers
import django.core.mail
from django.core.mail import EmailMessage

from mftutor.tutormail.models import Email
from mftutor.tutormail.forms import EmailForm
from mftutor.tutor.models import TutorProfile
from mftutor.settings import TUTORMAIL_YEAR


email_backend_type = 'django.core.mail.backends.smtp.EmailBackend'


class EmailFormView(FormView):
    template_name = 'email_form.html'
    form_class = EmailForm

    def get_initial(self):
        initial_data = super(EmailFormView, self).get_initial()
        name, email = self.get_sender()
        initial_data['sender_name'] = name
        initial_data['sender_email'] = email
        return initial_data

    def get_success_url(self):
        return django.core.urlresolvers.reverse('email_form')

    def get_context_data(self, **kwargs):
        data = super(EmailFormView, self).get_context_data(**kwargs)
        data['recipients'] = self.get_recipients()
        return data

    def get_sender(self):
        profile = self.request.user.tutorprofile
        return (profile.name, 'best')

    def perform_wrapping(self, text, wrapping):
        text = text.replace(u'\r', u'')

        if wrapping == u'paragraphs':
            paragraphs = re.findall(r'(.*?)(\n\n+|\n*$)', text, re.S)
            text = u''.join(
                u'%s%s'
                % ('\n'.join(textwrap.wrap(par, 79)),
                   sep)
                for par, sep in paragraphs)
        elif wrapping == 'lines':
            text = u''.join(
                u'%s\n' % u'\n'.join(textwrap.wrap(line, 79))
                for line in text.splitlines())

        return text

    def post(self, request):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if request.POST.get('wrap'):
            wrapping = form['wrapping'].value()
            text = self.perform_wrapping(form['text'].value(), wrapping)
            text2 = self.perform_wrapping(text, wrapping)

            kwargs = self.get_form_kwargs()
            kwargs['data'] = kwargs['data'].copy()
            kwargs['data']['text'] = text
            form = form_class(**kwargs)

            if text != text2:
                raise ValueError(u'Line wrapping failed (no fixpoint)')

            return self.render_to_response(self.get_context_data(form=form))
        else:
            return super(EmailFormView, self).post(request)

    def get_recipients(self):
        profiles = TutorProfile.objects.filter(
            tutor__year__exact=TUTORMAIL_YEAR,
            tutor__early_termination__isnull=True,
            tutor__groups__handle='alle')

        return sorted([profile.email for profile in profiles])

    def form_valid(self, form):
        data = form.cleaned_data
        subject = data['subject']
        text = self.perform_wrapping(data['text'], data['wrapping'])
        from_email = '"%s" <%s@matfystutor.dk>' % (
            data['sender_name'], data['sender_email'])

        recipients = self.get_recipients()

        if data['only_me']:
            text += '\n' + repr(recipients)
            recipients = [self.request.user.tutorprofile.email]

        messages = []
        for recipient in recipients:
            msg = EmailMessage(
                subject=subject,
                body=text,
                from_email='webfar@matfystutor.dk',
                bcc=[recipient],
                headers={'From': from_email, 'X-Tutor-Recipient': recipient},
            )
            messages.append(msg)

        email_backend = django.core.mail.get_connection(
            backend=email_backend_type)

        # email_backend = django.core.mail.get_connection(
        #     backend='django.core.mail.backends.filebased.EmailBackend',
        #     file_path='./mails')

        email_backend.send_messages(messages)

        return HttpResponseRedirect(self.get_success_url())


class EmailListView(ListView, TemplateResponseMixin):
    model = Email
    template_name = 'email_list.html'

    def get_queryset(self):
        return Email.objects.filter(archive=False)


class EmailDetailView(DetailView, TemplateResponseMixin):
    model = Email
    template_name = 'email_detail.html'

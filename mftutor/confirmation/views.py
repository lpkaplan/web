# vim: set fileencoding=utf8:
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect, render_to_response
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django import forms
from django.views.generic import UpdateView, TemplateView, View
from django.views.generic.edit import FormMixin

from ..settings import YEAR
from ..tutor.auth import user_tutor_data, NotTutor, tutorbest_required_error, tutor_required_error
from ..tutor.models import Tutor
from .models import Confirmation
from .forms import OwnConfirmationForm, EditNoteForm

class OwnConfirmationView(UpdateView):
    form_class = OwnConfirmationForm

    def dispatch(self, request, *args, **kwargs):
        try:
            td = user_tutor_data(request.user)
        except NotTutor:
            return tutor_required_error(request)

        return super(OwnConfirmationView, self).dispatch(request, *args, **kwargs)

    def get_object(self):
        td = user_tutor_data(self.request.user)
        try:
            return Confirmation.objects.get(tutor=td.tutor)
        except Confirmation.DoesNotExist:
            return Confirmation(tutor=td.tutor, study=td.profile.study)

    def form_valid(self, form):
        td = user_tutor_data(self.request.user)

        if self.object.tutor.pk != td.tutor.pk:
            errors = form._errors.setdefault(forms.forms.NON_FIELD_ERRORS, forms.util.ErrorList())
            errors.append(u"Ugyldig tutor")
            return self.form_invalid(form)

        self.object = form.save(commit=False)
        self.object.save()

        return self.render_to_response(self.get_context_data(object=self.object, form=form, success=True))

class ConfirmationListView(TemplateView):
    def get_context_data(self, **kwargs):
        context = super(ConfirmationListView, self).get_context_data(**kwargs)
        context['confirmation_list'] = sorted(list(Confirmation.objects.all())
                + list(Confirmation(tutor=t) for t in Tutor.members.filter(confirmation__isnull=True)),
                key=lambda c: c.tutor.profile.get_full_name())
        return context

class ConfirmationTableView(ConfirmationListView):
    template_name = 'confirmation/confirmation_table.html'

class ConfirmationCardView(ConfirmationListView):
    template_name = 'confirmation/confirmation_card.html'

class EditNoteView(View, FormMixin):
    model = Confirmation
    form_class = EditNoteForm

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse('confirmation_table')

    def form_valid(self, form):
        try:
            c = Confirmation.objects.get(tutor__pk__exact=form.cleaned_data['tutor'])
        except Confirmation.DoesNotExist:
            c = Confirmation(tutor=Tutor.objects.get(pk__exact=form.cleaned_data['tutor']))
        c.internal_notes = form.cleaned_data['internal_notes']
        c.save()
        return super(EditNoteView, self).form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        try:
            td = user_tutor_data(request.user)
        except NotTutor:
            return tutorbest_required_error(request)
        if not td.tutor.is_tutorbest():
            return tutorbest_required_error(request)

        return super(EditNoteView, self).dispatch(request, *args, **kwargs)


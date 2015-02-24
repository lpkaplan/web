# vim: set fileencoding=utf8:
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render, redirect, render_to_response
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.views.generic import View

#from ..settings import YEAR
from mftutor.tutor.models import Rus
from mftutor.events.models import EventParticipant


class DumpView(View):
    @staticmethod
    def access_field(o, field):
        parts = field.split('__')
        for p in parts:
            o = getattr(o, p)
        return o

    def usage(self, s=None):
        return HttpResponseBadRequest(
            ("%s\n\n" % s if s else '') +
            'Available fields:\n' +
            ', '.join(self.available_fields.keys()) +
            '\n\n' +
            'Use display_fields=f1,f2 to set tab-separated output columns.\n' +
            'Use order_by=f1,f2 to set the output order.\n',
            'text/plain; charset=utf8')

    def get(self, request):
        model = self.model
        available_fields = self.available_fields
        params = dict(request.GET.items())
        try:
            display_fields = params.pop('display_fields').split(',')
        except KeyError as e:
            return self.usage('Missing param display_fields')
        available_display_fields = set(available_fields.keys())
        available_display_fields.add('n')
        if any(f not in available_display_fields for f in display_fields):
            return self.usage('Invalid display_fields')

        order_by = params.pop('order_by', None)
        download = params.pop('download', None)

        filter_kwargs = {}
        for k, v in params.items():
            try:
                filter_kwargs[available_fields[k]] = v
            except KeyError:
                return self.usage('Unknown key %s' % (k,))

        objects = model.objects.filter(**filter_kwargs)
        if order_by:
            try:
                args = [
                    available_fields[k]
                    for k in order_by.split(',')
                ]
            except KeyError:
                return self.usage('Unknown key in order_by')
            objects = objects.order_by(*args)

        rows = [
            [i+1 if k == 'n' else self.access_field(o, available_fields[k])
             for k in display_fields]
            for i, o in enumerate(objects)
        ]
        s = ''.join('%s\n' % '\t'.join(map(unicode, r)) for r in rows)
        response = HttpResponse(s)
        if download is not None:
            response['Content-Disposition'] = 'attachment; filename="dump.csv"'
            response['Content-Type'] = 'text/csv; charset=utf-8'
        else:
            response['Content-Type'] = 'text/plain; charset=utf-8'
        return response


class RusDumpView(DumpView):
    model = Rus
    available_fields = {
        'year': 'year',
        'rusclass': 'rusclass',
        'name': 'profile__name',
        'phone': 'profile__phone',
        'email': 'profile__email',
        'studentnumber': 'profile__studentnumber',
    }


class EventsDumpView(DumpView):
    model = EventParticipant
    available_fields = {
        'event': 'event__pk',
        'name': 'tutor__profile__name',
        'status': 'status',
        'notes': 'notes',
    }

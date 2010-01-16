from datetime import datetime
from django.views.generic import simple, date_based, list_detail
from django.template import RequestContext
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from anthill.events.models import Event, Attendance
from anthill.events.forms import EventForm, SearchForm, AttendForm

def search(request):
    """
        Display search form/results for events (using distance-based search).

        Template: events/search.html

        Context:
            form           - ``anthill.events.forms.SearchForm``
            event_list     - events in the near future
            searched       - True/False based on if a search was done
            search_results - list of results (may be empty)
    """
    upcoming_events = Event.objects.future().select_related()[0:5]
    if request.GET:
        form = SearchForm(request.GET)
        form.is_valid()
        name = form.cleaned_data['name']
        location = form.cleaned_data['location']
        location_range = form.cleaned_data['location_range']

        # only events that haven't happened
        events = Event.objects.future().select_related()
        if name:
            events = events.filter(title__icontains=name)
        if location:
            events = events.search_by_distance(location, location_range)
        context = {'form': form, 'searched': True, 'search_results': events,
                   'event_list': upcoming_events}
    else:
        context = {'form': SearchForm(), 'event_list': upcoming_events}

    return render_to_response('events/search.html', context,
                              context_instance=RequestContext(request))

def event_detail(request, event_id):
    """
        Detail page for individual events, displays information / allows RSVP.

        Template: events/event_detail.html

        Context:
            event - the ``Event`` object
            form  - ``anthill.events.forms.AttendForm`` instance
            finished - boolean flag indicating if event is in the past
    """
    event = get_object_or_404(Event, pk=event_id)
    now = datetime.now()
    if event.end_date:
        finished = event.end_date < now
    else:
        finished = event.start_date < now

    if not finished and request.method == 'POST' and request.user.is_authenticated():
        form = AttendForm(request.POST)
        if form.is_valid():
            Attendance.objects.create(user=request.user, event_id=event_id,
                                      guests=form.cleaned_data['guests'],
                                      message=form.cleaned_data['message'])
    else:
        form = AttendForm()
    return render_to_response('events/event_detail.html',
                              {'event':event, 'form':form, 'finished':finished},
                              context_instance=RequestContext(request))

@login_required
def edit_event(request, event_id):
    """
        Edit an already existing event.

        Requires editor to be the creator or staff.

        Template: events/edit_event.html

        Context:
            form  - ``EventForm`` with the editable details
            event - ``Event`` with current details of event being edited
    """
    event = get_object_or_404(Event, pk=event_id)
    if event.creator != request.user and not request.user.is_staff:
        return HttpResponseForbidden('Only the creator of an event may edit it.')

    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            return redirect(event.get_absolute_url())
    else:
        form = EventForm(instance=event)

    return render_to_response('events/edit_event.html',
                              {'form':form, 'event':event},
                             context_instance=RequestContext(request))

@login_required
def new_event(request):
    """
        Create a new event.

        Template:
            events/edit_event.html

        Context:
            form - ``EventForm`` for creating a new event
    """
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.creator = request.user
            event.save()
            form.save_m2m()
            return redirect(event.get_absolute_url())
    else:
        form = EventForm()

    return render_to_response('events/edit_event.html',
                              {'form':form},
                             context_instance=RequestContext(request))

def archive(request):
    """
        Listing of all *future* events.

        Template:
            events/event_list.html

        Context:
            event_list
            paginator
            page_obj
            is_paginated
    """
    return list_detail.object_list(request,
                                   queryset=Event.objects.future().select_related().all(),
                                   template_object_name='event')

def archive_year(request, year):
    """
        Listing of months that contain events in a given year.

        Template:
            events/event_archive_year.html

        Context:
            object_list
            date_list
            year
    """
    return date_based.archive_year(request, year=year,
                                   queryset=Event.objects.all(),
                                   allow_future=True,
                                   date_field='start_date',)

def archive_month(request, year, month):
    """
        Listing of all events in a given month.

        Template:
            events/event_archive_month.html

        Context:
            event_list
            previous_month
            next_month
            month
    """
    return date_based.archive_month(request, year=year, month=month,
                                    queryset=Event.objects.all(),
                                    date_field='start_date', month_format='%m',
                                    allow_future=True,
                                    template_object_name='event')

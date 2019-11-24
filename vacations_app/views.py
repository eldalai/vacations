# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from io import BytesIO
from datetime import timedelta

from bootstrap_datepicker_plus import DatePickerInput
from django.contrib.auth.mixins import PermissionRequiredMixin
from django import forms
from django.http import HttpResponse
from django.template.loader import get_template
from django.urls import reverse_lazy
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import (
    CreateView,
    DeleteView,
    FormView,
    UpdateView,
)
from xhtml2pdf import pisa

from vacations_app import (
    CAN_VIEW_OTHER_VACATIONS,
    CAN_VIEW_TEAM_MEMBERS_VACATIONS,
)
from vacations_app.models import (
    AssignedVacations,
    Employee,
    Holiday,
    Vacation,
    validate_from_date,
)


class HomeView(ListView):
    template_name = 'vacations_app/index.html'

    def get_queryset(self):
        if self.request.user.is_authenticated():
            return Vacation.objects.filter(employee=self.request.user)
        else:
            return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['staff_user'] = self.request.user.has_perm('vacations_app.can_view_other_vacations')
        context['manager_user'] = self.request.user.has_perm('vacations_app.can_view_team_members_vacations')
        return context


class VacationRequestForm(forms.Form):
    from_date = forms.DateField(
        widget=DatePickerInput(),
        validators=[validate_from_date],
    )
    year_days_quantity = forms.ChoiceField()


class VacationRequest(FormView):
    template_name = 'vacations_app/vacation_request.html'
    form_class = VacationRequestForm
    success_url = reverse_lazy('home')

    def get_form(self):
        form = super().get_form()

        available_vacations = self.request.user.get_available_vacations()
        days_quantity_choices = []
        self.other_available_vacation = []
        first = True
        for available_vacation_year, available_vacation_days in sorted(available_vacations.items()):
            if first:
                first = False
                while available_vacation_days > 0:
                    key = 'Applicable worked year: {} Days quantity: {}'.format(
                        available_vacation_year,
                        available_vacation_days,
                    )
                    value = '{}-{}'.format(
                        available_vacation_year,
                        available_vacation_days,
                    )
                    days_quantity_choices.append(
                        (value, key, )
                    )
                    available_vacation_days -= 7
            else:
                key = 'Applicable worked year: {} Days quantity: {}'.format(
                    available_vacation_year,
                    available_vacation_days,
                )
                self.other_available_vacation.append(key)
        form.fields['year_days_quantity'] = forms.ChoiceField(
            choices=days_quantity_choices,
        )
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['other_available_vacation'] = self.other_available_vacation
        return context

    def form_valid(self, form):
        applicable_worked_year, days_quantity = form.cleaned_data['year_days_quantity'].split('-')
        from_date = form.cleaned_data['from_date']
        Vacation.objects.create(
            from_date=from_date,
            days_quantity=int(days_quantity),
            employee=self.request.user,
            to_date=from_date + timedelta(days=int(days_quantity) - 1),
            applicable_worked_year=int(applicable_worked_year),
        )
        return super().form_valid(form)


class AdminVacationRequest(CreateView):
    model = Vacation
    success_url = reverse_lazy('home')
    template_name = 'vacations_app/admin_vacation_request.html'
    fields = ['employee', 'from_date', 'days_quantity', 'applicable_worked_year']

    def get_form(self):
        form = super().get_form()
        form.fields['from_date'] = forms.DateField(
            widget=DatePickerInput(),
        )
        form.fields['applicable_worked_year'] = forms.ChoiceField(
            choices=(
                (2016, 2016, ),
                (2017, 2017, ),
                (2018, 2018, ),
                (2019, 2019, ),
            )
        )
        return form

    def form_valid(self, form):
        days = form.instance.days_quantity
        form.instance.to_date = form.instance.from_date + timedelta(days=days - 1)
        return super().form_valid(form)


class VacationList(PermissionRequiredMixin, ListView):
    template_name = 'vacations_app/vacation-list.html'
    permission_required = CAN_VIEW_OTHER_VACATIONS
    model = Vacation


class TeamVacationsList(PermissionRequiredMixin, ListView):
    template_name = 'vacations_app/team-vacations-list.html'
    permission_required = CAN_VIEW_TEAM_MEMBERS_VACATIONS

    def get_queryset(self):
        managed_teams = self.request.user.managed_teams.all()
        all_vacations = Vacation.objects.filter(employee__team__in=managed_teams)
        vacations_by_team = {
            team.name: all_vacations.filter(employee__team=team)
            for team in managed_teams
        }
        return vacations_by_team

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['teams'] = [team.name for team in self.request.user.managed_teams.all()]
        return context


class VacationPrintView(DetailView):
    template_name = 'vacations_app/vacation_print_form.html'
    model = Vacation

    def render_to_response(self, context, **response_kwargs):
        pdf = render_to_pdf(self.template_name, context)
        return HttpResponse(pdf, content_type='application/pdf')


def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    return HttpResponse(result.getvalue(), content_type='application/pdf') if not pdf.err else None


class HolidayList(PermissionRequiredMixin, ListView):
    template_name = 'vacations_app/holiday-list.html'
    permission_required = CAN_VIEW_OTHER_VACATIONS
    model = Holiday


class HolidayCreateView(PermissionRequiredMixin, CreateView):
    permission_required = CAN_VIEW_OTHER_VACATIONS
    model = Holiday
    fields = '__all__'
    success_url = reverse_lazy('holidays-list')

    def get_form(self):
        form = super().get_form()
        form.fields['date'] = forms.DateField(
            widget=DatePickerInput(),
        )
        return form


class HolidayDeleteView(PermissionRequiredMixin, DeleteView):
    permission_required = CAN_VIEW_OTHER_VACATIONS
    model = Holiday
    success_url = reverse_lazy('holidays-list')


class HolidayUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = CAN_VIEW_OTHER_VACATIONS
    model = Holiday
    fields = '__all__'
    success_url = reverse_lazy('holidays-list')

    def get_form(self):
        form = super().get_form()
        form.fields['date'] = forms.DateField(
            widget=DatePickerInput(),
        )
        return form


class AssignedVacationsList(PermissionRequiredMixin, ListView):
    permission_required = CAN_VIEW_OTHER_VACATIONS
    model = AssignedVacations


class AssignedVacationCreateView(PermissionRequiredMixin, CreateView):
    permission_required = CAN_VIEW_OTHER_VACATIONS
    model = AssignedVacations
    fields = '__all__'
    success_url = reverse_lazy('assigned-vacations-list')


class AssignedVacationUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = CAN_VIEW_OTHER_VACATIONS
    model = AssignedVacations
    fields = '__all__'
    success_url = reverse_lazy('assigned-vacations-list')


class AssignedVacationDeleteView(PermissionRequiredMixin, DeleteView):
    permission_required = CAN_VIEW_OTHER_VACATIONS
    model = AssignedVacations
    success_url = reverse_lazy('assigned-vacations-list')


class EmployeeList(PermissionRequiredMixin, ListView):
    permission_required = CAN_VIEW_OTHER_VACATIONS

    def get_queryset(self):
        return Employee.objects.all().order_by('email')


class EmployeeUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = CAN_VIEW_OTHER_VACATIONS
    model = Employee
    fields = [
        'first_name', 'last_name',
        'is_staff', 'job_start_date', 'initial_annual_vacations_days', 'team',
    ]
    success_url = reverse_lazy('employees-list')

    def get_form(self):
        form = super().get_form()
        form.fields['job_start_date'] = forms.DateField(
            widget=DatePickerInput(),
        )
        return form


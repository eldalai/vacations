"""vacations URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from .views import (
    HolidayCreateView,
    HolidayUpdateView,
    HolidayDeleteView,
    HolidayList,
    HomeView,
    TeamVacationsList,
    AdminVacationRequest,
    VacationList,
    VacationPrintView,
    VacationRequest,
)


urlpatterns = [
    url(r'^$', HomeView.as_view(), name='home'),
    url(r'^vacation/request$', VacationRequest.as_view(), name='vacation-request'),
    url(r'^vacation/admin-request$', AdminVacationRequest.as_view(), name='vacation-admin-request'),
    url(r'^vacations$', VacationList.as_view(), name='vacations-list'),
    url(r'^vacations/team$', TeamVacationsList.as_view(), name='vacations-team'),
    url(r'^holidays$', HolidayList.as_view(), name='holidays-list'),
    url(r'^holidays/create$', HolidayCreateView.as_view(), name='holidays-create'),
    url(r'^holidays/update/(?P<pk>[0-9]+)/$', HolidayUpdateView.as_view(), name='holidays-update'),
    url(r'^holidays/delete/(?P<pk>[0-9]+)/$', HolidayDeleteView.as_view(), name='holidays-delete'),
    url(r'^print/(?P<pk>[0-9]+)/$', VacationPrintView.as_view(), name='print'),
]

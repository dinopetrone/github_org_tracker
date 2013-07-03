import requests
import json
from django.views.generic import View
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import OrgForm
from .api_services import GithubService, github_authorize, get_github_auth_url
import logging


logger = logging.getLogger(__name__)


class IndexView(View):
    def get(self, request):
        form = OrgForm()
        context = {
                'form':form,
            }

        code = request.GET.get('code',False)
        access_token = request.session.get('access_token',False)
        organization = request.session.get('organization',False)
        days = request.session.get('days',False)



        if access_token and organization and days:
            logger.debug('vars already set to %s, %s, %s', access_token, organization, days)
            try:
                gh = GithubService(access_token, organization, days)
            except:
                request.session.flush()
                return redirect(request.path)
            context['access_token'] = access_token
            context['organization'] = organization
            context['days'] = days
            context['users'] = gh.users
            all_days = set()
            for user in gh.users:
                days = gh.users[user]
                for day in days:
                    all_days.add(day)
            context['all_days'] = sorted(all_days)
        elif code:
            github_authorize(request, code)
            return redirect(request.path)
        
        return render(self.request, 'index.html', context)

    def post(self, request):
        form = OrgForm(request.POST)
        if form.is_valid():
            request.session['organization'] = form.cleaned_data['organization']
            request.session['days'] = form.cleaned_data['days']
        
        gh_url = get_github_auth_url(request)
        return redirect(gh_url)
        context = {'form':form}
        return render(self.request, 'index.html', context)

    

    








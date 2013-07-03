import requests
import json
import logging
from django.views.generic import View
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import OrgForm
from .api_services import GithubService, github_authorize, get_github_auth_url



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
                gh = GithubService()
                context.update(gh.user_data(access_token, organization, days))
            except:
                request.session.flush()
                return redirect(request.path)
        elif code:
            request.session['access_token'] = github_authorize(code)
            return redirect(request.path)
        
        return render(self.request, 'index.html', context)

    def post(self, request):
        form = OrgForm(request.POST)
        if form.is_valid():
            request.session['organization'] = form.cleaned_data['organization']
            request.session['days'] = form.cleaned_data['days']
            gh_url = get_github_auth_url(request.build_absolute_uri(request.path))
            return redirect(gh_url)
        
        context = {'form':form}
        return render(self.request, 'index.html', context)

    

    








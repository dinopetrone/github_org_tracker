import os
import requests
import json
from urlparse import urlparse, parse_qs
from django.views.generic import View
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import OrgForm
from .api_services import GithubService, API_ROOT, AUTH_URL,  ACCESS_TOKEN_URL
import logging


logger = logging.getLogger(__name__)

CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')


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
            gh = GithubService(access_token, organization, days)
            context['access_token'] = access_token
            context['organization'] = organization
            context['days'] = days
            context['users'] = json.dumps(gh.users)
            if gh.users:
                return HttpResponse(json.dumps(gh.users), mimetype="application/json")
        elif code:
            self.github_authorize(request, code)
            return redirect(request.path)
        return render(self.request, 'index.html', context)

    def post(self, request):
        form = OrgForm(request.POST)
        if form.is_valid():
            request.session['organization'] = form.cleaned_data['organization']
            request.session['days'] = form.cleaned_data['days']
        
        gh_url = self.get_github_auth_url(request)
        return redirect(gh_url)
        context = {'form':form}
        return render(self.request, 'index.html', context)

    def github_authorize(self, request, code):
        context = {
            'client_id':CLIENT_ID,
            'client_secret':CLIENT_SECRET,
            'code':code,
        }
        resp = requests.post(ACCESS_TOKEN_URL, params=context)
        query = parse_qs(resp.text)
        try:
            request.session['access_token'] = query['access_token'][0]
        except:
            logger.error('uhm...crap :)')
        
        
        

    def get_github_auth_url(self,request):
        context = {
            'redirect_uri':request.build_absolute_uri(request.path),
            'response_type':'code',
            'scope':'repo,private_repo',
            'client_id': CLIENT_ID
        }
        req = requests.Request('GET', AUTH_URL, params=context)
        url = req.prepare().url
        return url

    








import os
import json
import logging
from datetime import datetime
from urlparse import urlparse, parse_qs
import gevent
from gevent import monkey
monkey.patch_all()
from django.core.cache import cache
import requests





logger = logging.getLogger(__name__)

API_ROOT = 'https://api.github.com'
AUTH_URL = 'https://github.com/login/oauth/authorize'
ACCESS_TOKEN_URL = 'https://github.com/login/oauth/access_token'

CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')

class GithubException(Exception):
    pass

class GithubService(object):

    def user_data(self, token, organization, days):
        
        self.token = token
        self.organization = organization
        self.days = days
        self.users = {}
        response = {}
        response['access_token'] = token
        response['organization'] = organization
        response['days'] = days
        
        if cache.get(token):
            self.users = cache.get(token)
        else:
            self.get_private_repos()
            cache.set(token,self.users,6000)
        
        response['all_days'] = self.get_all_days()
        response['users'] = self.users
        return response

    def get_all_days(self):
        all_days = set()
        for user in self.users:
            days = self.users[user]
            map(all_days.add,days)
        return sorted(all_days)


    def get_api_content(self, url, context={}):
        context['access_token'] = self.token
        resp = requests.get(url, params=context)
        print(resp.url)
        return resp


    def get_private_repos(self):
        
        context = {
            'type':'private',
            'per_page': '100'
        }
        api_private_repos_url = '/orgs/{}/repos'.format(self.organization)
        url = API_ROOT + api_private_repos_url
        logger.debug("[organization repos] %s", url)
        repos = self.get_api_content(url, context).json()
        if type(repos) is dict:
            logger.error('[github issues] %s', repos.get('message'))
            raise GithubException(repos.get('message'))
            print(repos.get('message'))
            return
        
        threads = []
        for repo in repos:
            threads.append(gevent.spawn(self.parse_repo, repo))
            #self.parse_repo(repo)
            
        gevent.joinall(threads)    
        
        
    def parse_repo(self, repo):
        url = repo['commits_url'].replace('{/sha}','')
        logger.debug("[commits url] %s", url)
        commits = self.parse_commits_url(url)
        threads = []
        for commit in commits:
            #self.parse_commit(commit)
            threads.append(gevent.spawn(self.parse_commit, commit))
        gevent.joinall(threads)

    def parse_commits_url(self, url):
        commits_resp = self.get_api_content(url)
        commits = commits_resp.json()

        if type(commits) is dict:
            raise StopIteration

        while(1):
            for commit in commits:
                date_str = commit.get('commit',{}).get('author',{}).get('date','')
                date = datetime.strptime(date_str,'%Y-%m-%dT%H:%M:%SZ')
                now = datetime.now()
                diff = now - date
                if diff.days > self.days:
                    raise StopIteration
                yield commit
            try:
                next = commits_resp.links['next']['url']
            except:
                raise StopIteration
            commits_resp = self.get_api_content(next)
            commits = commits_resp.json()

            
            

    def parse_commit(self, commit):
        try:
            author = commit.get('commit',{}).get('author',{}).get('name','')
            date_str = commit.get('commit',{}).get('author',{}).get('date','')
        except:
            logger.error('crap and fans sonnnnnn')
        date = datetime.strptime(date_str,'%Y-%m-%dT%H:%M:%SZ')
        now = datetime.now()
        diff = now - date
        if diff.days > self.days:
            return
        day = date.strftime('%D')
        
        self.users.setdefault(author,{})
        self.users[author].setdefault(day,{'commit_count':0,'changes':0})
        
        lines = self.get_total_chars_changed(commit['url'])
        self.users[author][day]['commit_count'] += 1
        self.users[author][day]['changes'] += lines
        #self.users[author][day]['commits'].append(commit['url'])
        
        
    def get_total_chars_changed(self, url):
        resp = self.get_api_content(url)
        commit = resp.json()
        files = commit['files']
        total = 0
        for f in files:
            total += f['changes']
        return total





def github_authorize(code):
    context = {
        'client_id':CLIENT_ID,
        'client_secret':CLIENT_SECRET,
        'code':code,
    }
    resp = requests.post(ACCESS_TOKEN_URL, params=context)
    query = parse_qs(resp.text)
    try:
        return query['access_token'][0]
    except:
        logger.error('uhm...crap :)')
        raise
    
    
    

def get_github_auth_url(redirect_uri):
    context = {
        'redirect_uri':redirect_uri,
        'response_type':'code',
        'scope':'repo,private_repo',
        'client_id': CLIENT_ID
    }
    req = requests.Request('GET', AUTH_URL, params=context)
    url = req.prepare().url
    return url
from os import path
from subprocess import Popen
from fabric.api import local, cd, lcd, get, env, roles, execute, task, run, \
                       settings, abort, hide
from fabric.colors import yellow


# paths
base_path   = "./project/static"
css_path    = base_path + "/css/"
config_path = css_path + "config.rb"


# sass execs
exec_sass_watch   = "compass watch {} -c {}"
#exec_sass_compile = "compass compile {} --output-style compressed -c {} --force"
exec_sass_compile = "compass compile {} -c {} --trace --force"



@task
def runall():
    local('touch nohup.out')
    local('nohup fab vagrant.css_watch &')
    local('nohup fab vagrant.gunicorn &')
    local('tail -f nohup.out')

@task
@roles('vagrant')
def killall():
    with settings(warn_only=True):
        run("ps ax | grep [r]unserver | awk '{ print $1 }' | xargs sudo kill -9")
        run("ps ax | grep [r]un_gunicorn | awk '{ print $1 }' | xargs sudo kill -9")
        run("ps ax | grep [w]orker | awk '{ print $1 }' | xargs sudo kill -9")
        run("ps ax | grep [c]elerybeat | awk '{ print $1 }' | xargs sudo kill -9")
        run("ps ax | grep [c]ompass | awk '{ print $1 }' | xargs sudo kill -9")
        run("ps ax | grep [s]ass | awk '{ print $1 }' | xargs sudo kill -9")

@task
@roles('vagrant')
def runserver():
    with settings(warn_only=True):
        # FOR SOME REASON IF THE PROCESS WASN'T ENDED CORRECTLY, THIS WILL KILL IT
        run("ps ax | grep [r]unserver | awk '{ print $1 }' | xargs kill -9")
    with cd("/var/www"):
        run('python ./manage.py runserver [::]:8000')

@task
@roles('vagrant')
def gunicorn():
    with settings(warn_only=True):
        # FOR SOME REASON IF THE PROCESS WASN'T ENDED CORRECTLY, THIS WILL KILL IT
        run("ps ax | grep [r]un_gunicorn | awk '{ print $1 }' | xargs kill -9")
    with cd("/var/www"):
        run('python ./manage.py run_gunicorn [::]:8000')

@task
@roles('vagrant')
def celery():
    with settings(warn_only=True):
        # FOR SOME REASON IF THE PROCESS WASN'T ENDED CORRECTLY, THIS WILL KILL IT
        run("ps ax | grep [w]orker | awk '{ print $1 }' | xargs kill -9")
    with cd("/var/www"):
        run('python manage.py celery worker --loglevel=INFO')


@task
@roles('vagrant')
def celerybeat():
    with settings(warn_only=True):
        # FOR SOME REASON IF THE PROCESS WASN'T ENDED CORRECTLY, THIS WILL KILL IT
        run("ps ax | grep [c]elerybeat | awk '{ print $1 }' | xargs kill -9")
    with cd("/var/www"):
        run('python manage.py celerybeat --loglevel=INFO')

@task
@roles('vagrant')
def initdb(load_images=False):
    with cd("/var/www"):
        run('yes no | python manage.py syncdb')
        run('python manage.py migrate')
        run('python manage.py createsuperuser')

    if load_images:
        load_fixture_images()


@task
@roles('vagrant')
def syncdb():
    with cd("/var/www"):
        run('python manage.py syncdb')
        run('python manage.py migrate')

@task
@roles('vagrant')
def resetall():
    """Stop all services, destroy the database, restore it from fixtures, remove all files in uploads directory and download assets."""
    killall()
    local('vagrant provision')
    resetdb(delete_images=True, load_images=True)

@task
@roles('vagrant')
def resetdb(load_images=False, delete_images=False):
    # mysql
    #run("mysql -u vagrant -pvagrant -e 'drop database if exists django'")
    #run('mysql -u vagrant -pvagrant -e "create database django"')

    # postgres
    run('dropdb django')
    run('createdb django')

    if delete_images:
        with cd("/var/www/uploads"):
            run('rm -rf ./*')

    initdb(load_images)

@task
def load_fixture_images():
    uploads_dir = path.abspath(path.join(path.dirname(__file__), '../uploads'))
    with lcd(uploads_dir):
        with settings(warn_only=True):
            local('rm -rf ./*')
        local('curl -sLO https://dl.dropboxusercontent.com/s/zpb8troupk1x2g1/haus_com_assets.tar.bz2')
        local('tar xjvf haus_com_assets.tar.bz2')
        local('rm haus_com_assets.tar.bz2')

@task
@roles('vagrant')
def collectstatic(no_input=False):
    with cd("/var/www"):
        run('python manage.py collectstatic {}'.format('--noinput' if no_input else ''))

@task
@roles('vagrant')
def css_watch(new_config=None):
    with settings(warn_only=True):
        # Killing all sass processes before executing a new one
        run("ps ax | grep [c]ompass | awk '{ print $1 }' | xargs sudo kill -9")
    with cd("/var/www"):
        run(exec_sass_watch.format(base_path, config_path))

@task
@roles('vagrant')
def pipinstall():
    run('/home/vagrant/.venv/bin/pip install --use-mirrors -r /var/www/requirements.txt')

@task
@roles('vagrant')
def freeze():
    run('/home/vagrant/.venv/bin/pip freeze > /var/www/current-requirements.txt')

@task
@roles('vagrant')
def css_compile():
    with cd("/var/www"):
        run(exec_sass_compile.format(base_path, config_path))

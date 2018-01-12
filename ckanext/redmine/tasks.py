import logging
from urlparse import urlparse

import os
import routes

from pylons import config

import ckan
import ckan.plugins.toolkit as toolkit
from ckan.lib.helpers import get_pkg_dict_extra, url_for

from redminelib import Redmine

# ------------- #
# config access #
# ------------- #

def get_redmine_flag():
    return config.get('ckan.redmine.flag', 'redmine_url')


def get_redmine_subject_prefix():
    return config.get('ckan.redmine.subject_prefix', 'New dataset')


def get_redmine_url():
    return config.get('ckan.redmine.url')


def get_redmine_apikey():
    return config.get('ckan.redmine.apikey')


def get_redmine_project():
    return config.get('ckan.redmine.project')

# ----------- #
# entry point #
# ----------- #

def create_ticket_task(package, action, ckan_ini_filepath):
    logger = create_ticket_task.get_logger()
    load_config(ckan_ini_filepath)
    register_translator()
    logger.info("Create ticket for package %s, with action %s" % (package, action))
    return sync_package(package, action)


logger = logging.getLogger(__name__)

def get_logger():
    return logger
create_ticket_task.get_logger = get_logger


def load_config(ckan_ini_filepath):
    import paste.deploy
    config_abs_path = os.path.abspath(ckan_ini_filepath)
    conf = paste.deploy.appconfig('config:' + config_abs_path)
    import ckan
    ckan.config.environment.load_environment(conf.global_conf,
                                             conf.local_conf)

    ## give routes enough information to run url_for
    parsed = urlparse(conf.get('ckan.site_url', 'http://0.0.0.0'))
    request_config = routes.request_config()
    request_config.host = parsed.netloc + parsed.path
    request_config.protocol = parsed.scheme


def register_translator():
    # https://github.com/ckan/ckanext-archiver/blob/master/ckanext/archiver/bin/common.py
    # If not set (in cli access), patch the a translator with a mock, so the
    # _() functions in logic layer don't cause failure.
    from paste.registry import Registry
    from pylons import translator
    from ckan.lib.cli import MockTranslator
    if 'registry' not in globals():
        global registry
        registry = Registry()
        registry.prepare()

    if 'translator_obj' not in globals():
        global translator_obj
        translator_obj = MockTranslator()
        registry.register(translator, translator_obj)


def sync_package(package_id, action, ckan_ini_filepath=None):
    logger.info('sync package')

    # load the package at run of time task (rather than use package state at
    # time of task creation).
    from ckan import model
    context = {'model': model, 'ignore_auth': True, 'session': model.Session,
               'use_cache': False, 'validate': True}

    params = {
        'id': package_id,
    }
    package = toolkit.get_action('package_show')(
        context,
        params,
    )

    if action == 'dataset/create':
        _create_ticket(package)
    elif action == 'dataset/update':
        #_update_package(package)
        pass
    else:
        raise Exception('Unsupported action {0}'.format(action))


def _create_ticket(package):
    redmine = Redmine(get_redmine_url(), key=get_redmine_apikey())
    proj = redmine.project.get(get_redmine_project())

    logger.info("Creating redmine issue")

    url = url_for(controller='package', action='read', id=package['name'], qualified=True)
    issue = redmine.issue.create(
                project_id=proj.identifier,
                subject='{} {}'.format(get_redmine_subject_prefix(), package['title']),
                description='URL: {}'.format(url))

    logger.info("Setting redmine url for package")

    urltemplate = "{}/issues/{}/"
    if get_redmine_url().endswith('/'):
        urltemplate = "{}issues/{}/"

    set_redmine_url(
            package,
            urltemplate.format(get_redmine_url(), issue.id))

    logger.info("Done")

def set_redmine_url(local_package, url):
    """ Set redmine url """
    local_package[get_redmine_flag()] = url
    _update_package(local_package)

def _update_package(package):
    site_user = ckan.logic.get_action('get_site_user')({
            'model': ckan.model,
            'ignore_auth': True},
            {}
      )

    context = {'model': ckan.model, 'ignore_auth': True, 'session': ckan.model.Session,
               'use_cache': False, 'validate': True, 'user': site_user['name']}
    toolkit.get_action('package_update')(context, package)



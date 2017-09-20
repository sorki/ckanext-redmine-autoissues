import logging
from urlparse import urlparse
import ckanapi
import os
import routes

from pylons import config

import ckan.plugins.toolkit as toolkit
from ckan.lib.celery_app import celery
from ckan.lib.helpers import get_pkg_dict_extra
from ckanext.redmine.plugin import (
    get_redmine_flag,
    get_redmine_url,
    get_redmine_apikey,
    get_redmine_project
)

logger = logging.getLogger(__name__)


@celery.task(name='redmine.create_ticket')
def create_ticket_task(package, action, ckan_ini_filepath):
    logger = sync_package_task.get_logger()
    load_config(ckan_ini_filepath)
    register_translator()
    logger.info("Create ticket for package %s, with action %s" % (package, action))
    return sync_package(package, action)


# TODO: why mp this
# enable celery logging for when you run nosetests -s
log = logging.getLogger('ckanext.redmine.tasks')


def get_logger():
    return log
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
    if 'registery' not in globals():
        global registry
        registry = Registry()
        registry.prepare()

    if 'translator_obj' not in globals():
        global translator_obj
        translator_obj = MockTranslator()
        registry.register(translator, translator_obj)


def sync_package(package_id, action, ckan_ini_filepath=None):
    logger.info('sync package {0}'.format(package_id))

    # load the package at run of time task (rather than use package state at
    # time of task creation).
    from ckan import model
    context = {'model': model, 'ignore_auth': True, 'session': model.Session,
               'use_cache': False, 'validate': False}

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
    redmine.issue.create(
            project_id=proj.identifier,
            subject='New dataset {}'.format(package['title'])
            description='URL: {}'.format(package['id']))

    logger.info("Setting redmine url for package {}".format(package))

    set_redmine_url(
            package,
            "{}/issues/{}/".format(get_redmine_url(), issue.id))

    logger.info("Done")


def set_redmine_url(local_package, url):
    """ Set the remote package id on the local package """
    extras = local_package['extras']
    extras_dict = dict([(o['key'], o['value']) for o in extras])
    extras_dict.update({get_redmine_flag(): url})
    extras = [{'key': k, 'value': v} for (k, v) in extras_dict.iteritems()]
    local_package['extras'] = extras
    _update_package_extras(local_package)


def _update_package_extras(package):
    from ckan import model
    from ckan.lib.dictization.model_save import package_extras_save

    package_id = package['id']
    package_obj = model.Package.get(package_id)
    if not package:
        raise Exception('No Package with ID %s found:s' % package_id)

    extra_dicts = package.get("extras")
    context_ = {'model': model, 'session': model.Session}
    model.repo.new_revision()
    package_extras_save(extra_dicts, package_obj, context_)
    model.Session.commit()
    model.Session.flush()

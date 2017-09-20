import os

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.lib.celery_app import celery

from pylons import config
import ckan.model as model
from ckan.model.domain_object import DomainObjectOperation

import uuid


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


def redmine_dataset(package_id, topic):
    ckan_ini_filepath = os.path.abspath(config['__file__'])
    celery.send_task(
        'redmine.create_ticket',
        args=[package_id, topic, ckan_ini_filepath],
        task_id='{}-{}'.format(str(uuid.uuid4()), package_id)
    )


class RedminePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IDomainObjectModification, inherit=True)

    # IConfigurer

    ## Based on ckanext-webhooks plugin
    # IDomainObjectNotification & IResourceURLChange
    def notify(self, entity, operation=None):
        if not operation:
            # This happens on IResourceURLChange
            return

        if isinstance(entity, model.Package):
            self._redmine_dataset(entity, operation)

    def update_config(self, config_):
        pass

    def _redmine_dataset(self, dataset, operation):
        topic = self._get_topic('dataset', operation)

        if topic is not None:
            redmine_dataset(dataset.id, topic)

    def _get_topic(self, prefix, operation):
        topics = {
            DomainObjectOperation.new: 'create',
            DomainObjectOperation.changed: 'update',
        }

        topic = topics.get(operation, None)

        if topic is not None:
            return '{0}/{1}'.format(prefix, topic)

        return None

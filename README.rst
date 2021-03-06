==========================
ckanext-redmine-autoissues
==========================

CKAN plugin to automatically create redmine issues when new dataset appears.

Based on `ckanext-syndicate <https://github.com/aptivate/ckanext-syndicate>`_.

------------
Requirements
------------

* Requires ``python-redmine``
* To work over SSL, requires ``pyOpenSSL``, ``ndg-httpsclient`` and ``pyasn1``

------------
Installation
------------

To install ckanext-redmine:

1. Activate your CKAN virtual environment, for example::

    . /usr/lib/ckan/default/bin/activate

2. Install the ckanext-redmine-autoissues Python package into your virtual environment::

    pip install ckanext-redmine-autoissues

3. Add ``redmine`` to the ``ckan.plugins`` setting in your CKAN
   config file (by default the config file is located at
   ``/etc/ckan/default/production.ini``).

4. Restart CKAN. For example if you've deployed CKAN with Apache::

    sudo service apache2 reload

5. You will also need to set up RQ job runner, to test it you can run::

   paster jobs worker default

---------------
Config Settings
---------------

::

    # The URL of the Redmine site
    ckan.redmine.url = https://redmine.example.org/

    # Redmine API key
    ckan.redmine.apikey = CHANGE_THIS_OR_IT_WONT_WORK

    # Redmine project
    ckan.redmine.project = my_project

    # The custom metadata flag used for storing redmine URL
    # (optional, default: redmine_url).
    ckan.redmine.flag = redmine_url

    # A prefix to apply to the name of the dataset when creating an issue
    # (optional, default: New dataset)
    ckan.redmine.subject_prefix = New dataset

------------------------
Development Installation
------------------------

To install ckanext-redmine-autoissues for development, activate your CKAN virtualenv and
do::

    git clone https://github.com/sorki/ckanext-redmine-autoissues.git
    cd ckanext-redmine-autoissues
    python setup.py develop
    pip install -r dev-requirements.txt

See also Installation

---------------------------------------------------
Releasing a New Version of ckanext-redmine-autoissues
---------------------------------------------------

ckanext-redmine-autoissues is availabe on PyPI as https://pypi.python.org/pypi/ckanext-redmine-autoissues.
To publish a new version to PyPI follow these steps:

1. Update the version number in the ``setup.py`` file.
   See `PEP 440 <http://legacy.python.org/dev/peps/pep-0440/#public-version-identifiers>`_
   for how to choose version numbers.

2. Create a source distribution of the new version::

     python setup.py sdist

3. Upload the source distribution to PyPI::

     python setup.py sdist upload

4. Tag the new release of the project on GitHub with the version number from
   the ``setup.py`` file. For example if the version number in ``setup.py`` is
   0.0.2 then do::

       git tag v1.0.1
       git push --tags

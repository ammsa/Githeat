|logo|
======

Do you often find your self looking for a specific commit but you're unsure
when it has been committed? Do you have any large git repositories that you
want to find out who's contributing the most on a specifc day or month?
Do you hesitate whether you should install an open-source project because
you're not sure how active it is? GitHeat is developed to help you solve these
problems. GitHeat will local machine to parse the git-log of your repo and
allow you to navigate through an interactive heatmap in your own terminal,
showing you what days are most popular, and what months are most active.

Minimum Requirements
====================

* Python 2.7


Optional Requirements
=====================

..  _py.test: http://pytest.org
..  _Sphinx: http://sphinx-doc.org

* `py.test`_ 2.7 (for running the test suite)
* `Sphinx`_ 1.3 (for generating documentation)


Basic Setup
===========

Install for the current user:

..  code-block::

    $ python setup.py install --user


Run the application:

..  code-block::

    $ python -m githeat --help


Run the test suite:

..  code-block::
   
    $ py.test test/


Build documentation:

..  code-block::

    $ cd doc && make html
    
    
Deploy the application in a self-contained `Virtualenv`_ environment:

..  _Virtualenv: https://virtualenv.readthedocs.org

..  code-block::

    $ python deploy.py /path/to/apps
    $ cd /path/to/apps/ && githeat/bin/cli --help


.. |logo| image:: https://raw.githubusercontent.com/AmmsA/Githeat/master/website/static/images/logo.png?token=AAtq743NFLfHArCfd_styq-ckCxrpPKeks5XhWFNwA%3D%3D
   :width: 100px
   :alt: githeat
   :target: https://github.com/ammsa/Githeat
|logo|
======

GitHeat uses your local machine to parse the git-log of your repo and build an interactive heatmap in your terminal. You can use GitHeat to see what days are most popular, and what months are most active.

To start the interactive heatmap, run:

        $ githeat.interactive

|video|

or skip the interactive part and print the heatmap directly by running: 

        $ githeat

|githeat_cli|


Want to merge in the months? run

        $ githeat --month-merge

|githeat_cli_month_merge|


Want to separate each day block? run

        $ githeat --separate

|githeat_cli_separate|


Want to change the width of each block? choose between thin, reg, thick:

        $ githeat --width {thick,reg,thin}


|githeat_cli_width_thin|


Want to change the color of the graph? choose between grass, sky, fire

        $ githeat --color {grass,fire,sky}

|githeat_cli_color_fire|


Want to show who are the top 10 most committers? run and it will parse the days for you:

        $ githeat --stat --stat-number 10

|githeat_cli_stat_stat_number_10|


Want to filter out commits by author? write regex in the author argument:

        $ githeat --author="Will"

Want to filter out commits by keywords in commit? write regex in the grep argument:

        $ githeat --grep="Fix"

Have a specific YAML configuration file you want to use? pass it to the config argument:

        $ githeat --config PATH_TO_CONFIG.yaml

Need help? run:

      .. code-block:: html

        $ githeat -h

        usage: githeat.py [-h] [-c FILE] [--gtype {inline,block}]
                         [--width {thick,reg,thin}] [--days DAYS [DAYS ...]]
                          [--color {grass,fire,sky}] [--stat-number STAT_NUMBER]
                          [--stat] [--separate] [--month-merge] [--author AUTHOR]
                          [--grep GREP] [-v]
                          [--logging {CRITICAL,ERROR,WARNING,INFO,DEBUG,NOTSET}]

        githeat: Terminal Heatmap for your git repos

        optional arguments:
          -h, --help            show this help message and exit
          -c FILE, --config FILE
                                Specify YAML config file
          --gtype {inline,block}
                                Choose how you want the graph to be displayed
          --width {thick,reg,thin}
                                Choose how wide you want the graph blocks to be
          --days DAYS [DAYS ...]
                                Choose what days to show. Please enter list of day
                                abbreviations or full name of week
          --color {grass,fire,sky}
                                Choose type of coloring you want for your graph
          --stat-number STAT_NUMBER
                                Number of top committers to show in stat
          --stat, -s            Show commits stat
          --separate, -b        Separate each day
          --month-merge         Separate each month
          --author AUTHOR, -a AUTHOR
                                Filter heatmap by author. You can also write regex
                                here
          --grep GREP, -g GREP  Filter by keywords in commits
          -v, --version         print version and exit
          --logging {CRITICAL,ERROR,WARNING,INFO,DEBUG,NOTSET}
                                logger level

or for the interactive help

      .. code-block:: html

        $ githeat.interactive -h
         usage: githeat.py [-h] [-c FILE] [--width {thick,reg,thin}]
                  [--days DAYS [DAYS ...]] [--color {grass,fire,sky}]
                  [--month-merge] [--hide-legend] [--author AUTHOR]
                  [--grep GREP] [-v]
                  [--logging {CRITICAL,ERROR,WARNING,INFO,DEBUG,NOTSET}]

         githeat: Terminal Heatmap for your git repos

         optional arguments:
           -h, --help            show this help message and exit
           -c FILE, --config FILE
                                 Specify YAML config file
           --width {thick,reg,thin}
                                 Choose how wide you want the graph blocks to be
           --days DAYS [DAYS ...]
                                 Choose what days to show. Please enter list of day
                                 abbreviations or full name of week
           --color {grass,fire,sky}
                                 Choose type of coloring you want for your graph
           --month-merge         Separate each month
           --hide-legend         Hide legend
           --author AUTHOR, -a AUTHOR
                                 Filter heatmap by author. You can also write regex
                                 here
           --grep GREP, -g GREP  Filter by keywords in commits
           -v, --version         print version and exit
           --logging {CRITICAL,ERROR,WARNING,INFO,DEBUG,NOTSET}
                                 logger level



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

Install using pip:

..  code-block::

    $ pip install githeat


Or to obtain the latest most-up-to-date version, clone the repo and install it from source:

.. code-block::

    $ git clone https://github.com/AmmsA/Githeat
    $ cd Githeat && python setup.py install


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
.. |video| image:: https://asciinema.org/a/812lm3uzd9yk8dbe0aehj5jvj.png
   :target: https://asciinema.org/a/812lm3uzd9yk8dbe0aehj5jvj
.. |githeat_cli| image:: https://raw.githubusercontent.com/AmmsA/Githeat/master/website/static/images/githeat_cli.png?token=AAtq7w4e7O2ttQRmDsdX-7u1zRzv5q3Pks5XhWZIwA%3D%3D
.. |githeat_cli_month_merge| image:: https://raw.githubusercontent.com/AmmsA/Githeat/master/website/static/images/githeat_cli_month_merge.png?token=AAtq7wqIcMdV5lIyG2t76lcGPO6g_T60ks5XhWcewA%3D%3D
.. |githeat_cli_separate| image:: https://raw.githubusercontent.com/AmmsA/Githeat/master/website/static/images/githeat_cli_separate.png?token=AAtq7xdd7EWEmYnI-9Y5g3kJdj9kb26Qks5XhWjXwA%3D%3D
.. |githeat_cli_width_thin| image:: https://raw.githubusercontent.com/AmmsA/Githeat/master/website/static/images/githeat_cli_width_thin.png?token=AAtq7ycoZEZT0g99UJMrWmhyYHUYW4dGks5XhWkRwA%3D%3D
.. |githeat_cli_color_fire| image:: https://raw.githubusercontent.com/AmmsA/Githeat/master/website/static/images/githeat_cli_color_fire.png?token=AAtq7xPXiZYtF3U6dQcN4ikFHVIQCfHzks5XhWkcwA%3D%3D
.. |githeat_cli_stat_stat_number_10| image:: https://raw.githubusercontent.com/AmmsA/Githeat/master/website/static/images/githeat_cli_stat_stat_number_10.png?token=AAtq72NP0xh5eel4N5WGO3JgdSQgUMX-ks5XhWkkwA%3D%3D


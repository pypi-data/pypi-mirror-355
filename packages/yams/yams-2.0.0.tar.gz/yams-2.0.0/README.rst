README for yams
===============

Distributions
-------------
The source tarball is available at https://pypi.python.org/pypi/yams

Install
-------
From the source distribution, extract the tarball and run ::

    python setup.py install

For debian and rpm packages, use your usual tools according to your Linux
distribution. 


Documentation
-------------

The documentation is available at https://yams.readthedocs.io/


Code style
----------

The python code is verified against *flake8* and formatted with *black*.

* You can run `tox -e black` to check that the files are well formatted.
* You can run `tox -e black-run` to format them if needed.
* You can include the `.hgrc` to your own `.hgrc` to automatically run black
  before each commit/amend. This can be done by writing `%include ../.hgrc` at
  the end of your `.hgrc`.


Comments, support, bug reports
------------------------------
See the tracker at https://forge.extranet.logilab.fr/open-source/yams

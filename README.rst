
****************************
Wildfire Emission Explorer
****************************

|pypi_release| |pypi_status| |pypi_downloads| |docs|

An interface for quick analysis and reporting of wildfire emissions.

<h2 id = "contents">Contents</h2>

<details open = "open">
  <ol>
    <li><a href = "#description">Description</a></li>
    <li><a href = "#installation">Installation</a></li>
    <li><a href = "#cli-command">Low Level Modules</a></li>
    <li><a href = "#highlevint">High Level Interface</a></li>
    <li><a href = "#support">Support</a></li>
  </ol>
</details>

<h2 id = "description" >1.Description</h2>

#### Goal
Create an application that simplifies and speeds up the creation of various wildfire emission plots based on a subset of the ECMWF dataset.
The project consists of:
1. lower-level modules with the basic functions needed to extract data and produce a figure from a configuration file.
2.  higher-level interface for easily running the wildfire explorer in a notebook-like webpage.

#### Data Specifications

- **Dataset**: GFAS (Global Fire Assimilation System) from ECMWF.
- **Resolution**: daily data at 0.1 deg.
- **Period**: from January 2003 to present.
- **Satellite dataset assimilated**: MODIS Terra and Aqua Active Fire Products.

<h2 id = "installation">2. Installation</h2>

#### Quick Install
Download github repository and run 
```
conda env create -f environment.yml
```

<h2 id = "cli-command" >3. Low Level Modules</h2>       
<h2 id = "highlevint" >4. High Level Interface</h2>       
<h2 id = "support"     >5. Support</h2>                                             
                         
**Quick start**

Follow these steps to create a new repository from this template.

#. Click the `Use this template <https://github.com/esowc/python-package-template/generate>`_
   button and create a new repository with your desired name, location and visibility.

#. Clone the repository::

     git clone git@github.com:esowc/<your-repository-name>.git
     cd <your-repository-name>

#. Remove sample code::

     rm PACKAGE_NAME/sample.py
     rm tests/test_sample.py

#. Replace ``PACKAGE_NAME`` with your chosen package name::

     NEW_PACKAGE_NAME=<your-package-name>
     mv PACKAGE_NAME $NEW_PACKAGE_NAME
     sed -i "" "s/PACKAGE_NAME/$NEW_PACKAGE_NAME/g" setup.py \
        docs/source/conf.py \
        docs/source/getting_started/installing.rst \
        docs/source/index.rst \
        $NEW_PACKAGE_NAME/__meta__.py

#. Modify the contents of ``__meta__.py`` to reflect your repository. Note that there
   is no need to update this same information in ``setup.py``, as it will be imported
   directly from ``__meta__.py``.

#. Modify the project url in ``setup.py`` to reflect your project's home in GitHub.

#. Modify ``README.rst`` to reflect your repository. A number of `shield <https://shields.io/>`_
   templates are included, and will need to be updated to match your repository if you want
   to use them.

**Usage tips**

* Create an executable called ``qa`` containing the following::

    black .
    isort .

  Add this to your path, and run it from the top-level of your repository before
  committing changes::

    qa .

.. |pypi_release| image:: https://img.shields.io/pypi/v/thermofeel?color=green
    :target: https://pypi.org/project/thermofeel

.. |pypi_status| image:: https://img.shields.io/pypi/status/thermofeel
    :target: https://pypi.org/project/thermofeel

.. |pypi_downloads| image:: https://img.shields.io/pypi/dm/thermofeel
  :target: https://pypi.org/project/thermofeel
  
.. |docs| image:: https://readthedocs.org/projects/thermofeel/badge/?version=latest
  :target: https://thermofeel.readthedocs.io/en/latest/?badge=latest
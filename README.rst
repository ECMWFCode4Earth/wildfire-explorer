Wildfire Emission Explorer
--------------

An interface for quick analysis and reporting of wildfire emissions.

1. Description
--------------

Objective
^^^^^^^^^

Create an application that simplifies and speeds up the creation of
various wildfire emission plots based on a subset of the ECMWF dataset.
The project consists of:

#. Lower-level modules with the basic functions needed to extract data
   and produce a figure from a configuration file.
#. Higher-level interface for easily running the wildfire explorer in a
   notebook-like webpage.

Data Specifications
^^^^^^^^^^^^^^^^^^^

-  **Dataset**: GFAS (Global Fire Assimilation System) from ECMWF.
-  **Resolution**: daily data at 0.1 deg.
-  **Period**: from January 2003 to present.
-  **Satellite dataset assimilated**: MODIS Terra and Aqua Active Fire
   Products.

These data are stored in a PostGIS database (present locally in the ECMWF servers), which optimize the retrievel of these large amount of data. A preliminary study on the database performance is presented `here <https://github.com/esowc/wildfire-explorer/blob/master/emission_explorer/PostGIS/Database_Exploration_Phase.ipynb>`_ and `here <https://github.com/esowc/wildfire-explorer/blob/master/emission_explorer/PostGIS/Database_Exploration_v2.ipynb>`_, in the form of jupyter notebooks.

2. Installation
--------------

Quick Install
^^^^^^^^^^^^^

The file `environment.yml <https://github.com/esowc/wildfire-explorer/blob/master/environment.yml>`_ contains all the dependencies for this project. 
To run this project: 1) create a new environment using `conda  <https://docs.conda.io/en/latest/>`_ or `mamba <https://mamba.readthedocs.io/en/latest/>`_, 2) Install this repository through pip. Specific commands:

::

   conda env create -f environment.yml --name=<your-env-name>
   conda activate <your env name>
   pip install git+https://github.com/esowc/wildfire-explorer.git #installs the specific modules developed for this project

3. CLI command
--------------
It is possible to create quick plots directly using the CLI comands (no interface) and recursively producing plots for different countries as listed in the configuration file. In addition, the data can also be saved in separate csv file to reproduce again the plots. To run the cli, after installation use the following command:
::

   wildfire_explorer <path-to-file>/example_config.yml

the `example_config.yml https://github.com/esowc/wildfire-explorer/blob/master/emission_explorer/example_config.yml>`_ presented in this repository contains all the details about the parameters that can be changed by the user. 

This command is equivalent to running this line in the main folder of the repository:
::

   python data_handler.py <path-to-file>/example_config.yml

4. High-Level Interface
--------------
The best way to explore wildfire data and use this project is through its user interface, built as a jupyter notebook and visible with the following `voilá <https://voila.readthedocs.io/en/stable/>`_  command:
::

   voila <additional-path-to-file>/Official_UI_v0.1.ipynb

This will open the notebook Official_UI_v0.1.ipynb present in this repository and guide the user into creating and saving different plots. This `GIF <https://github.com/esowc/wildfire-explorer/blob/master/emission_explorer/GUI/images_gui/GIF_GUI_WildfireExplorer_3MB.gif>`_ shows the GUI capability.

.. image:: https://github.com/esowc/wildfire-explorer/blob/master/emission_explorer/GUI/images_gui/GIF_GUI_WildfireExplorer_3MB.gif
  :alt: GUI Demo

5. Acknowledgments
--------------
This project has been developed as part of the `ECMWF Summer of Weather Code <https://esowc.ecmwf.int/>`_ and proposes a solution for challenge `#32 <https://github.com/esowc/challenges_2022/issues/10>`_.

# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['ionics_fits', 'ionics_fits.models', 'ionics_fits.models.transformations']

package_data = \
{'': ['*']}

install_requires = \
['numpy>=1.21.2,<3.0', 'scipy>=1.7.1,<2.0.0', 'statsmodels>=0.14.0,<0.15.0']

setup_kwargs = {
    'name': 'ionics-fits',
    'version': '1.3.16',
    'description': 'Lightweight Python data fitting library with an emphasis on AMO/Quantum Information',
    'long_description': 'Lightweight Python library for data fitting with an emphasis on AMO (Atomic Molecular\nand Optical physics) and Quantum Information.\n\nSee the documentation at: https://oxionics.github.io/ionics_fits/\n',
    'author': 'hartytp',
    'author_email': 'thomas.peter.harty@gmail.com',
    'maintainer': 'None',
    'maintainer_email': 'None',
    'url': 'None',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.10,<4.0',
}


setup(**setup_kwargs)

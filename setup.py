import os
import re
import sys

from setuptools import setup, find_packages

setup(
	name='alliance-service',
	version=['poc.000'],
	packages=find_packages(),
	packages = ['alliance',
                  'alliance.common',
                  'alliance.model',
                  'pycassa.contrib'],

)

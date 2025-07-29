import os
from setuptools import setup

lib_folder = os.path.dirname(os.path.realpath(__file__))
requirement_path = lib_folder + '/requirements.txt'
install_requires = []

# Obtain list of requirements
if os.path.isfile(requirement_path):
    with open(requirement_path) as f:
        install_requires = f.read().splitlines()
        
with open("README.md", "r") as arq:
    readme = arq.read()

setup(
    name='gchat-sdk',
    version='0.0.8',
    license='MIT License',
    author='Tatianno Alves',
    long_description=readme,
    long_description_content_type="text/markdown",
    author_email='tferreiraalves@gmail.com',
    keywords='gchat chatbot sdk gnew',
    description=u'Gchat SDK for managing and closing conversations',
)
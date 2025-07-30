import json
from setuptools import setup
from pathlib import Path

here = Path(__file__).parent
with open('package.json') as f:
    package = json.load(f)
long_description = (here / 'README.md').read_text()

package_name = package["name"].replace(" ", "_").replace("-", "_")

setup(
    name=package_name,
    version=package["version"],
    author=package['author'],
    author_email="llbt.nvs.x@gmail.com",
    packages=[package_name],
    include_package_data=True,
    license=package['license'],
    description=package.get('description', package_name),
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
        "dash",
        "lifelines",
    ],
    classifiers = [
        'Framework :: Dash',
    ],    
    url="https://github.com/XLlobet/dash-kaplan-meier",
)

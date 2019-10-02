import os

from setuptools import setup

README = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()


setup(
    name='simplecharts',
    version='0.0.2',
    description='SVG charts without dependencies',
    long_description=README,
    url='https://github.com/xi/simplecharts',
    author='Tobias Bengfort',
    author_email='tobias.bengfort@posteo.de',
    py_modules=['simplecharts'],
    license='MIT',
    classifiers=[
        'Topic :: Scientific/Engineering :: Visualization',
    ]
)

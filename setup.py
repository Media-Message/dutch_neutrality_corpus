import os
import setuptools

CURRENT_DIRECTORY = os.path.abspath(os.path.dirname(__file__))
REQUIREMENTS_FILEPATH = os.path.join(CURRENT_DIRECTORY, 'requirements.txt')

with open(REQUIREMENTS_FILEPATH) as fp:
    required_packages = [
        r.rstrip() for r in fp.readlines()
        if not r.startswith('#') and not r.startswith('git+')
    ]

setuptools.setup(
    name='dutch_neutrality_corpus',
    version='0.1.0',
    author='Nick Leo Martin',
    author_email='nickleomartin@gmail.com',
    description=('A Python package to create the Dutch Wikipedia'
                 ' Neutrality Corpus.'),
    py_modules=['dutch_neutrality_corpus'],
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3 :: Only'
    ],
    install_requires=required_packages,
    entry_points="""
          [console_scripts]
          dutch_neutrality_corpus=dutch_neutrality_corpus:main
      """,
    packages=['dutch_neutrality_corpus'],
    package_data={},
    include_package_data=True,
)

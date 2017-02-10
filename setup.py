from setuptools import find_packages, setup

setup(name='energyPATHWAYS',
      version='0.2',
      description='Software package for long-term energy system modeling',
      url='https://github.com/energyPATHWAYS/energyPATHWAYS',
      author='Ben Haley, Ryan Jones, Michael Cohen, Gabe Kwok, Ana Mileva',
      packages=find_packages(),
      install_requires=['pandas',
                        'numpy',
                        'scipy',
                        'pint',
                        'pyomo',
                        'datetime',
                        'pytz',
                        'profilehooks',
                        'psycopg2',
                        'matplotlib', # util.py
                        'scikit-learn', # dispatch_classes.py
                        'click'
                        ],
      extras_require={'documentation': ["Sphinx"],
                      'api': ['flask',
                              'flask_bcrypt',
                              'flask_cors',
                              'flask_httpauth',
                              'flask_restful',
                              'flask_sqlalchemy',
                              'itsdangerous',
                              'marshmallow',
                              'mock',
                              'python-daemon',
                              'sqlalchemy'
                              ]
                      },
      include_package_data=True,
      entry_points='''
        [console_scripts]
        energyPATHWAYS=energyPATHWAYS.run:click_run
        ''',
)

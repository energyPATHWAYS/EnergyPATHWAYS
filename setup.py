from setuptools import find_packages, setup

setup(name='energyPATHWAYS',
      version='0.1',
      description='Software package for long-term energy system modeling',
      url='https://github.com/energyPATHWAYS/energyPATHWAYS',
      author='Ben Haley, Ryan Jones, Gabe Kwok, Michael Cohen, Ana Mileva, Sam Borgeson, Jim Williams',
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
                        'sklearn'
#                        'pathos'
                        ]
      )

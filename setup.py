from setuptools import setup, find_packages

setup(name='provider',
      version='0.1',
      description='Dependency injection. Or something.',
      license='MIT',
      author='Veeti Paananen',
      author_email='veeti.paananen@rojekti.fi',

      packages=find_packages(),
      install_requires=[
          'venusian',
      ],
      tests_require=[
          'pytest',
      ])
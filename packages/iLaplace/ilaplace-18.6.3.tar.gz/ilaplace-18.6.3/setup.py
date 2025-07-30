from setuptools import setup, find_packages
 
classifiers = [
  'Development Status :: 5 - Production/Stable',
  'Intended Audience :: Education',
  'Operating System :: Microsoft :: Windows :: Windows 10',
  'License :: OSI Approved :: MIT License',
  'Programming Language :: Python :: 3'
]
 
setup(
  name='iLaplace',
  version='18.6.3',
  description="A minimal Python interface for computing inverse Laplace transforms using Talbot’s method — designed as a clean and practical wrapper around mpmath, sympy, and numpy.",
  long_description=open('README.txt').read(),
  url='',  
  author='Mohammad H. Rostami',
  author_email='mhro.r84@gmail.com',
  license='MIT', 
  classifiers=classifiers,
  keywords='Laplace Inverse''Laplace Inverse Calculator''Fast Laplace Inverse Calculate''iLaplace''Fat iLaplace Calculator''Fast iLpalace Calculate''Math''Talbot''inverse Laplace transforms''Laplace',
  packages=find_packages(),
  install_requires=['mpmath','sympy','numpy']
)

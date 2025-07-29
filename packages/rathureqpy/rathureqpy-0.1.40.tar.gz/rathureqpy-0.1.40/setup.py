from setuptools import setup, find_packages
 
classifiers = [
  'Development Status :: 5 - Production/Stable',
  'Intended Audience :: Education',
  'Operating System :: Microsoft :: Windows :: Windows 10',
  'License :: OSI Approved :: MIT License',
  'Programming Language :: Python :: 3'
]
 
setup(
  name='rathureqpy',
  version='0.1.40',
  description='Manipulating lists, basic mathematical functions and LaTeX-like writing',
  long_description=open('README.md').read() + '\n\n' + open('CHANGELOG.txt').read(),
  long_description_content_type="text/markdown",
  url='',  
  author='Arthur Quersin',
  author_email='arthur.quersin@gmail.com',
  license='MIT', 
  classifiers=classifiers,
  keywords=['lists', 'math'],
  packages=find_packages(),
  install_requires=[],
  include_package_data=True
)
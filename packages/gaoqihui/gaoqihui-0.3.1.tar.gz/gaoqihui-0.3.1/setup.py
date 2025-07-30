from distutils.core import setup
from setuptools import find_packages

with open("README.rst", "r",encoding='utf-8') as f:
  long_description = f.read()

setup(name='gaoqihui',  # 包名
      version='0.3.1',  # 版本号
      description='just for an stupid exam',
      long_description=long_description,
      author='this_is_xm',
      author_email='386697591@qq.com',
      url='https://mp.weixin.qq.com/s/9FQ-Tun5FbpBepBAsdY62w',
      install_requires=[],
      license='BSD License',
      packages=find_packages(),
      platforms=["all"],
      classifiers=[
          'Intended Audience :: Developers',
          'Operating System :: OS Independent',
          'Natural Language :: Chinese (Simplified)',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: 3.8',
          'Topic :: Software Development :: Libraries'
      ],
      )
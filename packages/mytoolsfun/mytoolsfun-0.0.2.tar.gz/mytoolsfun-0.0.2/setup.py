from setuptools import setup
from setuptools.command.install import install
import os
import sys

class CustomInstall(install):
    def run(self):
        install.run(self)       
        if sys.platform == 'win32':
            project_root = os.path.dirname(os.path.abspath(_file__))
            sys.path.insert(0, project_root)
            from mytoolsfun import mytools
            mytools.init()
        elif sys.platform == 'linux':
            pass


setup(name='mytoolsfun',
      version='0.0.1',
      description="tools",
      author="xianzhi", 
      py_modules=["mytoolsfun.hello"],
      cmdclass={
           "install": CustomInstall
       },
   )

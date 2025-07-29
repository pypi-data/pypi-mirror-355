from setuptools import setup
from setuptools.command.install import install
import os
import sys

class CustomInstall(install):
    def run(self):
        install.run(self)
        #project_root = os.path.dirname(os.path.abspath(__file__))
        #sys.path.insert(0, project_root)
        if sys.platform == 'win32':
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

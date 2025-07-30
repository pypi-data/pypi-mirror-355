from setuptools import setup, find_packages
import codecs
import os

version     = "0.2.3"
description = "To generate a log tracking mechanism that can be customised."

with open( "README.md", "r" ) as f:
    long_description = f.read( )

# setting up
setup(
     name               = "logtrek"
    , version           = version
    , author            = "mose_tucker_0159"
    , author_email      = "mose.tucker.0159@gmail.com"
    , description       = description
    , long_description  = long_description
    , long_description_content_type \
                        = "text/markdown"
    , packages          = find_packages( )
    , install_requires  = [
         "bips"
      ]
    , keywords = [ "python" ]
    , classifiers = [
             "Development Status :: 1 - Planning"
            ,  "Intended Audience :: End Users/Desktop"
            ,  "Programming Language :: Python :: 3"
            ,  "Operating System :: Microsoft :: Windows"
      ]
)

# -*- coding: utf-8 -*-
"""
The __init__ module of the "apek" package, used to expose the package's classes and functions.

Classes:
    largeNumber.LargeNumber:
        Represent large numbers using the scientific notation XeY.
        Attributes:
            base (float): The base part of the number.
            exp (int): The exponent part of the number.
        Methods:
            __init__:
                Provide parameters "base" and "exp" to create an instance of LargeNumber.
                
                The specific value of LargeNumber is set through "base" and "exp",
                and it also supports setting precision and display unit table.
            parseToString:
                Convert the LargeNumber instance to a string based on the provided or default formatting parameters.

Constants:
    meta.cst_version:
        The version number of this package.
    meta.cst_lastVersion:
        The version number of the previous version of this package.
"""



from . import largeNumber
from . import helps
from . import meta

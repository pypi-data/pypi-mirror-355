# -*- coding: utf-8 -*-
"""
The __init__ module of the "apek" package, used to expose the package's classes and functions.

Classes:
    largeNumber.LargeNumber:
        Infomation:
            Represent large numbers using the scientific notation XeY.
        Attributes:
            base (float): The base part of the number.
            exp (int): The exponent part of the number.
        Methods:
            __init__:
                To Do:
                    Provide parameters "base" and "exp" to create an instance of LargeNumber.
                    
                    The specific value of LargeNumber is set through "base" and "exp",
                    and it also supports setting precision and display unit table.
                Args:
                    base (int or float, optional): "base" is used to control the base part of LargeNumber, that is, the "X" in "XeY", and its range will be automatically calibrated to [1, 10). The corresponding "exp" will be modified. The default is 0.
                    exp (int, optional): "exp" is used to control the exponent part of LargeNumber, that is, the "Y" in "XeY". The default is 0.
                    *args: When the constructor's argument list provides more (greater than or equal to three) non-keyword arguments, a TypeError will be thrown.
                    displayPrecision (int, optional): Keyword argument. Controls the decimal precision when displaying. Parts below the precision will be automatically rounded. It cannot be greater than "realPrecision" and cannot be negative. The default is 4.
                    realPrecision (int, optional): Keyword argument. Controls the decimal precision during actual calculations. Parts below the precision will be discarded. It cannot be less than "displayPrecision" and cannot be negative. The default is 8.
                    reprUnitTable (str or list or tuple, optional): Keyword argument. Controls the English units used for the exponent part when converting a LargeNumber instance with a large "exp" to a string. When accepting a str, each character is treated as a unit. When accepting a list or tuple, each item is treated as a unit. The units are ordered from smallest to largest from the beginning to the end. The iterable object must not be empty.
                    reprChineseUnitTable (str or list or tuple, optional): Keyword argument. Controls the Chinese units used for the exponent part when converting a LargeNumber instance with a large "exp" to a string. When accepting a str, each character is treated as a unit. When accepting a list or tuple, each item is treated as a unit. The units are ordered from smallest to largest from the beginning to the end. The iterable object must not be empty.
                Returns:
                    None
                Raises:
                    TypeError: A TypeError will be thrown when the number or type of the accepted arguments is incorrect.
                    ValueError: A ValueError will be thrown when the value of the accepted arguments is incorrect.
            parseToString:
                To Do:
                    Convert the LargeNumber instance to a string based on the provided or default formatting parameters.
                Args:
                    *args: When the constructor's argument list provides more (greater than or equal to three) non-keyword arguments, a TypeError will be thrown.
                    precision (int or "default"): Keyword argument. Controls the display precision of the base part when converting to a string. When the value is "default" or not provided, it defaults to the value of self.config["displayPrecision"].
                    largeExpRepr ("dotSplit" or "byUnit" or "byChineseUnit" or "power"): Keyword argument. Controls the display mode of the exponent part when converting to a string.
                        In the "dotSplit" mode, the exponent will use thousand separators.
                        In the "byUnit" mode, the exponent will use the unit table set by self.config["reprUnitTable"].
                        In the "byChineseUnit" mode, the exponent will use the unit table set by self.config["reprChineseUnitTable"].
                        In the "power" mode, the exponent will use the nested exponent syntax.
                        If no value is provided, it defaults to "dotSplit".
                Returns:
                    str: The string representation of the LargeNumber instance after conversion.
                Raises:
                    TypeError: A TypeError will be thrown when the number or type of the accepted arguments is incorrect.
"""



from . import largeNumber

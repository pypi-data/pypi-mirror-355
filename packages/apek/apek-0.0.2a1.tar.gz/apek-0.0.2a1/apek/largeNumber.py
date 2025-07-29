# -*- coding: utf-8 -*-

from math import floor as _flr, inf as _inf, nan as _nan
from re import sub as _sub


def _showArgsError(args):
    raise TypeError(f"{len(args)} extra parameters gived: {args}")


def _checkAndShowParamTypeError(varName, var, varType):
    if not isinstance(var, varType):
        s = None
        if isinstance(varType, type):
            s = varType.__name__
        elif isinstance(varType, (tuple, list, set)):
            if isinstance(varType, set):
                varType = list(varType)
            if len(varType) == 1:
                s = varType[0].__name__
            elif len(varType) == 2:
                s = varType[0].__name__ + " or " + varType[1].__name__
            elif len(varType) >= 3:
                bl = varType[:-1]
                s = ", ".join([i.__name__ for i in bl]) + " or " + varType[-1].__name__
        raise ValueError(f"The parameter \"{varName}\" must be {s}, but gived {type(var).__name__}.")


class LargeNumber():
    @staticmethod
    def _parseLargeNumberOrShowError(n):
        _checkAndShowParamTypeError("n", n, (LargeNumber, int, float))
        if not isinstance(n, (LargeNumber)):
            return LargeNumber(n, 0)
        return n
    
    def __init__(self, base=0, exp=0, *args, displayPrecision=4, realPrecision=8, reprUnitTable="KMBTPEZY", reprChineseUnitTable="万亿兆京垓秭穰"):
        """
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
        """
        _checkAndShowParamTypeError("base", base, (int, float))
        _checkAndShowParamTypeError("exp", exp, int)
        if args:
            _showArgsError(args)
        
        if base < 0:
            self.isNegative = True
            base = -base
        else:
            self.isNegative = False
        self.base, self.exp = base, exp
        
        cfg = {}
        
        if displayPrecision:
            _checkAndShowParamTypeError("displayPrecision", displayPrecision, int)
            if displayPrecision < 0:
                raise ValueError("The parameter 'displayPrecision' cannot be less than 0.")
            cfg["displayPrecision"] = displayPrecision
        else:
            cfg["displayPrecision"] = 4
        
        if realPrecision:
            _checkAndShowParamTypeError("realPrecision", realPrecision, int)
            if realPrecision < 0:
                raise ValueError("The parameter 'realPrecision' cannot be less than 0.")
            if realPrecision < displayPrecision:
                raise ValueError("The parameter 'realPrecision' cannot be less than parameter 'displayPrecision'.")
            cfg["realPrecision"] = realPrecision
        else:
            cfg["realPrecision"] = 8
        
        if reprUnitTable:
            _checkAndShowParamTypeError("reprUnitTable", reprUnitTable, (str, list, tuple))
            if not reprUnitTable:
                raise ValueError(f"The paramter 'reprUnitTable' cannot be empty {type(reprUnitTable).__name__}.")
            cfg["reprUnitTable"] = reprUnitTable
        else:
            cfg["reprUnitTable"] = "KMBTPEZY"
        
        if reprChineseUnitTable:
            _checkAndShowParamTypeError("reprChineseUnitTable", reprChineseUnitTable, (str, list, tuple))
            if not reprChineseUnitTable:
                raise ValueError(f"The paramter 'reprChineseUnitTable' cannot be empty {type(reprUnitTable).__name__}.")
            cfg["reprChineseUnitTable"] = reprChineseUnitTable
        else:
            cfg["reprChineseUnitTable"] = "万亿兆京垓秭穰"
        
        self.config = cfg
        
        self._calibrate()
    
    def _calibrate(self):
        base, exp = self.base, self.exp
        
        # Make the base in range: 1 <= base < 10
        if base >= 10:
            base /= 10
            exp += 1
        elif base < 1:
            base *= 10
            exp -= 1
        
        t = 10 ** self.config["realPrecision"]
        s1 = base * t
        s2 = _flr(s1)
        base = s2 / t
        
        self.base, self.exp = base, exp
    
    def parseString(self, *args, precision="default", largeExpRepr="dotSplit"):
        """
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
        if args:
            _showArgsError(args)
        if precision == "default":
            precision = self.config["displayPrecision"]
        _checkAndShowParamTypeError("precision", precision, int)
        _checkAndShowParamTypeError("largeExpRepr", largeExpRepr, str)
        
        base, exp = self.base, self.exp
        if -4 <= exp <= self.config["realPrecision"]:
            r = str(base * 10 ** exp)
            
            if self.isNegative:
                r = "-" + r
            
            r = _sub("\\.0$", "", r)
            return r
        
        pr = 10 ** precision
        
        dispBase = str(round(base * pr) / pr)
        dispExp = None
        
        if exp >= 1_000_000_000_000_000 or exp <= -10:
            largeExpRepr = "power"
        
        match largeExpRepr:
            case "dotSplit":
                s = str(exp)
                s = s[::-1]
                ns = ""
                while len(s) > 4:
                    ns += s[:4] + ","
                    s = s[4:]
                ns += s
                dispExp = ns[::-1]
            
            case "byUnit":
                units = self.config["reprUnitTable"]
                index = -1
                unit = ""
                while exp >= 1000 and index < len(units):
                    exp /= 1000
                    index += 1
                    unit = str(units[index])
                dispExp = str(round(exp * pr) / pr) + unit
            
            case "byChineseUnit":
                units = self.config["reprChineseUnitTable"]
                index = -1
                unit = ""
                while exp >= 10000 and index < len(units):
                    exp /= 10000
                    index += 1
                    unit = str(units[index])
                dispExp = str(round(exp * pr) / pr) + unit
            
            case "power":
                dispExp = str(LargeNumber(exp, 0))
        
        if self.isNegative:
            dispBase = "-" + dispBase
        
        dispBase = _sub("\\.0$", "", dispBase)
        dispExp = _sub("\\.0$", "", dispExp)
        
        return dispBase + "e" + dispExp
    
    def __str__(self):
        return self.parseString()
    
    def __repr__(self):
        return self.parseString()
    
    def __getitem__(self, key):
        _checkAndShowParamTypeError("key", key, str)
        
        match key:
            case "base" if not self.isNegative:
                return self.base
            case "base" if self.isNegative:
                return -self.base
            case "exp":
                return self.exp
            case "config.displayPrecision":
                return self.config["displayPrecision"]
            case "config.realPrecision":
                return self.config["realPrecision"]
            case "config.reprUnitTable":
                return self.config["reprUnitTable"]
            case "config.reprChineseUnitTable":
                return self.config["reprChineseUnitTable"]
            case _:
                raise KeyError(f"Not found the key '{key}'.")
    
    def __setitem__(self, key, value):
        _checkAndShowParamTypeError("key", key, str)
        def check(t):
            _checkAndShowParamTypeError("value", value, t)
        
        match key:
            case "base":
                check((int, float))
                if value >= 0:
                    self.base = value
                    self.isNegative = False
                else:
                    self.base = -value
                    self.isNegative = True
            case "exp":
                check(int)
                self.exp = value
            case "config.displayPrecision":
                check(int)
                self.config["displayPrecision"] = value
            case "config.realPrecision":
                check(int)
                self.config["realPrecision"] = value
            case "config.reprUnitTable":
                check((str, list, tuple))
                self.config["reprUnitTable"] = value
            case "config.reprChineseUnitTable":
                check((str, list, tuple))
                self.config["reprChineseUnitTable"] = value
            case _:
                raise KeyError(f"Not found the key '{key}'.")
    
    def __neg__(self):
        return LargeNumber(-self.base, self.exp)
    
    def __pos__(self):
        return self
    
    def __abs__(self):
        return LargeNumber(self.base, self.exp)
    
    def __add__(self, other):
        other = self._parseLargeNumberOrShowError(other)
        
        if self.exp < other.exp:
            self.base, self.exp, other.base, other.exp = other.base, other.exp, self.base, self.exp
        elif self.exp == other.exp:
            return LargeNumber(self.base + other.base, self.exp)
        
        t = 10 ** (self.exp - other.exp)
        
        n1, n2 = self.base * t, other.base
        newExp = other.exp
        
        if self.isNegative:
            n1 = -n1
        if other.isNegative:
            n2 = -n2
        
        return LargeNumber(n1 + n2, newExp)
    
    def __radd__(self, other):
        return self + other
    
    def __iadd__(self, other):
        return self + other
    
    def __sub__(self, other):
        other = self._parseLargeNumberOrShowError(other)
        return self + -other
    
    def ___rsub__(self, other):
        other = self._parseLargeNumberOrShowError(other)
        return other + -self
    
    def __isub__(self, other):
        other = self._parseLargeNumberOrShowError(other)
        return self - other
    
    def __mul__(self, other):
        other = self._parseLargeNumberOrShowError(other)
        b1, b2, e1, e2 = self.base, other.base, self.exp, other.exp
        
        if self.isNegative == other.isNegative:
            return LargeNumber(b1 * b2, e1 + e2)
        
        return LargeNumber(-b1 * b2, e1 + e2)
    
    def __rmul__(self, other):
        return self * other
    
    def __imul__(self, other):
        return self * other
    
    def __truediv__(self, other):
        other = self._parseLargeNumberOrShowError(other)
        return LargeNumber(self.base / other.base, self.exp - other.exp)
        # In the LargeNumber,
        # errors divided by 0 will use the default behavior.
    
    def __rtruediv__(self, other):
        other = self._parseLargeNumberOrShowError(other)
        return LargeNumber(other.base / self.base, other.exp - self.exp)
    
    def __itruediv__(self, other):
        return self / other
    
    def __bool__(self):
        if self.base == self.exp == 0:
            return False
        return True
    
    def __eq__(self, other):
        other = self._parseLargeNumberOrShowError(other)
        if (self.base == other.base) and (self.exp == other.exp):
            return True
        return False
    
    def __ne__(self, other):
        return not self == other
    
    def __lt__(self, other):
        other = self._parseLargeNumberOrShowError(other)
        if self.exp != other.exp:
            return self.exp < other.exp
        return self.base < other.base
    
    def __le__(self, other):
        return self < other or self == other
    
    def __gt__(self, other):
        return not self <= other
    
    def __ge__(self, other):
        return not self < other
    
    def __int__(self):
        n = 0
        
        if self.exp < 0:
            return n
        
        if 0 <= self.exp < 7:
            n = int(self.base * 10 ** self.exp)
        elif 7 <= self.exp <= 32768:
            s1 = str(10 ** self.exp)
            s2 = str(int(self.base * 100_0000))
            s3 = s2 + s1[7:]
            n = int(s3)
        elif self.exp > 32768:
            raise OverflowError(f"Cannot convert the number to int, it is too large: {self.base}e{self.exp}")
        
        if self.isNegative:
            n = -n
        return n
    
    def __float__(self):
        n = 0.0
        
        if self.exp < -256:
            return n
        
        if -256 <= self.exp <= 256:
            n = float(self.base * 10 ** self.exp)
        elif self.exp > 256:
            return _inf
        
        if self.isNegative:
            n = -n
        return n
    
    def __complex__(self):
        return complex(float(self))

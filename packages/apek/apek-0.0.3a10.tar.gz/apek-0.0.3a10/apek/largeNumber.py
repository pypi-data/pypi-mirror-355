# -*- coding: utf-8 -*-
"""
The main module of the package.

Handle large numbers through the LargeNumber class.

Classes:
    LargeNumber:
        The main class.
"""



import math as _math
import re as _re


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
    """
    Handle large numbers through the class.
    
    Attributes:
        base (float): The base part of the number.
        exp (int): The exponent part of the number.
        isNegative (bool): Set whether the base is negative.
        cfg (dict): The dictionary that stores dispPrec, realPrec, reprUnits_en, and reprUnits_zh.
    
    Methods:
        parseToString:
            Convert the LargeNumber instance to a string based on the provided or default formatting parameters.
    """
    
    @staticmethod
    def _parseLargeNumberOrShowError(n):
        _checkAndShowParamTypeError("n", n, (LargeNumber, int, float))
        if not isinstance(n, (LargeNumber)):
            return LargeNumber(n, 0)
        return n
    
    def __init__(
        self,
        base = 0,
        exp = 0,
        *args,
        dispPrec = 4,
        realPrec = 8,
        reprUnits_en = "KMBTPEZY",
        reprUnits_zh = "万亿兆京垓秭穰"
    ):
        """
        Provide parameters "base" and "exp" to create an instance of LargeNumber.
        
        The specific value of LargeNumber is set through "base" and "exp",
        and it also supports setting precision and display unit table.
        
        Args:
            base (int or float, optional):
                "base" is used to control the base part of LargeNumber, that is the "X" in "XeY",
                and its range will be automatically calibrated to [1, 10).
                The corresponding "exp" will be modified.
                The default is 0.
            exp (int, optional):
                "exp" is used to control the exponent part of LargeNumber, that is the "Y" in "XeY".
                The default is 0.
            *args:
                When the constructor's argument list provides more (greater than or equal to three) non-keyword arguments,
                a TypeError will be thrown.
            dispPrec (int, optional):
                Keyword argument.
                Controls the decimal precision when displaying.
                Parts below the precision will be automatically rounded.
                It cannot be greater than "realPrec" and cannot be negative.
                The default is 4.
            realPrec (int, optional):
                Keyword argument.
                Controls the decimal precision during actual calculations.
                Parts below the precision will be discarded.
                It cannot be less than "dispPrec" and cannot be negative.
                The default is 8.
            reprUnits_en (str or list or tuple, optional):
                Keyword argument.
                Controls the English units used for the exponent part when converting a LargeNumber instance with a large "exp" to a string.
                When accepting a str, each character is treated as a unit.
                When accepting a list or tuple, each item is treated as a unit.
                The units are ordered from smallest to largest from the beginning to the end.
                The iterable object must not be empty.
            reprUnits_zh (str or list or tuple, optional):
                Keyword argument.
                Controls the Chinese units used for the exponent part when converting a LargeNumber instance with a large "exp" to a string.
                When accepting a str, each character is treated as a unit.
                When accepting a list or tuple, each item is treated as a unit.
                The units are ordered from smallest to largest from the beginning to the end. The iterable object must not be empty.
        
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
        
        if dispPrec:
            _checkAndShowParamTypeError("dispPrec", dispPrec, int)
            if dispPrec < 0:
                raise ValueError("The parameter 'dispPrec' cannot be less than 0.")
            cfg["dispPrec"] = dispPrec
        else:
            cfg["dispPrec"] = 4
        
        if realPrec:
            _checkAndShowParamTypeError("realPrec", realPrec, int)
            if realPrec < 0:
                raise ValueError("The parameter 'realPrec' cannot be less than 0.")
            if realPrec < dispPrec:
                raise ValueError("The parameter 'realPrec' cannot be less than parameter 'dispPrec'.")
            cfg["realPrec"] = realPrec
        else:
            cfg["realPrec"] = 8
        
        if reprUnits_en:
            _checkAndShowParamTypeError("reprUnits_en", reprUnits_en, (str, list, tuple))
            if not reprUnits_en:
                raise ValueError(f"The paramter 'reprUnits_en' cannot be empty {type(reprUnits_en).__name__}.")
            cfg["reprUnits_en"] = reprUnits_en
        else:
            cfg["reprUnits_en"] = "KMBTPEZY"
        
        if reprUnits_zh:
            _checkAndShowParamTypeError("reprUnits_zh", reprUnits_zh, (str, list, tuple))
            if not reprUnits_zh:
                raise ValueError(f"The paramter 'reprUnits_zh' cannot be empty {type(reprUnits_en).__name__}.")
            cfg["reprUnits_zh"] = reprUnits_zh
        else:
            cfg["reprUnits_zh"] = "万亿兆京垓秭穰"
        
        self.config = cfg
        
        self._calibrate()
    
    def _calibrate(self):
        base, exp = self.base, self.exp
        
        k = _math.floor(_math.log10(base))
        exp += k
        base /= 10 ** k
        
        t = 10 ** self.config["realPrec"]
        s1 = base * t
        s2 = _math.floor(s1)
        base = s2 / t
        
        self.base, self.exp = base, exp
    
    def parseString(self, *args, prec="default", expReprMode="dotSplit", template="{1}e{2}"):
        """
        Convert the LargeNumber instance to a string based on the provided or default formatting parameters.
        
        Args:
            *args:
                When the constructor's argument list provides more (greater than or equal to three) non-keyword arguments,
                a TypeError will be thrown.
            prec (int or "default"):
                Keyword argument.
                Controls the display prec of the base part when converting to a string.
                When the value is "default" or not provided,
                it defaults to the value of self.config["dispPrec"].
            expReprMode ("dotSplit" or "byUnit" or "byChineseUnit" or "power"):
                Keyword argument.
                Controls the display mode of the exponent part when converting to a string.
                In the "dotSplit" mode, the exponent will use thousand separators.
                In the "byUnit" mode, the exponent will use the unit table set by self.config["reprUnits_en"].
                In the "byChineseUnit" mode, the exponent will use the unit table set by self.config["reprUnits_zh"].
                In the "power" mode, the exponent will use the nested exponent syntax.
                If no value is provided, it defaults to "dotSplit".
            template (str):
                Keyword argument.
                Controls the position and format of base and exp during string formatting.
                The index of base is 0 and the index of exp is 1.
                The default is "{}e{}".
        
        Returns:
            str:
                The string representation of the LargeNumber instance after conversion.
        
        Raises:
            TypeError:
                It will be thrown when the number or type of the accepted arguments is incorrect.
        """
        
        if args:
            _showArgsError(args)
        if prec == "default":
            prec = self.config["dispPrec"]
        _checkAndShowParamTypeError("prec", prec, int)
        _checkAndShowParamTypeError("expReprMode", expReprMode, str)
        
        base, exp = self.base, self.exp
        if -4 <= exp <= self.config["realPrec"]:
            r = str(base * 10 ** exp)
            
            if self.isNegative:
                r = "-" + r
            
            r = _re.sub("\\.0$", "", r)
            return r
        
        pr = 10 ** prec
        
        dispBase = str(round(base * pr) / pr)
        dispExp = None
        
        if exp >= 1_000_000_000_000_000 or exp <= -10:
            expReprMode = "power"
        
        match expReprMode:
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
                units = self.config["reprUnits_en"]
                index = -1
                unit = ""
                while exp >= 1000 and index < len(units):
                    exp /= 1000
                    index += 1
                    unit = str(units[index])
                dispExp = str(round(exp * pr) / pr) + unit
            
            case "byChineseUnit":
                units = self.config["reprUnits_zh"]
                index = -1
                unit = ""
                while exp >= 10000 and index < len(units):
                    exp /= 10000
                    index += 1
                    unit = str(units[index])
                dispExp = str(round(exp * pr) / pr) + unit
            
            case "power":
                dispExp = str(LargeNumber(exp, 0))
            
            case _:
                raise ValueError(f"Invalid expReprMode: {repr(expReprMode)}")
        
        if self.isNegative:
            dispBase = "-" + dispBase
        
        dispBase = _re.sub("\\.0$", "", dispBase)
        dispExp = _re.sub("\\.0$", "", dispExp)
        
        return template.format(dispBase, dispExp)
    
    def parseInt(self, *args, mode="default"):
        """
        Convert the string to an integer
        
        Args:
            mode (str):
                Keyword argument.
                Controls the behavior when converting to an integer.
                In "default" mode, it will be directly converted to an integer.
                In "power N" mode, when the exponent is greater than N, an error will be thrown, using only "power" defaults to "power 128".
        
        Returns:
            int:
                The converted integer
        
        Raises:
            OverflowError:
                This error is raised when the exponent exceeds the specified range of power,
                or the limits of Python.
        """
        
        if args:
            _showArgsError(args)
        
        if mode == "default":
            if self.getBase() == 0:
                return 0
            if self.getConfig("realPrec") >= self.getExp():
                return int(self.getBase() * 10 ** self.getExp())
            expSub = self.getExp() - self.getConfig("realPrec")
            base = str(self.getBase()).replace(".", "")
            expSub -= len(base) - 1
            return base + "0" * expSub
        
        elif mode == "power" or _re.search("^power\\s+\\d{1,6}$", mode):
            if mode == "power":
                mode = "power 128"
                power = int(_re.split("\\s+", mode)[1])
                if self.getExp() > power:
                    raise OverflowError(f"The exponent exceeds the allowed upper limit: {power}")
                return self.parseInt(mode="default")
        
        else:
            raise ValueError(f"Invalid mode: {repr(mode)}")
    
    def getBase(self):
        """
        Get the base.
        
        Returns:
            float: The base.
        """
        
        if self.isNegative:
            return -self.base
        return self.base
    
    def getExp(self):
        """
        Get the exponent.
        
        Returns:
            int: The exponent.
        """
        
        return self.exp
    
    def getConfig(self, key):
        """
        Get the configs.
        
        Returns:
            dict: The configs.
        """
        
        if not key:
            return self.config
        return self.config.get(key)
    
    def __str__(self):
        return self.parseString()
    
    def __repr__(self):
        return self.parseString()
    
    def __neg__(self):
        return LargeNumber(self.getBase(), self.getExp())
    
    def __pos__(self):
        return self
    
    def __abs__(self):
        return LargeNumber(self.base, self.exp)
    
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
    
    def __bool__(self):
        if self.base == self.exp == 0:
            return False
        return True
    
    def __int__(self):
        return self.parseInt()
    
    def __float__(self):
        n = 0.0
        
        if self.exp < -256:
            return n
        
        if -256 <= self.exp <= 256:
            n = float(self.base * 10 ** self.exp)
        elif self.exp > 256:
            return _math.inf
        
        if self.isNegative:
            n = -n
        return n
    
    def __complex__(self):
        return complex(float(self))
    
    def __add__(self, other):
        other = self._parseLargeNumberOrShowError(other)
        
        if self == other:
            return (self.base + other.base, self.exp)
        
        big, small = 0, 0
        if self < other:
            big, small = other, self
        else:
            big, small = self, other
        
        if big.getExp() - small.getExp() > big.getConfig("realPrec"):
            return big
        
        expSub = big.getExp() - small.getExp()
        bigBase = big.getBase * 10 ** expSub()
        smallBase = small.getBase()
        
        return LargeNumber(bigBase + smallBase, small.getExp())
    
    def __radd__(self, other):
        return self + other
    
    def __iadd__(self, other):
        return self + other
    
    def __sub__(self, other):
        other = self._parseLargeNumberOrShowError(other)
        return self + -other
    
    def __rsub__(self, other):
        other = self._parseLargeNumberOrShowError(other)
        return other + -self
    
    def __isub__(self, other):
        other = self._parseLargeNumberOrShowError(other)
        return self - other
    
    def __mul__(self, other):
        pass
        other = self._parseLargeNumberOrShowError(other)
        return LargeNumber(
            self.getBase() * other.getBase(),
            self.getExp() + other.getExp()
        )
    
    def __rmul__(self, other):
        return self * other
    
    def __imul__(self, other):
        return self * other
    
    def __truediv__(self, other):
        other = self._parseLargeNumberOrShowError(other)
        if other == 0:
            return _math.inf
        return LargeNumber(self.base / other.base, self.exp - other.exp)
    
    def __rtruediv__(self, other):
        return other / self
    
    def __itruediv__(self, other):
        return self / other

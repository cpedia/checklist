'''
module to help encode and/or decode string.

no rights reserved.
'''
import sys

defaultencoding = "uft-8"

def str2uni(string, enc = defaultencoding):
    '''convert str to unicode
    you can specify encoding. default to local encoding.
    string can be a int.
    '''
    if isinstance(string, str):
        return unicode(string, enc)
    elif isinstance(string, int):
        return unicode(str(string), enc)
    else:
        return string

def uni2str(string, enc = defaultencoding):
    '''convert unicode to str
    you can specify encoding. default to local encoding.
    '''
    if isinstance(string, unicode):
        return string.encode(enc)
    else:
        return string

def utf82uni(string):
    '''convert utf8 str to unicode'''
    return str2uni(string, "utf-8")

def uni2utf8(string):
    '''convert unicode to utf8 str'''
    return uni2str(string, "utf-8")

def local2utf8(string):
    '''convert local str to utf8 str'''
    return uni2utf8(str2uni(string))

def utf82local(string):
    '''convert utf8 str to local str'''
    return uni2str(utf82uni(string))

from StringIO import StringIO

import sys

import unittest

import moderation

from moderation.tests.utils.testsettingsmanager import get_only_settings_locals


class UtilsTestCase(unittest.TestCase):
        
    def test_get_only_settings_locals(self):
        MYSETTING_LOCAL1 = 'test'
        MYSETTING_LOCAL2 = 'test'
        self.assertEqual(get_only_settings_locals(locals()),
                        dict(MYSETTING_LOCAL1='test',
                             MYSETTING_LOCAL2='test'))
        
        
class PEP8TestCase(unittest.TestCase):
    
    def test_pep8_rules(self): 
        import pep8 
        sys.argv[1:] = ['--filename=*.py', '--show-source', '--show-pep8',
                        '--ignore=W291', moderation.__path__[0]]  
        buf = StringIO()         
        sys.stdout = buf
        pep8._main()            
        sys.stdout = sys.__stdout__   
        result = buf.getvalue()

        self.assertEqual("", result,
                         "Code messages should be empty but was:\n" + result)

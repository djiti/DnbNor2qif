#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

# DnbNor2Qif is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# DnbNor2Qif is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with DnbNor2Qif; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

# Author: djiti


import sys
import csv
import tempfile
import re
from datetime import date
import os
import getopt

def Usage():
    print '''Usage: dnbnor2qif -h | <files>
Generates a file 'dnbnor.qif' from a list of CSV files generated by DnbNor.
Assumes that the DnbNor files have been generated in English.

-h      Displays this help
<files> List of CSV files'''

def Parse(FileName):
    ''' Cleans up a DnbNor-issued CSV file and returns a usable CSV file '''
    File = open(FileName, 'rb')
    data = File.read()
    File.close()
    CleanedUpFile = tempfile.NamedTemporaryFile(delete=False)
    # TODO: Sure we can do better to handle the Norwegian characters
    data = data.replace('\x00', '_').replace('\xc5','A').replace('\xf8','o').replace('\xe6','ae').replace('\xd8','O').replace('\xd6','O').replace('\xe5','aa').replace('\xc8', 'E').replace('\xe9','ae').replace('\xe8','e')
    CleanedUpFile.write(data)
    CleanedUpFile.close()
    CsvReader = csv.DictReader(open(CleanedUpFile.name, 'rb'), delimiter=';')
    return CsvReader, CleanedUpFile.name

def GenerateQif(Reader, File):
    ''' Populates a QIF file from a CSV reader '''
    File.write('!Type:Bank\n')
    for Entry in Reader:
        TheTransaction = Transaction(Entry)
        TheTransaction.WriteQifLine(File)


class Transaction:
    ''' This class represents a single transaction '''
    def __init__(self, _CsvLine):
        self._CsvLine = _CsvLine
        
    def GetDate(self):
        m = re.match('^(\d+)\.(\d+)\.(\d+)$', self._CsvLine['Date'])
        if m is None:
            raise Exception('Unable to parse Date %s' % self._CsvLine['Date'] )
        TheDate = date(2000+int(m.group(3)), int(m.group(1)), int(m.group(2)))
        return TheDate.strftime('%d/%m/%Y')

    def GetDescription(self):
        Description = self._CsvLine['Description']
        # TODO: Clean-up of the description field can certainly be improved
        m = re.match('^(.*) Dato.*$', Description)
        if m is not None:
            Description = m.group(1)
        m = re.search('     ([^ ].*)$', Description)
        if m is not None:
            Description = m.group(1)
        return Description

    def GetAmount(self):
        return float(self._CsvLine['Deposits'])-float(self._CsvLine['Withdrawals'])

    def WriteQifLine(self, File):
        Entry = '''D%s
T%s
P%s
^
''' % (self.GetDate(), self.GetAmount(), self.GetDescription())
        File.write(Entry)


def main(argvec):
    
    try:
        opts, args = getopt.getopt(argvec, "h")
    except getopt.GetoptError:
        Usage()
        sys.exit(1)

    for opt, _ in opts:
        if opt == '-h':
            Usage()
            sys.exit(0)
        else:
            print "Unhandled option: ", opt
            Usage()
            sys.exit(1)

    if len(args)<1:
        Usage()
        sys.exit(0)
    
    OutFileName = os.path.join(os.path.dirname(args[0]), 'dnbnor.qif')
    OutFile = open(OutFileName, 'w') 
    for FileName in args:
        TempFile = ''
        try:
            print 'Working on %s' % FileName
            Reader, TempFile = Parse(FileName)
            GenerateQif(Reader, OutFile)
        except:
            raise
        os.unlink(TempFile)

    OutFile.close()
   

if __name__ == "__main__":
    main(sys.argv[1:])

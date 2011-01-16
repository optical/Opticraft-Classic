'''Simple command-line tool for executing querys on an SQLite3 database'''
# Copyright (c) 2010-2011,  Jared Klopper
# All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice, this
#       list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright notice,
#       this list of conditions and the following disclaimer in
#       the documentation and/or other materials provided with the distribution.
#     * Neither the name of Opticraft nor the names of its contributors may be
#       used to endorse or promote products derived from this software without
#       specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
#  A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import sqlite3
import time
import os.path

def SetupConnection():
    ValidName = False
    while not ValidName:
        DatabaseName = raw_input("Database name: ")

        if DatabaseName != ":memory:" and os.path.exists(DatabaseName) == False:
            NewDatabasePrompt = True
            while NewDatabasePrompt:
                CreateNew = raw_input("\"%s\" does not exist. Would you like to create it? (y/n): " %DatabaseName)
                if CreateNew.lower() in ["y","n"]:
                    if CreateNew.lower() == "y":
                        ValidName = True
                        NewDatabasePrompt = False
                    else:
                        NewDatabasePrompt = False
        else:
            ValidName = True


    Con = sqlite3.connect(DatabaseName)
    print "Now connected to: %s" %DatabaseName
    print #New line
    return Con

def ExecuteQuery(Connection,Query):
    Cursor = Connection.cursor()
    Start = time.time()
    try:
        Cursor.execute(Query)
    except sqlite3.OperationalError, (Message):
        print "OperationalError: %s" %Message
        return
    Rows = Cursor.fetchall()
    NumRows = len(Rows)
    Delta = time.time()-Start
    #Is it anything but a SELECT operation
    if Query.split()[0].upper() != "SELECT":
        if Cursor.rowcount != -1:
            print "Query OK, %d rows affected (%.2f sec)" %(Cursor.rowcount,Delta)
        else:
            print "Query OK, 0 rows affected (%.2f sec)" %(Delta)
        return
    #Its a select operation
    if len(Rows) == 0:
        print "Empty set (%.2f sec)" %(Delta)
        return
    #Do some fancy formatting.
    Fields = Rows[0].keys()
    NumFields = len(Fields)
    ColumnLengths = [len(i) for i in Fields]
    #Calculate the longest value for the column, so we can make a nicely spaced table
    for Row in Rows:
        for Column in xrange(len(ColumnLengths)):
            if len(str(Row[Column])) > ColumnLengths[Column]:
                ColumnLengths[Column] = len(str(Row[Column]))
    ColumnLengths = [i + 2 for i in ColumnLengths] #Increase value by two for buffering
    LineSeperator = "+"
    for Length in ColumnLengths:
        LineSeperator += "-" * Length + "+"
    print LineSeperator
    #Print Field/Column names
    ColumnLine = "|"
    for i in xrange(len(Fields)):
        Field = Fields[i]
        Length = ColumnLengths[i]
        LeftPadding = (Length - len(Field))/2
        RightPadding = Length - len(Field) - LeftPadding
        ColumnLine += "%s%s%s|" %(" " *LeftPadding, Field, " "*RightPadding)
    print ColumnLine
    print LineSeperator
    Delta = time.time() - Start
    #Now to print rows
    for Row in Rows:
        RowLine = "|"
        for i in xrange(NumFields):
            Length = ColumnLengths[i]
            LeftPadding = (Length - len(str(Row[i])))/2
            RightPadding = Length - len(str(Row[i])) - LeftPadding
            RowLine += "%s%s%s|" %(" "*LeftPadding, str(Row[i])," " *RightPadding)
        print RowLine
    print LineSeperator
    print "%d rows in set (%.2f sec)" %(NumRows,Delta)


def main():
    print "Welcome to the Sqlite3 shell"
    print "Press Ctrl-C at any time to terminate\n"
    Connection = SetupConnection()
    Connection.row_factory = sqlite3.Row
    Connection.text_factory = str
    Connection.isolation_level = None
    Continue = False
    while True:
        if not Continue:
            Query = raw_input("sqlite> ")
        else:
            Query += raw_input("     -> ")
        if sqlite3.complete_statement(Query):
            ExecuteQuery(Connection,Query.strip())
            print #New line
            Continue = False
        else:
            Continue = True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass

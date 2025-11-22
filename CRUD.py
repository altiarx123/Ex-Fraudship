#importing liberaries
#import tkinter as tk
#from tkinter import *
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pymysql
import os
import getpass
#Code Starts Here
print("Basic CRUD OPERATION")
# read connection info from environment if provided, otherwise prompt for password
MYSQL_HOST = os.getenv('MYSQL_HOST', '127.0.0.1')
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_PWD = os.getenv('MYSQL_PWD')
if not MYSQL_PWD:
    try:
        MYSQL_PWD = getpass.getpass(f"MySQL password for user {MYSQL_USER}: ")
    except Exception:
        # fallback to empty password if getpass fails (non-interactive)
        MYSQL_PWD = ''

con = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PWD,
    cursorclass=pymysql.cursors.DictCursor)
try:
    print(con.connection_id())
except Exception:
    print("connection complete")

#installation curobj object
curobj=con.cursor()
def cls():
    print("\n" * 4)
def intro():
    print('''+================================+
    SQL Data Management System (DMS)
+================================+''')
def menu():
    cls()
    intro()
    print(" Select a CRUD operation...")
    print(" 1. Create Database")
    print(" 2. Create table")
    print(" 3. Insert")
    print(" 4. Select All Records") 
    print(" 5. Select columns Conditionally")
    print(" 6. Update")
    print(" 7. Delete table")
    print(" 8. Delete Database")
    print(" 9. Desc table")
    print(" S. Show Tables")
    print(" P. Plot a graph")
    print(" A. Alter")
    print(" E. Export")
    print(" Q. Quit")
    #showtb()
    
def main():
    ch = 0
    menu()
    ch = input("Press 1 to 5 for CRUD or Q to Quit: ")
    if ch == '1':
        createdb()
    elif ch=='s' or ch=='S':
        showtb()
    elif ch == '2':
        createtb()
    elif ch == '3':
        insert()
    elif ch == '4':
        selectall()       
    elif ch == '5':
        selectcon() 
    elif ch == '6':
        update()
    elif ch == '7':
        droptb()
    elif ch=='8':
        dropdb()
    elif ch == '9':
        desctb()
    elif ch=='A' or ch=='a':
        alter()
    elif ch=='P' or ch=='p':
        plot()
    elif ch == 'Q' or ch == 'q' :
        print("Thanks for using DMS!")
    elif ch == 'E' or ch == 'e' :
        export()
    else: 
        print("Invalid choice! Enter a valid option.")
        main() 
    while ch == 'Q' or ch == 'q':
        curobj.close()
        con.close()
        raise SystemExit#terminate the app
    else:
        replayMenu()
def replayMenu():
    startover = ""
    startover = input('...continue (y/n)? ')
    while startover.lower() != 'y':
        print("Thank you for using DMS.")
        break
    else:
        main()
def createdb():
    Q=input("Do you have a Database (y/n): ").lower()
    if Q=='n':
        dname=input("enter the database name: ")
        q1='create database {}'.format(dname)
        curobj.execute(q1)
    elif Q=='y':
        dbn=input("Enter the Database name: ")
        q1='use '+dbn
        curobj.execute(q1)
    else:
        print("Inavalid Choice..")
    
def createtb():
    db=input("enter the database name: ")
    sql1='use {}'.format(db)
    curobj.execute(sql1)
    tb=input("enter the table name: ")
    col=int(input("enter the number of columns: "))
    sql='create table '+tb+'('
    for i in range(col):
        colname=input("enter the column name: ")
        print('''
                1.NUM
                2.Alphabets
                3.Date
                4.Decimal
            ''')
        datatype=input("enter the datatype[num,a lpabets,date,decimal]: ")
        if datatype=='1':
            datatype='INT'
        elif datatype=='2':
            datatype='VARCHAR'
        elif datatype=='3':
            datatype='DATE'
        elif datatype=='4':
            datatype='DECIMAL'
        else:
            print('Invalid Choice!')
        constraint=input("enter the constraint[blanks space for none]: ")
        size = ''
        if datatype=='DECIMAL':
            x=int(input("enter the characters before decimal point: "))
            y=int(input("enter the characters after decimal point: "))
            size=str(x)+","+str(y)
        elif datatype=='DATE':
            # DATE type does not need a size
            size = ''
        else:
            size=input("enter the lenghth of the column: ")
        # build column definition depending on whether size is needed
        if size:
            col_def = f"{colname} {datatype}({size}) {constraint}".strip()
        else:
            col_def = f"{colname} {datatype} {constraint}".strip()
        # append column definition
        if sql.endswith('('):
            sql += col_def + ','
        else:
            sql += col_def + ','
    sql = sql.rstrip(',') + ')'
    print(sql)
    try:
        curobj.execute(sql)
        con.commit()
        print('New table created')
    except Exception as e:
        print("ERROR:", e)
def showtb():
    db=input("enter the database name: ")
    sql1='use {}'.format(db)
    curobj.execute(sql1)
    sql="Show tables"
    curobj.execute(sql)
    tbn=curobj.fetchall()
    s1=pd.DataFrame(tbn)
    print('''===================================
            Tables=''',list(s1['Tables_in_'+db])
            ,'===================================')
    #print(s1)
def insert():
    db=input("enter the database name: ")
    sql1='use {}'.format(db)
    curobj.execute(sql1)
    sql3='show tables'
    curobj.execute(sql3)
    result=curobj.fetchall()
    df=pd.DataFrame(result)
    colname=list(df['Tables_in_'+db])
    print('Tables=',colname)
    tbn=input("enter the table name: ")
    sql2='desc {}'.format(tbn)
    curobj.execute(sql2)
    result=curobj.fetchall()
    df=pd.DataFrame(result)
    colname=list(df['Field'])
    sql='insert into '+tbn+' values('
    for i in colname:
        x = input(i+':')
        sql += "'"+x+"',"
    sql = sql[:-1]
    sql += ')'
    print(sql)
    try:
        curobj.execute(sql)
        con.commit()
    except Exception as e:
        print("ERROR:", e)
def selectall():
    db=input("enter the database name: ")
    sql1='use {}'.format(db)
    curobj.execute(sql1)
    #db=input("enter the database name: ")
    #sql1='use {}'.format(db)
    #curobj.execute(sql1)
    sql="Show tables"
    curobj.execute(sql)
    tbnd=curobj.fetchall()
    s1=pd.DataFrame(tbnd)
    print('''Tables=''',list(s1['Tables_in_'+db]))
    tbn=input("enter the table name: ")
    
    sql='select * from {}'.format(tbn)
    curobj.execute(sql)
    record=curobj.fetchall()
    result=pd.DataFrame(record)
    print(result)
    
    '''
    sql1="SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = N'{}'".format(tbn)
    print(sql1)
    curobj.execute(sql1)
    column=curobj.fetchall()
    result.columns=column
    result.index.name='S.no'
    #a=len(result.index)
    #result.index=list(np.arange(1,a))
    #result.columns=curobj.keys()
    #print('roll \t\t name \t\t class')
    print(result)
    '''
def selectcon():
    db=input("enter the database name: ")
    sql1='use {}'.format(db)
    curobj.execute(sql1)
    tbn=input("enter the table name: ")
    print("Table selected")
    coln=int(input("enter the number of columns: "))
    x=''
    for i in range(coln):
        x +=input("enter the name of the column: ")+","
    x=x[:-1]
    sql='Select '+x
    
    #if coln==1:
        #sql=sql[:-1]
    sql=sql +' from {}'.format(tbn)
    curobj.execute(sql)
    record=curobj.fetchall()
    result=pd.DataFrame(record)
    print(result)
    
def export():
    db=input("enter the Database Name: ")
    sql='use {}'.format(db)
    curobj.execute(sql)
    tbn=input("enter the table name: ")
    sql='select * from {}'.format(tbn)
    curobj.execute(sql)
    record=curobj.fetchall()
    result=pd.DataFrame(record)
    # write to CSV file named after the table
    try:
        filename = input('Enter filename to save CSV (leave blank to use table name): ').strip()
        if not filename:
            filename = f"{tbn}.csv"
        result.to_csv(filename, index=False)
        print(f"Exported to {filename}")
    except Exception as e:
        print('Export error:', e)
def alter():
    db=input("enter the database name: ")
    sql='use {}'.format(db)
    curobj.execute(sql)
    print(" 1.Add Column")
    print(" 2.Drop Column")
    print(" 3.Modify Column")
    print(" 4.Rename Column")
    ch1=input("enter the valid choice: ")
    if ch1=='1':
        tbn=input("enter the table name: ")
        col=input("enter the column name: ")
        dt=input("enter the column type[int,varchar,char etc]: ")
        constraint=input("enter the constraint[leave blank if not any]: ")
        ln=input("enter the length of columns: ")
        sql='Alter table '+tbn+' add column '+col+' '+dt+'('+ln+')'+constraint
        print(sql)
        curobj.execute(sql)
        con.commit()
    elif ch1=='2':
        tbn=input("enter the table name: ")
        col=input("enter the column name: ")
        sql='Alter table '+tbn+' drop column '+col
        print(sql)
        curobj.execute(sql)
        con.commit()
    elif ch1=='3':
        tbn=input("enter the table name: ")
        col1=input("enter the column name: ")
        dt=input("enter the column type[int,varchar,char etc]: ")
        ln=input("enter the length of columns: ")
        sql='Alter table '+tbn+' modify '+col1+' '+dt+'('+ln+')'
        print(sql)
        curobj.execute(sql)
        con.commit()
    elif ch1=='4':
        tbn=input("enter the table name: ")
        col1=input("enter the column name: ")
        col2=input("enter the new column name: ")
        dt=input("enter the new datatype for the column: ")
        size=input("enter the size of the column: ")
        sql='ALTER TABLE '+tbn+' Change '+col1+" "+col2+" "+dt+'('+size+')'
        print(sql)
        curobj.execute(sql)
        con.commit()
    else:
        print('invalid choice')
        main()
def update():
    db=input("enter the database name: ")
    sql='use {}'.format(db)
    curobj.execute(sql)
    tbn=input("enter the table name: ")
    col1=input("enter the column name to update: ")
    val=input("enter the value for the column: ")
    col=input("enter the primary key name in the column: ")
    val2=input("enter the values in the column: ")
    sql='Update '+tbn+' set '+col1+' = '+'"'+val+'"'+' where '+col+'='+val2
    print(sql)
    curobj.execute(sql)
    con.commit()
def desctb():
    db=input("enter the database name: ")
    sql='use {}'.format(db)
    curobj.execute(sql)
    tbn=input("enter the table name: ")
    sql='desc {}'.format(tbn)
    curobj.execute(sql)
    result=curobj.fetchall()
    df=pd.DataFrame(result)
    print(df)
def droptb():
    db=input("enter the database name: ")
    sql='use {}'.format(db)
    curobj.execute(sql)
    tbn=input("enter the table name: ")
    sql='DROP TABLE {}'.format(tbn)
    print(sql)
    curobj.execute(sql)
    con.commit()
    print("Table successfully Deleted...")
def plot():
    db=input("enter the database name: ")
    sql1='use {}'.format(db)
    curobj.execute(sql1)
    tbn=input("enter the table name: ")
    sql='select * from {}'.format(tbn)
    curobj.execute(sql)
    record=curobj.fetchall()
    result=pd.DataFrame(record)
    column=list(result.columns)
    print('Column Names:',column)
    bartype=input("Enter the bar Type[Bar,Line]: ").lower()
    title=input("enter the title for graph: ")
    x_axis=input("enter the x-axis column name: ")
    y_axis=input("enter the y-axis column name: ")
    colors=input("enter the Bar colours: ")
    x=result[x_axis].tolist()
    y=result[y_axis].tolist()
    plt.title(title)
    if bartype=='bar':
        outline=input('enter the outline color: ')
        plt.bar(x,y,color=colors,width=0.5,edgecolor=outline)
    elif bartype=='line':
        plt.plot(x,y,color=colors)
    else:
        print("Invalid Choice...")
    plt.xlabel(x_axis)
    plt.ylabel(y_axis)
    plt.xticks(x)
    ymin=int(input("enter the minimum y-axis value: "))
    ymax=int(input("enter the maximum y-axis value: "))
    yinter=int(input("enter the interval of y-axis: "))
    plt.yticks(np.arange(ymin,ymax,yinter))
    plt.show()
def dropdb(): 
    db=input("enter the database name to delete: ")
    sql='drop database '+db
    curobj.execute(sql)
    con.commit()
    print("Database Successfully Deleted...")
main()

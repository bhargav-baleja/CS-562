# Authors: Bhargav Baleja and Vishal Manjunath

# Dependencies: Ensure sure that the py-postgresql, and PrettyTable modules are installed, the dbConfig dictionary in the 
# databaseConfig.py file is updated with the credentials needed to connect to your database. A sql file to create the sales table
# is also needed to run this program. This file must be named 'sdap.sql' and contain rows for the sales table as described in the
# project document.

# Starting the Program: Type 'python main.py' and the program will begin executing.

# Running the Program: When the program is run, the terminal will prompt the user to input a file name or the phi operator variables
# inline. The input will then be processed and will generate an algorithm corresponding to the type of query specified by the
# user input.

# Output: The program will output to a file called 'algorithm.py', which can be run without input to return a table of the output
# for the query. The program will also add all rows from 'sdap.sql' into your database into the 'sales' table.

import psycopg2
from databaseConfig import dbConfig
from sqlQuery import sqlQuery
from mfQueries import mfQuery
from emfQueries import emfQuery

# Create connection to database
conn = psycopg2.connect(
    user = dbConfig["user"],
    password = dbConfig["password"],
    host = dbConfig["host"],
    port = dbConfig["port"],
    database = dbConfig["database"],
)

db = conn.cursor()

db.execute("SELECT VERSION();")
version = db.fetchone()
print("Connected into - ", version)

# Run sql file to initialize database with sales table defined in sdap.sql
initializeFile = open("sdap.sql")
for line in initializeFile:
    db.execute(line)

conn.commit()

# Receive Input
inputType = input("Please enter the name of the file which you would like to read, or enter nothing to input the variables inline: ")
selectAttributes = ""
groupingVarCount = ""
groupingAttributes = ""
fVect = ""
predicates = ""
havingCondition = ""

if inputType != "":
    with open(inputType) as f:
        content = f.readlines()
    content = [x.rstrip() for x in content]
    i = 0
    while i < len(content):
        if(content[i] == "SELECT ATTRIBUTE(S):"):
            i += 1
            selectAttributes = content[i].replace(" ", "")
            i += 1
        elif(content[i] == "NUMBER OF GROUPING VARIABLES(n):"):
            i += 1
            groupingVarCount = content[i].replace(" ", "")
            i += 1
        elif(content[i] == "GROUPING ATTRIBUTES(V):"):
            i += 1
            groupingAttributes = content[i].replace(" ", "")
            i += 1
        elif(content[i] == "F-VECT([F]):"):
            i += 1
            fVect = content[i].replace(" ", "")
            i += 1
        elif(content[i] == "SELECT CONDITION-VECT([Ïƒ]):"):
            i += 1
            predicates = content[i]
            i += 1
        elif(content[i] == "HAVING_CONDITION(G):"): 
            i += 1     
            havingCondition = content[i]
            i += 1
        else:
            predicates += "," + content[i]
            i += 1
    #trim input of whitespace
    selectAttributes = selectAttributes.replace(" ", "")
    groupingVarCount = groupingVarCount.replace(" ", "")
    groupingAttributes = groupingAttributes.replace(" ", "")
    fVect = fVect.replace(" ", "")
    predicates = predicates #white space needed to evaluate each predicate statment 
    havingCondition = havingCondition #white space needed to evaluate each having condition
    print(predicates)
else:
    #read inline
    selectAttributes = input("Please input the select attributes seperated by a comma: ").replace(" ", "")
    groupingVarCount = input("Please input the number of grouping variables: ").replace(" ", "")
    groupingAttributes = input("Please input the grouping attribute(s). If more than one, seperate with commas: ").replace(" ", "")
    fVect = input("Please input the list of aggregate functions for the query seperated by a comma: ").replace(" ", "")
    predicates = input("Please input the predicates that define the range of the grouping variables seperated by a comma. Each predicate must have each element sperated by a space: ")
    havingCondition = input("Please input the having condition with each element seperated by spaces, and the AND and OR written in lowercase: ")

print("selectAttributes = ",selectAttributes,"\n","groupingVarCount = ",groupingVarCount,"\n","groupingAttributes = ",groupingAttributes,"\n","fVect = ",fVect,"\n","predicates = ",predicates,"\n","havingCondition = ",havingCondition)
#initalizing algorithmFile with needed modules, database connection, input variables, and empty MF Struct
with open('algorithm.py', 'w') as algorithmFile: # opens file to write algorithm to
    algorithmFile.write("import psycopg2\nfrom databaseConfig import dbConfig\nfrom prettytable import PrettyTable\n\n") #import modules
    algorithmFile.write(f"""selectAttributes = "{selectAttributes}"\ngroupingVarCount = {groupingVarCount}\ngroupingAttributes = "{groupingAttributes}"\nfVect = "{fVect}"\npredicates = "{predicates}"\nhavingCondition = "{havingCondition}"\n""") #write input variables to file
    algorithmFile.write("MF_Struct = {}\n") #initalize empty MF Struct
    algorithmFile.write("conn = psycopg2.connect(user = dbConfig['user'],password = dbConfig['password'],host = dbConfig['host'],port = dbConfig['port'],database = dbConfig['database'],)\n\n")
    algorithmFile.write("db = conn.cursor()\ndb.execute('SELECT * FROM sales;')\nquery = db.fetchall()\n") #connect to DB and query sales table to loop through row by row during evaluation of MF Struct
    
    #after initalizing the file, the groupingVarCount, and predicates are examined to determine which algorithm to use: 
    mf = 1 #flag to tell if a query is an MF Query
    if groupingVarCount == '0': #If no grouping variables, evaluate as a regular SQL Query
        mf = 0 #set flag to 0 as the query is not an MF Query
        algorithmFile.write("\n\n# Algorithm for basic SQL Query:\n")
        algorithmFile.close() #close file before passing to sqlQuery function
        sqlQuery() #calls sqlQuery function which will write the appropriate algorithm to the algorithm.py file
    
    for pred in predicates.split(','): #loop through the list of predicate statments to see if there is a grouping attribute referenced that is not attributed to a grouping variable
        if(mf): #if the query has not been found to be a EMF or SQL Query, continue checking
            for string in pred.split(' '): #for each element of the predicate statment,
                if(string in groupingAttributes.split(',')): #if there is a grouping attribute in the predicate statment, the query is an EMF Query
                    mf = 0 #Query is an EMF Query, update flag
                    algorithmFile.write("\n\n# Algorithm for EMF Query:\n")
                    algorithmFile.close()
                    emfQuery() #calls emfQuery function to write the appropriate algorithm to the algorithm.py file
                    break #if the query is an EMF Query, break out of the loop
        else: 
            break #break out of the loop if the query was found to be an SQL or EMF Query
    if(mf): # If query isn't a basic SQL query or an EMF query, evaluate as an MF Query
        algorithmFile.write("\n\n# Algorithm for MF Query:\n")
        algorithmFile.close()
        mfQuery() #calls mfQuery function to write the appropriate algorithm to the algorithm.py file
conn.close()
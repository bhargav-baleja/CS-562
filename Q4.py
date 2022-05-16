import psycopg2
from databaseConfig import dbConfig
from prettytable import PrettyTable

selectAttributes = "cust,1_sum_quant,1_avg_quant,1_max_quant,1_min_quant,1_count_quant"
groupingVarCount = 1
groupingAttributes = "cust"
fVect = "1_sum_quant,1_avg_quant,1_max_quant,1_min_quant,1_count_quant"
predicates = "1.state = 'NY' and 1.cust = cust"
havingCondition = ""
MF_Struct = {}
conn = psycopg2.connect(user = dbConfig['user'],password = dbConfig['password'],host = dbConfig['host'],port = dbConfig['port'],database = dbConfig['database'],)

db = conn.cursor()
db.execute('SELECT * FROM sales;')
query = db.fetchall()


# Algorithm for EMF Query:

#Function for setting attribute value according to the input provided
def getAttributesValue(attr): 
	if attr == "cust":
		flag = 0
	elif attr == "prod":
		flag = 1
	elif attr == "day":
		flag = 2
	elif attr == "month":
		flag = 3
	elif attr == "year":
		flag = 4
	elif attr == "state":
		flag = 5
	elif attr == "quant":
		flag = 6
	else:
		flag = 7
	
	return flag

predicates = predicates.split(',') #splits predicates by each predicate statment and creates list to store the parts of each predicate in a single 2D array
pList = []

for i in predicates:
	pList.append(i.split(' '))

for i in range(int(groupingVarCount)+1):
    # 0th pass of the algorithm, where each row of the MF Struct is initalized for every unique group based on the grouping variables.
    # Each row in the MF struct also has its columns initalized appropriately based on the aggregates in the F-Vect
	if i == 0:
		for row in query:
			key = ''
			value = {}
			
			for attr in groupingAttributes.split(','):
				flag = getAttributesValue(attr) 
				key += f'{str(row[flag])},'
			key = key[:-1]
			
			if key not in MF_Struct.keys():
				for groupAttr in groupingAttributes.split(','):
					flag = getAttributesValue(groupAttr) 
					colVal = row[flag]
					
					if colVal:
						value[groupAttr] = colVal
				for fVectAttr in fVect.split(','):
                    # Average is saved as an object with the sum, count, and overall average
					if (fVectAttr.split('_')[1] == 'avg'):
						value[fVectAttr] = {'sum':0, 'count':0, 'avg':0}
                    # Min is initialized as 1000, which is the largest value of 'quant' in the sales table. This allows the first value that the algorithm comes across will be saved as the min (except the row with quant=4994)
					elif (fVectAttr.split('_')[1] == 'min'):
						value[fVectAttr] = 1000
					else:
						value[fVectAttr] = 0
				MF_Struct[key] = value
	else:
        # Begin n passes for each of the n grouping variables
		for aggregate in fVect.split(','):
			aggList = aggregate.split('_')
			groupVar = aggList[0]
			aggFunc = aggList[1]
			aggCol = aggList[2]
            
			# Check to make sure the aggregate function is being called on the grouping variable you are currently on (i)
            # Also loop through every key in the MF_Struct to update every row of the MF_Struct the predicate statments apply to(1.state = state and 1.cust = cust vs 1.state = state)
			if i == int(groupVar):
				for row in query:
					for key in MF_Struct.keys():
						if aggFunc == 'sum':
							evalString = predicates[i-1]
                            
							# Creates a list1 to be run with the eval() method by replacing grouping variables with their actual values
                            # Since it's an EMF query, it must also check if the list1 is a grouping variable and replace that with the actual value from the table row as well
							for list1 in pList[i-1]:
								if len(list1.split('.')) > 1 and list1.split('.')[0] == str(i):
									new_string = list1.split('.')[1]
									flag = getAttributesValue(new_string)
									rowVal = row[flag]
									
									try:
										int(rowVal)
										evalString = evalString.replace(list1, str(rowVal))
									except:
										evalString = evalString.replace(list1, f"'{rowVal}'")
								elif list1 in groupingAttributes.split(','):
									rowVal = MF_Struct[key][list1]
									
									try:
										int(rowVal)
										evalString = evalString.replace(list1, str(rowVal))
									except:
										evalString = evalString.replace(list1, f"'{rowVal}'")
                            # If evalString is true, update the sum
							if eval(evalString.replace('=', '==')):
								flag = getAttributesValue(aggCol)
								sum = int(row[flag])
								MF_Struct[key][aggregate] += sum
						elif aggFunc == 'avg':
							sum = MF_Struct[key][aggregate]['sum']
							count = MF_Struct[key][aggregate]['count']
							evalString = predicates[i-1]
							
							for list1 in pList[i-1]:
								if len(list1.split('.')) > 1 and list1.split('.')[0] == str(i):
									new_string = list1.split('.')[1]
									flag = getAttributesValue(new_string)
									rowVal = row[flag]
									
									try:
										int(rowVal)
										evalString = evalString.replace(list1, str(rowVal))
									except:
										evalString = evalString.replace(list1, f"'{rowVal}'")
								elif list1 in groupingAttributes.split(','):
									rowVal = MF_Struct[key][list1]
									
									try:
										int(rowVal)
										evalString = evalString.replace(list1, str(rowVal))
									except:
										evalString = evalString.replace(list1, f"'{rowVal}'")
                            
							# If evalString is true and count isn't 0, update the avg
							if eval(evalString.replace('=', '==')):
								flag = getAttributesValue(aggCol)
								sum += int(row[flag])
								count += 1
								
								if count != 0:
									MF_Struct[key][aggregate] = {'sum': sum, 'count': count, 'avg': (sum/count)}
						elif aggFunc == 'min':
							evalString = predicates[i-1]
							
							for list1 in pList[i-1]:
								if len(list1.split('.')) > 1 and list1.split('.')[0] == str(i):
									new_string = list1.split('.')[1]
									flag = getAttributesValue(new_string)
									rowVal = row[flag]
									
									try:
										int(rowVal)
										evalString = evalString.replace(list1, str(rowVal))
									except:
										evalString = evalString.replace(list1, f"'{rowVal}'")
								elif list1 in groupingAttributes.split(','):
									rowVal = MF_Struct[key][list1]
									
									try:
										int(rowVal)
										evalString = evalString.replace(list1, str(rowVal))
									except:
										evalString = evalString.replace(list1, f"'{rowVal}'")
                            # If evalString is true, update the min
							if eval(evalString.replace('=', '==')):
								min = int(MF_Struct[key][aggregate])
								flag = getAttributesValue(aggCol)
								
								if int(row[flag]) < min:
									MF_Struct[key][aggregate] = row[flag]
						elif aggFunc == 'max':
							evalString = predicates[i-1]
							
							for list1 in pList[i-1]:
								if len(list1.split('.')) > 1 and list1.split('.')[0] == str(i):
									new_string = list1.split('.')[1]
									flag = getAttributesValue(new_string)
									rowVal = row[flag]
									
									try:
										int(rowVal)
										valString = evalString.replace(list1, str(rowVal))
									except:
										evalString = evalString.replace(list1, f"'{rowVal}'")
								elif list1 in groupingAttributes.split(','):
									rowVal = MF_Struct[key][list1]
									
									try:
										int(rowVal)
										valString = evalString.replace(list1, str(rowVal))
									except:
										evalString = evalString.replace(list1, f"'{rowVal}'")
                            # If evalString is true, update the max
							if eval(evalString.replace('=', '==')):
								max = int(MF_Struct[key][aggregate])
								flag = getAttributesValue(aggCol)
								
								if int(row[flag]) > max:
									MF_Struct[key][aggregate] = row[flag]
						elif aggFunc == 'count':
							evalString = predicates[i-1]
							
							for list1 in pList[i-1]:
								if len(list1.split('.')) > 1 and list1.split('.')[0] == str(i):
									new_string = list1.split('.')[1]
									flag = getAttributesValue(new_string)
									rowVal = row[flag]
									
									try:
										int(rowVal)
										evalString = evalString.replace(list1, str(rowVal))
									except:
										evalString = evalString.replace(list1, f"'{rowVal}'")
								elif list1 in groupingAttributes.split(','):
									rowVal = MF_Struct[key][list1]
									
									try:
										int(rowVal)
										evalString = evalString.replace(list1, str(rowVal))
									except:
										evalString = evalString.replace(list1, f"'{rowVal}'")
                            # If evalString is true, increment the count
							if eval(evalString.replace('=', '==')):
								MF_Struct[key][aggregate] += 1

#Generate output table(also checks the HAVING condition)
output = PrettyTable()
output.field_names = selectAttributes.split(',')

for row in MF_Struct:
    #create an evalString to be used to check each having condition
	evalString = ''
	
	if havingCondition != '':
		for list1 in havingCondition.split(' '):
            #if there is a having condition, loop through each element of the having condition to fill in the correct information into the evalString
            #the eval list1 will be equal to the having condition, replaced with the values of the variables in question, 
            #then evaluated to check if the row of the MFStruct being examined is to be included in the output table
			if list1 not in ['>', '<', '==', '<=', '>=', 'and', 'or', 'not', '*', '/', '+', '-']:
				try:
					float(list1)
					evalString += list1
				except:
					if len(list1.split('_')) > 1 and list1.split('_')[1] == 'avg':
						evalString += str(MF_Struct[row][list1]['avg'])
					else:
						evalString += str(MF_Struct[row][list1])
			else:
				evalString += f' {list1} '
		
		if eval(evalString.replace('=', '==')):
			row_info = []
			
			for val in selectAttributes.split(','):
				if len(val.split('_')) > 1 and val.split('_')[1] == 'avg':
					row_info += [str(MF_Struct[row][val]['avg'])]
				else:
					row_info += [str(MF_Struct[row][val])]
			output.add_row(row_info)
		evalString = ''
	else:
        #there is no having condition, thus every MFStruct row will be added to the output table
		row_info = []
		
		for val in selectAttributes.split(','):
			if len(val.split('_')) > 1 and val.split('_')[1] == 'avg':
				row_info += [str(MF_Struct[row][val]['avg'])]
			else:
				row_info += [str(MF_Struct[row][val])]
		output.add_row(row_info)

print(output)
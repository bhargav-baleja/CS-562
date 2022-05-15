function = """
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

predicates = predicates.split(',')
pList = []
#splits predicates by each predicate statment and creates list to store the parts of each predicate in a single 2D array
for i in predicates:
	pList.append(i.split(' '))
for i in range(int(groupingVarCount)+1): # loop through the table to evaluate each grouping variable
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
					if (fVectAttr.split('_')[1] == 'avg'):
                        # Average is saved as an object with the sum, count, and overall average
						value[fVectAttr] = {'sum':0, 'count':0, 'avg':0}
					elif (fVectAttr.split('_')[1] == 'min'):
                        # Min is initialized as 4994, which is the largest value of 'quant' in the sales table.
                        # This allows the first value that the algorithm comes across will be saved as the min (except the row with quant=4994)
						value[fVectAttr] = 1000 # Max quant in sales table
					else:
                        # Initalize values of count, sum and max to 0
						value[fVectAttr] = 0
				MF_Struct[key] = value #add row into MF Struct
	else: #The other n passes for each grouping variable 
			for aggregate in fVect.split(','):
				aggList = aggregate.split('_')
				groupVar = aggList[0]
				aggFunc = aggList[1]
				aggCol = aggList[2]
                # Check to make sure the aggregate function is being called on the grouping variable you are currently on (i)
				if i == int(groupVar):
					for row in query:
						key = ''
						for attr in groupingAttributes.split(','):
							flag = getAttributesValue(attr)
							key += f'{str(row[flag])},'
						key = key[:-1]
						if aggFunc == 'sum':
                            # Creates a list1 to be run with the eval() method by replacing grouping variables with their actual values
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
                            # If evalString is true, update the sum
							if eval(evalString.replace('=','==')):
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
                            # If evalString is true and count isn't 0, update the avg
							if eval(evalString.replace('=','==')):
								flag = getAttributesValue(aggCol)
								sum += int(row[flag])
								count += 1
								if count != 0:
									MF_Struct[key][aggregate] = {'sum': sum, 'count': count, 'avg': (sum/count)}
						elif aggFunc == 'min':
							# check if row meets predicate requirements
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
                            # If evalString is true, update the min
							if eval(evalString.replace('=','==')):
								min = int(MF_Struct[key][aggregate])
								flag = getAttributesValue(aggCol)
								if int(row[flag]) < min:
									MF_Struct[key][aggregate] = row[flag]
						elif aggFunc == 'max':
							# check if row meets predicate requirements
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
                            # If evalString is true, update the max
							if eval(evalString.replace('=','==')):
								max = int(MF_Struct[key][aggregate])
								flag = getAttributesValue(aggCol)
								if int(row[flag]) > max:
									MF_Struct[key][aggregate] = row[flag]
						elif aggFunc == 'count':
							# check if row meets predicate requirements
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
							if eval(evalString.replace('=','==')): # If evalString is true, increment the count
								MF_Struct[key][aggregate] += 1
#Generate output table(also checks the HAVING condition)
output = PrettyTable()
output.field_names = selectAttributes.split(',')
for row in MF_Struct:
	evalString = ''
	if havingCondition != '':
        #if there is a having condition, loop through each element of the having condition to fill in the correct information into the evalString
        #the eval list1 will be equal to the having condition, replaced with the values of the variables in question,
        # then evaluated to check if the row of the MFStruct being examined is to be included in the output table
		for list1 in havingCondition.split(' '):
			if list1 not in ['>', '<', '==', '<=', '>=', 'and', 'or', 'not', '*', '/', '+', '-']:
				try:
					int(list1)
					evalString += list1
				except:
					if len(list1.split('_')) > 1 and list1.split('_')[1] == 'avg':
						evalString += str(MF_Struct[row][list1]['avg'])
					else:
						evalString += str(MF_Struct[row][list1])
			else:
				evalString += f' {list1} '
		if eval(evalString.replace('=','==')):
			row_info = []
			for val in selectAttributes.split(','):
				if len(val.split('_')) > 1 and val.split('_')[1] == 'avg':
					row_info += [str(MF_Struct[row][val]['avg'])]
				else:
					row_info += [str(MF_Struct[row][val])]
			output.add_row(row_info)
		evalString = ''
	else:
        #there is no having condition, thus every MFStruct row will be in the output table
		row_info = []
		for val in selectAttributes.split(','):
			if len(val.split('_')) > 1 and val.split('_')[1] == 'avg':
				row_info += [str(MF_Struct[row][val]['avg'])]
			else:
				row_info += [str(MF_Struct[row][val])]
		output.add_row(row_info)
print(output) #Pretty table corresponding to evaluation of query
"""
def mfQuery():
    with open('algorithm.py', 'a') as algorithmFile:
        algorithmFile.write(function)
        algorithmFile.close()
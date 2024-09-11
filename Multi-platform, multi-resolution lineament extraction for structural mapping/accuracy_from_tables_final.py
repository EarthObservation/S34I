import arcpy
import numpy as np
import os
import pandas as pd

import tkinter as tk
from tkinter import filedialog
from tkinter.filedialog import asksaveasfile
import csv
from functools import reduce


###### This part of the script is applied when both vectors - Ground Truth (Contacts) and Measured (Extracted Lineaements) - are 
###### inside the search radius 

root = tk.Tk()
root.withdraw()

root.attributes('-topmost',True) 

file_path_1 = filedialog.askopenfilename(parent=root, title='Choose __contacts_measured')

Contacts_Measured = pd.read_csv(file_path_1,
                 sep=',',
                 engine='python')

 

result_Contacts_Measured = Contacts_Measured.drop_duplicates(subset=['IN_FID'])
arr_Contacts_Measured_0 = result_Contacts_Measured[['IN_FID']].to_numpy()
#print(arr_Contacts_Measured)
print(len(arr_Contacts_Measured_0))
print(arr_Contacts_Measured_0)

############# The code below Takes the Contacts_Measured_Join_Quadrant as input to calculated the True Positives. True positives are  
############# considered to be the random_points (random sampling points) where the Ground Truth (Contacts) and Measured (Extracted Lineaements)
############# are present on the search radius and have a matching azimuth in at least one of the line segments.


Contacts_Measured_Az_Match = Contacts_Measured[Contacts_Measured['Az_Match'] == 1] 
print(Contacts_Measured_Az_Match)
result_Contacts_Measured = Contacts_Measured_Az_Match.drop_duplicates(subset=['IN_FID'])
arr_Contacts_Measured = result_Contacts_Measured[['IN_FID']].to_numpy()
#print(arr_Contacts_Measured)
print(arr_Contacts_Measured)
TP=len(arr_Contacts_Measured)
print("The number of TP is: " + str(TP))


############# The code below Takes the Contacts_Measured_Join_Quadrant as input to calculated a part of the False Negatives. This part of False Negatives are  
############# considered to be the random_points (random sampling points) where the Ground Truth (Contacts) and Measured (Extracted Lineaements)
############# are present on the search radius and don't have a matching azimuth in all the line segments.

Contacts_Measured_Az_Match_1 = Contacts_Measured[Contacts_Measured['Az_Match'] == 0] 
#print(Contacts_Measured_Az_Match_1)
result_Contacts_Measured_1 = Contacts_Measured_Az_Match_1.drop_duplicates(subset=['IN_FID'])
arr_Contacts_Measured_1 = result_Contacts_Measured_1[['IN_FID']].to_numpy()
#print(arr_Contacts_Measured_1)
print(arr_Contacts_Measured_1)
print(len(arr_Contacts_Measured_1))

intersect=np.intersect1d(arr_Contacts_Measured,arr_Contacts_Measured_1)
print(intersect)
FN_1_arr=np.setdiff1d(arr_Contacts_Measured_1,intersect)
print(FN_1_arr)
FN_1=len(arr_Contacts_Measured_1)-len(intersect)
print("FN_1:"+str(FN_1))


###### This part of the code reads the Contactos_Vert  to determine which random_points have  ground truth line segments inside the search radius.


root = tk.Tk()
root.withdraw()
root.attributes('-topmost',True) 

file_path_2 = filedialog.askopenfilename(parent=root, title='Choose __contacts_vert')

Contacts = pd.read_csv(file_path_2,
                 sep=',',
                 engine='python')

result_Contacts = Contacts.drop_duplicates(subset=['IN_FID'])
arr_Contacts = result_Contacts[['IN_FID']].to_numpy()
#print(arr_Contacts_Measured)
#print(arr_Contacts)
#print(len(arr_Contacts))


###### This part of the code reads the Measured_Vert  to determine which random_points have  Extracted lineaments line segments inside the search radius.



root = tk.Tk()
root.withdraw()
root.attributes('-topmost',True) 

file_path_3 = filedialog.askopenfilename(parent=root, title='Choose __measured_vert')

Measured = pd.read_csv(file_path_3,
                 sep=',',
                 engine='python')

result_Measured = Measured.drop_duplicates(subset=['IN_FID'])
arr_Measured = result_Measured[['IN_FID']].to_numpy()
#print(arr_Contacts_Measured)
#print(arr_Measured)
#print(len(arr_Measured))


##### Calculates intersection between Measured_Vert and Contacts_Vert


intersect=np.intersect1d(arr_Contacts,arr_Measured)

#print(intersect)
#print(len(intersect))

FN_2 = len(arr_Measured) - len(intersect)
FN=FN_1 + FN_2




###### Random points to check the True negatives

root = tk.Tk()
root.withdraw()
root.attributes('-topmost',True) 

file_path_4 = filedialog.askopenfilename(parent=root, title='Choose __random_points')

Random_Points = pd.read_csv(file_path_4,
                 sep=',',
                 engine='python')

 
#print(Random_Points)
Random_Points_TN = Random_Points[Random_Points['NEAR_ANGLE'] == 0] 
#print(Contacts_Measured_Az_Match)
random_points_arr = Random_Points_TN[['OID_']].to_numpy()
#print(random_points_arr)
#print(arr_Contacts_Measured)

TN_1=np.intersect1d(random_points_arr,arr_Measured)
TN_2=np.intersect1d(random_points_arr,arr_Contacts)

#print(TN_1)
#print(TN_2)

TN_1_1=np.intersect1d(TN_1,TN_2)

#print(TN_1_1)


TN=len(random_points_arr)-(len(TN_1)+len(TN_2))+len(TN_1_1)


###### The code below serves to indicate the other part of False Negatives. From the table it indicates the random_points
###### where the there's only Ground Truth (Contacts) on the search radius. 

dif_contacts_measured=np.setdiff1d(arr_Contacts, arr_Measured)
#print(dif_contacts_measured)
FP_0=len(dif_contacts_measured)
#print("The number of False Positives is:" + str(FP_0))
###### The code below serves to indicate the other part of False Positives. From the table it indicates the random_points
###### where the there's only Ground Truth (Contacts) on the search radius. 
dif_measured_contacts=np.setdiff1d(arr_Measured,arr_Contacts)
#print(dif_measured_contacts)
FP_1=len(dif_measured_contacts)
#print("The number of False _1 is:" + str(FP_1))

false_positive=FP_0-FN_1
#FP=false_positive
false_negative=FN_1+FN_1
#FN=false_negative
FN = FN_1 + FN_2  # Remove the later overwriting of FN
FP = FP_0 + FP_1  # Combine both FP counts without subtracting FN_1

FN=len(dif_contacts_measured)+len(FN_1_arr)
FP=len(dif_measured_contacts)
TP=len(arr_Contacts_Measured)




"""intersect=np.intersect1d(dif_contacts_measured,dif_measured_contacts)
print(intersect)

intersect=np.intersect1d(arr_Contacts_Measured,dif_measured_contacts)
print(intersect)


intersect=np.intersect1d(arr_Contacts_Measured,dif_contacts_measured)
print(intersect)

intersect=np.intersect1d(arr_Contacts_Measured_1,dif_measured_contacts)
print(intersect)


intersect=np.intersect1d(arr_Contacts_Measured_1,dif_contacts_measured)
print(intersect)


intersect=np.intersect1d(FN_1_arr,dif_contacts_measured)
print(intersect)

intersect=np.intersect1d(FN_1_arr,dif_measured_contacts)
print(intersect)

intersect=np.intersect1d(FN_1_arr,arr_Contacts_Measured)
print(intersect)

union=reduce(np.union1d, (dif_contacts_measured,dif_measured_contacts,arr_Contacts_Measured, arr_Contacts_Measured_1,FN_1_arr,random_points_arr))


union_sort=np.sort(union)


arr_500=np.arange(1, 500, 1)

print(len(union_sort))



print(len(arr_500))


dif_500_union= np.setdiff1d(arr_500,union_sort)

print(dif_500_union)
print(len(dif_500_union))

a=dif_contacts_measured
a_1= a.ravel()     
b=dif_measured_contacts
b_1= b.ravel()     

c=arr_Contacts_Measured
c_1= c.ravel()     

d=arr_Contacts_Measured_1
d_1= d.ravel()     

e=FN_1_arr
e_1= e.ravel()     

f=random_points_arr
f_1= f.ravel()     

concatenate_arr= np.concatenate((a_1,b_1,c_1,d_1,e_1,f_1), axis=0)



concatenate_arr_sort=np.sort(concatenate_arr)
print(concatenate_arr_sort)
print(len(concatenate_arr_sort))
unique_rows = np.unique(concatenate_arr_sort, axis=0)
print(unique_rows)
print(len(unique_rows))






print(len(dif_contacts_measured))     
print(len(dif_measured_contacts))
print(len(arr_Contacts_Measured))
print(len(arr_Contacts_Measured_1))
print(len(FN_1_arr))
print(len(random_points_arr))
dif_500_union= np.setdiff1d(arr_500,unique_rows)
print(dif_500_union)
"""




print("The number of TP is:" + str(TP))
print("The number of TN is:" + str(TN))
print("The number of FP is:" + str(FP))
print("The number of FN is:" + str(FN))



Accuracy = (TP+TN)/(TP+TN+FP+FN)
Precision = TP/(TP+FP)
Recall = TP/(TP+FN)
F1_Score = TP/(TP+((FN+FP)/2))
FPR= FP/(FP+TN)
Specificity=TN/(TN+FP)


print("Accuracy:"+ str(Accuracy))
print("Precision:"+str(Precision))
print("Recall:"+str(Recall))
print("F1_Score:"+str(F1_Score))
print("FPR:"+str(FPR))
print("Specificity:"+str(Specificity))

print(TP+TN+FP+FN)

print(file_path_1)
print(file_path_2)
print(file_path_3)
print(file_path_4)


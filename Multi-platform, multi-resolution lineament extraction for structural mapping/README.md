Instructions to use the ArcGis Pro plugin and the python script to determine accuracy.  
=======================================================================================
 

The plugins structural_accuracy_nosplit.pyt and structural_accuracy_split.pyt should be added to the ArcGis Pro environment and used according to previous analysis of the data used. If the extracted lineaments have a small lenght (<50m) in general, the structural_accuracy_nosplit.pyt tool should be used. Otherwise, structural_accuracy_split.pyt should be used.  

The ArcGis Pro plugin uses 4 inputs, 2 determined by the user: 

Input by the user: 

Ground Truth Input: This file contains the lineaments considered to be ground truth, like vectorized geological maps.  It should have line geometry type. The file should be added to the Project’s home geodatabase. 

Extracted Lineaments Input: This file contains the extracted lineaments. It should have line geometry type. The file should be added to the Project’s home geodatabase. 

Input needs to be generated separately: 

Clip area: This polygon sets the working area. It should have polygon geometry type. It should be named clip_area and added to the Project’s home geodatabase. 

Sampling points: This layer contains a set of randomly generated sample points. It can be generated using the “Create Random Points” tool- ArcGis Pro, and use the clip_area polygon as the Constraining Features Class. It should have point geometry type.  It should be named random_points and added to the Project’s home geodatabase. 

After running the script, several files are created on the Project’s home geodatabase. On the next accuracy calculation step, 4 files should be exported as tables: 

* Contactos_Vert; 

* Measured_Vert; 

* Contacts_Measured_Join_Quadrant; 

* random_points. 

The four above mentioned exported tables should be used as input when running the accuracy_from_tables_final.py script. Four user input windows to select the files to be used appear when running the code. The script requires the following python libraries to be installed:  

* pandas;  

* numpy; 

* tkinter; 

* csv; 

* functools. 

 

The script gives the following performance metrics on the terminal: 

* Accuracy; 

* Precision; 

* Recall; 

* F1_Score; 

* FPR; 

* Specificity. 

The output can be copied from the comand line or copied to a log file, as in the example below, where the script runs in the command line and should be given the full path of the script and desired output accuracy.txt location.   

python "..\accuracy_from_tables_final.py"   >>  "..\test.txt" 

 

The > or >> option are are explained below: 

* command > output.txt 

The standard output stream will be redirected to the file only, it will not be visible in the terminal. If the file already exists, it gets overwritten. 

* command >> output.txt 

The standard output stream will be redirected to the file only, it will not be visible in the terminal. If the file already exists, the new data will get appended to the end of the file. 

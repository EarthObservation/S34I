# -*- coding: utf-8 -*-

import arcpy
import shapefile
import random
import csv


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Toolbox"
        self.alias = "toolbox"

        # List of tool classes associated with this toolbox
        self.tools = [Tool]


class Tool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Lineament performance measurement - Line vs Line"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        ####Input Parameters
        params = [
            arcpy.Parameter(
                displayName="Ground Truth - Geology - Mapped",
                name="in_features",
                datatype="GPFeatureLayer",
                parameterType="Required",
                direction="Input"),    

            arcpy.Parameter(
                displayName="Measured - Satelite Lidar",
                name="in_features1",
                datatype="GPFeatureLayer",
                parameterType="Required",
                direction="Input"),  
            
            arcpy.Parameter(
                displayName="Clip Area",
                name="in_features2",
                datatype="GPFeatureLayer",
                parameterType="Required",
                direction="Input"),      
            
            # New parameter for search radius
            arcpy.Parameter(
                displayName="Search Radius (Meters)",
                name="search_radius",
                datatype="GPDouble",
                parameterType="Required",
                direction="Input"
            ),
            
            # New parameter for maximum line segment length
            arcpy.Parameter(
                displayName="Maximum Line Segment Length (Meters)",
                name="max_segment_length",
                datatype="GPDouble",
                parameterType="Optional",
                direction="Input"
            ),
            # Output CSV for Contacts_Measured_Join_Quadrant
            arcpy.Parameter(
                displayName="Contacts Measured Join Quadrant Output CSV",
                name="out_contacts_measured_join",
                datatype="DEFile",
                parameterType="Optional",
                direction="Output"
            ),

            # Output CSV for Contactos_Vert
            arcpy.Parameter(
                displayName="Contactos Vert Output CSV",
                name="out_contactos_vert",
                datatype="DEFile",
                parameterType="Optional",
                direction="Output"
            ),

            # Output CSV for Measured_Vert
            arcpy.Parameter(
                displayName="Measured Vert Output CSV",
                name="out_measured_vert",
                datatype="DEFile",
                parameterType="Optional",
                direction="Output"
            ),

            # Output CSV for Random Points
            arcpy.Parameter(
                displayName="Random Points Output CSV",
                name="out_random_points",
                datatype="DEFile",
                parameterType="Optional",
                direction="Output"
            ),
            arcpy.Parameter(
                displayName="Measured Contacts Join Quadrant Output CSV",
                name="out_measured_contacts_join",
                datatype="DEFile",
                parameterType="Optional",
                direction="Output"
            ),
            arcpy.Parameter(
            displayName="Random Points Input",
            name="random_points_input",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input"
        )
        ]
        
        # Set default values
        params[3].value = 200.0
        params[4].value = 1000.0  # Default max segment length of 1000 meters
        
        return params
    

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return
    def export_to_csv(self, input_features, output_csv):
        """Export feature class to CSV"""
        if not output_csv:
            return

        # Get field names, excluding BLOB or geometry fields
        fields = [field.name for field in arcpy.ListFields(input_features) 
                if field.type not in ['Blob', 'Geometry']]

        # Write to CSV
        with open(output_csv, 'w', newline='', encoding='utf-8', errors='replace') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(fields)

            with arcpy.da.SearchCursor(input_features, fields) as cursor:
                for row in cursor:
                    # Convert any non-string/non-numeric types to string
                    processed_row = [str(item) if item is not None else '' for item in row]
                    csvwriter.writerow(processed_row)

    def execute(self, parameters, messages):
        """The source code of the tool."""
   
        input0 = parameters[0].valueAsText
        input1 = parameters[1].valueAsText
        input2 = parameters[2].valueAsText
        
        # Get the search radius from the user input
        search_radius = parameters[3].valueAsText + " Meters"
        
        # Get max segment length (use default if not provided)
        min_segment_length = parameters[4].value or 1000.0
        out_contacts_measured_join = parameters[5].valueAsText
        out_contactos_vert = parameters[6].valueAsText
        out_measured_vert = parameters[7].valueAsText
        out_random_points = parameters[8].valueAsText
        out_measured_contacts_join = parameters[9].valueAsText
        # New parameter for random points input
        random_points_input = parameters[10].valueAsText

        # Clip the random points input to the clip area
        arcpy.analysis.Clip(
            in_features=random_points_input, 
            clip_features=input2,  # Using the clip area input 
            out_feature_class="random_points"
        )
        arcpy.analysis.Clip(input0, input2, out_feature_class="input0_clipped")
        arcpy.analysis.Clip(input1, input2, out_feature_class="input1_clipped")
        # Initialize with the clipped input
        current_round = 1
        input_features0 = "input0_clipped"
        input_features1 = "input1_clipped"
        
        
        """The source code of the tool."""
    # [Previous parameter setup code remains the same]
    
        while True:
            arcpy.AddMessage(f"\nProcessing round {current_round}")
            segments_to_split = []
            segments_to_keep = []

            # Add length_new field if it doesn't exist
            existing_fields = [f.name for f in arcpy.ListFields(input_features0)]
            if "length_new" in existing_fields:
                arcpy.management.DeleteField(input_features0, "length_new")

            arcpy.management.AddField(
                input_features0,
                field_name="length_new",
                field_type="DOUBLE",
                field_precision=None,
                field_scale=None,
                field_length=None,
                field_alias="",
                field_is_nullable="NULLABLE",
                field_is_required="NON_REQUIRED",
                field_domain=""
            )

            arcpy.management.CalculateGeometryAttributes(
                input_features0, 
                [["length_new", "LENGTH_GEODESIC"]], 
                length_unit="METERS"
            )

            with arcpy.da.SearchCursor(input_features0, ["OID@", "length_new"]) as cursor:
                for row in cursor:
                    length = row[1]
                    if length > min_segment_length:
                        segments_to_split.append(row[0])
                    else:
                        segments_to_keep.append(row[0])

            arcpy.AddMessage(f"Found {len(segments_to_split)} segments above minimum length")
            arcpy.AddMessage(f"Found {len(segments_to_keep)} segments below minimum length")

            if not segments_to_split:
                arcpy.AddMessage("No more segments to split. Processing complete.")
                break

            arcpy.management.MakeFeatureLayer(input_features0, "features_lyr")

            # Process in smaller batches
            batch_size = 100
            all_selected = False
            
            for i in range(0, len(segments_to_split), batch_size):
                batch = segments_to_split[i:i + batch_size]
                where_clause = "OBJECTID IN ({})".format(",".join(str(oid) for oid in batch))
                
                try:
                    arcpy.management.SelectLayerByAttribute(
                        "features_lyr",
                        "NEW_SELECTION" if i == 0 else "ADD_TO_SELECTION",
                        where_clause
                    )
                    all_selected = True
                except arcpy.ExecuteError:
                    arcpy.AddWarning(f"Batch selection failed, trying individual selections")
                    if i == 0:
                        arcpy.management.SelectLayerByAttribute("features_lyr", "CLEAR_SELECTION")
                    for oid in batch:
                        try:
                            where_clause = f"OBJECTID = {oid}"
                            arcpy.management.SelectLayerByAttribute(
                                "features_lyr",
                                "ADD_TO_SELECTION",
                                where_clause
                            )
                            all_selected = True
                        except arcpy.ExecuteError:
                            arcpy.AddWarning(f"Failed to select OID {oid}")
                            continue

            if all_selected:
                long_segments = f"long_segments_{current_round}"
                arcpy.management.CopyFeatures("features_lyr", long_segments)
                
                split_lines = f"split_lines_{current_round}"
                arcpy.management.SplitLine(long_segments, split_lines)
                
                mid_points = f"mid_points_{current_round}"
                arcpy.management.FeatureVerticesToPoints(split_lines, mid_points, "MID")
                
                new_segments = f"new_segments_{current_round}"
                arcpy.management.SplitLineAtPoint(split_lines, mid_points, new_segments)
                
                # Process kept segments
                arcpy.management.SelectLayerByAttribute("features_lyr", "NEW_SELECTION")
                where_clause = "OBJECTID IN ({})".format(",".join(str(oid) for oid in segments_to_keep))
                try:
                    arcpy.management.SelectLayerByAttribute("features_lyr", "NEW_SELECTION", where_clause)
                except arcpy.ExecuteError:
                    arcpy.AddWarning("Batch selection failed for kept segments, trying individual selections")
                    arcpy.management.SelectLayerByAttribute("features_lyr", "CLEAR_SELECTION")
                    for oid in segments_to_keep:
                        try:
                            where_clause = f"OBJECTID = {oid}"
                            arcpy.management.SelectLayerByAttribute(
                                "features_lyr",
                                "ADD_TO_SELECTION",
                                where_clause
                            )
                        except arcpy.ExecuteError:
                            continue
                
                kept_segments = f"kept_segments_{current_round}"
                arcpy.management.CopyFeatures("features_lyr", kept_segments)
                
                merged_output = f"merged_{current_round}"
                arcpy.management.Merge([new_segments, kept_segments], merged_output)
                
                for fc in [long_segments, split_lines, mid_points, new_segments, kept_segments]:
                    if arcpy.Exists(fc):
                        arcpy.management.Delete(fc)
                        
                min_length = float('inf')
                max_length = 0
                with arcpy.da.SearchCursor(merged_output, ["length_new"]) as cursor:
                    for row in cursor:
                        length = row[0]
                        min_length = min(min_length, length)
                        max_length = max(max_length, length)
                
                arcpy.AddMessage(f"After splitting - Minimum segment length: {min_length:.2f}")
                arcpy.AddMessage(f"After splitting - Maximum segment length: {max_length:.2f}")
                
                if arcpy.Exists(input_features0) and input_features0 != "input1_clipped":
                    arcpy.management.Delete(input_features0)
                input_features0 = merged_output
                
            current_round += 1
        
        # Copy final results to output
        arcpy.management.CopyFeatures(input_features0, "final_segments0")
        
        # Clean up fields
        arcpy.management.DeleteField("final_segments0", [
            "ORIG_FID", "ORIG_SEQ", "ORIG_FID_1", "ORIG_SEQ_1", "ORIG_FID_12", "ORIG_SEQ_12",
            "ORIG_FID_12_13", "ORIG_SEQ_12_13", "ORIG_FID_12_13_14", "ORIG_SEQ_12_13_14",
            "ORIG_FID_12_13_14_15", "ORIG_SEQ_12_13_14_15", "ORIG_FID_12_13_14_15_16", "ORIG_SEQ_12_13_14_15_16",
            "ORIG_FID_12_13_14_15_16_17", "ORIG_SEQ_12_13_14_15_16_17"
        ])
        while True:
            arcpy.AddMessage(f"\nProcessing round {current_round}")
            segments_to_split = []
            segments_to_keep = []

            # Add length_new field if it doesn't exist
            existing_fields = [f.name for f in arcpy.ListFields(input_features0)]
            if "length_new" in existing_fields:
                arcpy.management.DeleteField(input_features0, "length_new")

            arcpy.management.AddField(
                input_features1,
                field_name="length_new",
                field_type="DOUBLE",
                field_precision=None,
                field_scale=None,
                field_length=None,
                field_alias="",
                field_is_nullable="NULLABLE",
                field_is_required="NON_REQUIRED",
                field_domain=""
            )

            arcpy.management.CalculateGeometryAttributes(
                input_features1, 
                [["length_new", "LENGTH_GEODESIC"]], 
                length_unit="METERS"
            )

            with arcpy.da.SearchCursor(input_features1, ["OID@", "length_new"]) as cursor:
                for row in cursor:
                    length = row[1]
                    if length > min_segment_length:
                        segments_to_split.append(row[0])
                    else:
                        segments_to_keep.append(row[0])

            arcpy.AddMessage(f"Found {len(segments_to_split)} segments above minimum length")
            arcpy.AddMessage(f"Found {len(segments_to_keep)} segments below minimum length")

            if not segments_to_split:
                arcpy.AddMessage("No more segments to split. Processing complete.")
                break

            arcpy.management.MakeFeatureLayer(input_features1, "features_lyr")

            # Process in smaller batches
            batch_size = 100
            all_selected = False
            
            for i in range(0, len(segments_to_split), batch_size):
                batch = segments_to_split[i:i + batch_size]
                where_clause = "OBJECTID IN ({})".format(",".join(str(oid) for oid in batch))
                
                try:
                    arcpy.management.SelectLayerByAttribute(
                        "features_lyr",
                        "NEW_SELECTION" if i == 0 else "ADD_TO_SELECTION",
                        where_clause
                    )
                    all_selected = True
                except arcpy.ExecuteError:
                    arcpy.AddWarning(f"Batch selection failed, trying individual selections")
                    if i == 0:
                        arcpy.management.SelectLayerByAttribute("features_lyr", "CLEAR_SELECTION")
                    for oid in batch:
                        try:
                            where_clause = f"OBJECTID = {oid}"
                            arcpy.management.SelectLayerByAttribute(
                                "features_lyr",
                                "ADD_TO_SELECTION",
                                where_clause
                            )
                            all_selected = True
                        except arcpy.ExecuteError:
                            arcpy.AddWarning(f"Failed to select OID {oid}")
                            continue

            if all_selected:
                long_segments = f"long_segments_{current_round}"
                arcpy.management.CopyFeatures("features_lyr", long_segments)
                
                split_lines = f"split_lines_{current_round}"
                arcpy.management.SplitLine(long_segments, split_lines)
                
                mid_points = f"mid_points_{current_round}"
                arcpy.management.FeatureVerticesToPoints(split_lines, mid_points, "MID")
                
                new_segments = f"new_segments_{current_round}"
                arcpy.management.SplitLineAtPoint(split_lines, mid_points, new_segments)
                
                # Process kept segments
                arcpy.management.SelectLayerByAttribute("features_lyr", "NEW_SELECTION")
                where_clause = "OBJECTID IN ({})".format(",".join(str(oid) for oid in segments_to_keep))
                try:
                    arcpy.management.SelectLayerByAttribute("features_lyr", "NEW_SELECTION", where_clause)
                except arcpy.ExecuteError:
                    arcpy.AddWarning("Batch selection failed for kept segments, trying individual selections")
                    arcpy.management.SelectLayerByAttribute("features_lyr", "CLEAR_SELECTION")
                    for oid in segments_to_keep:
                        try:
                            where_clause = f"OBJECTID = {oid}"
                            arcpy.management.SelectLayerByAttribute(
                                "features_lyr",
                                "ADD_TO_SELECTION",
                                where_clause
                            )
                        except arcpy.ExecuteError:
                            continue
                
                kept_segments = f"kept_segments_{current_round}"
                arcpy.management.CopyFeatures("features_lyr", kept_segments)
                
                merged_output = f"merged_{current_round}"
                arcpy.management.Merge([new_segments, kept_segments], merged_output)
                
                for fc in [long_segments, split_lines, mid_points, new_segments, kept_segments]:
                    if arcpy.Exists(fc):
                        arcpy.management.Delete(fc)
                        
                min_length = float('inf')
                max_length = 0
                with arcpy.da.SearchCursor(merged_output, ["length_new"]) as cursor:
                    for row in cursor:
                        length = row[0]
                        min_length = min(min_length, length)
                        max_length = max(max_length, length)
                
                arcpy.AddMessage(f"After splitting - Minimum segment length: {min_length:.2f}")
                arcpy.AddMessage(f"After splitting - Maximum segment length: {max_length:.2f}")
                
                if arcpy.Exists(input_features1) and input_features1 != "input1_clipped":
                    arcpy.management.Delete(input_features1)
                input_features1 = merged_output
                
            current_round += 1
        
        # Copy final results to output
        arcpy.management.CopyFeatures(input_features1, "final_segments1")
        
        # Clean up fields
        arcpy.management.DeleteField("final_segments1", [
            "ORIG_FID", "ORIG_SEQ", "ORIG_FID_1", "ORIG_SEQ_1", "ORIG_FID_12", "ORIG_SEQ_12",
            "ORIG_FID_12_13", "ORIG_SEQ_12_13", "ORIG_FID_12_13_14", "ORIG_SEQ_12_13_14",
            "ORIG_FID_12_13_14_15", "ORIG_SEQ_12_13_14_15", "ORIG_FID_12_13_14_15_16", "ORIG_SEQ_12_13_14_15_16",
            "ORIG_FID_12_13_14_15_16_17", "ORIG_SEQ_12_13_14_15_16_17"
        ])
        #####Calculation of azimuth for Grount Turth and Extracted Lineaments
        
        arcpy.management.CalculateGeometryAttributes("final_segments0", [["Azimuth_new","LINE_BEARING"]])
        arcpy.management.CalculateGeometryAttributes("final_segments1", [["Azimuth_new","LINE_BEARING"]])
        #####Calculation of azimuth for Grount Turth and Extracted Lineaments
        
        arcpy.management.CalculateGeometryAttributes(input0, [["Azimuth_new","LINE_BEARING"]])
        arcpy.management.CalculateGeometryAttributes(input1, [["Azimuth_new","LINE_BEARING"]])
        input0="final_segments0"
        input1="final_segments1"
        ######Next steps are for azimuth correction according to project specification
        arcpy.management.AddField(
            input0,
            field_name="az_corrected",
            field_type="DOUBLE",
            field_precision=None,
            field_scale=None,
            field_length=None,
            field_alias="",
            field_is_nullable="NULLABLE",
            field_is_required="NON_REQUIRED",
            field_domain=""
        )
        arcpy.management.AddField(
            input1,
            field_name="az_corrected",
            field_type="DOUBLE",
            field_precision=None,
            field_scale=None,
            field_length=None,
            field_alias="",
            field_is_nullable="NULLABLE",
            field_is_required="NON_REQUIRED",
            field_domain=""
        )

        arcpy.management.CalculateField(
            input0,
            field="az_corrected",
            expression="az_cor(!Azimuth_new!)",
            expression_type="PYTHON3",
            code_block="""def az_cor(az):
            if (az>180):
                b = az - 180
                return b
            else:
                return az""",
            field_type="TEXT",
            enforce_domains="NO_ENFORCE_DOMAINS"
        )  
        
        arcpy.management.CalculateField(
            input1,
            field="az_corrected",
            expression="az_cor(!Azimuth_new!)",
            expression_type="PYTHON3",
            code_block="""def az_cor(az):
            if (az>180):
                b = az - 180
                return b
            else:
                return az""",
            field_type="TEXT",
            enforce_domains="NO_ENFORCE_DOMAINS"
        )  
        arcpy.management.AddField(
            input0,
            field_name="Azi_Correc_p20",
            field_type="DOUBLE",
            field_precision=None,
            field_scale=None,
            field_length=None,
            field_alias="",
            field_is_nullable="NULLABLE",
            field_is_required="NON_REQUIRED",
            field_domain=""
        )
        arcpy.management.AddField(
            input1,
            field_name="Azi_Correc_p20",
            field_type="DOUBLE",
            field_precision=None,
            field_scale=None,
            field_length=None,
            field_alias="",
            field_is_nullable="NULLABLE",
            field_is_required="NON_REQUIRED",
            field_domain=""
        )
        arcpy.management.AddField(
            input0,
            field_name="Azi_Correc_l20",
            field_type="DOUBLE",
            field_precision=None,
            field_scale=None,
            field_length=None,
            field_alias="",
            field_is_nullable="NULLABLE",
            field_is_required="NON_REQUIRED",
            field_domain=""
        )
        arcpy.management.AddField(
            input1,
            field_name="Azi_Correc_l20",
            field_type="DOUBLE",
            field_precision=None,
            field_scale=None,
            field_length=None,
            field_alias="",
            field_is_nullable="NULLABLE",
            field_is_required="NON_REQUIRED",
            field_domain=""
        )
        arcpy.management.AddField(
            input0,
            field_name="Azi_Correc_p20_corre",
            field_type="DOUBLE",
            field_precision=None,
            field_scale=None,
            field_length=None,
            field_alias="",
            field_is_nullable="NULLABLE",
            field_is_required="NON_REQUIRED",
            field_domain=""
        )
        arcpy.management.AddField(
            input1,
            field_name="Azi_Correc_p20_corre",
            field_type="DOUBLE",
            field_precision=None,
            field_scale=None,
            field_length=None,
            field_alias="",
            field_is_nullable="NULLABLE",
            field_is_required="NON_REQUIRED",
            field_domain=""
        )
        arcpy.management.AddField(
            input0,
            field_name="Azi_Correc_l20_corre",
            field_type="DOUBLE",
            field_precision=None,
            field_scale=None,
            field_length=None,
            field_alias="",
            field_is_nullable="NULLABLE",
            field_is_required="NON_REQUIRED",
            field_domain=""
        )
        arcpy.management.AddField(
            input1,
            field_name="Azi_Correc_l20_corre",
            field_type="DOUBLE",
            field_precision=None,
            field_scale=None,
            field_length=None,
            field_alias="",
            field_is_nullable="NULLABLE",
            field_is_required="NON_REQUIRED",
            field_domain=""
        )
        arcpy.management.CalculateField(
            input0,
            field="Azi_Correc_p20",
            expression="!az_corrected! + 20",
            expression_type="PYTHON3",
            code_block="",
            field_type="TEXT",
            enforce_domains="NO_ENFORCE_DOMAINS"
        )
        arcpy.management.CalculateField(
            input1,
            field="Azi_Correc_p20",
            expression="!az_corrected! + 20",
            expression_type="PYTHON3",
            code_block="",
            field_type="TEXT",
            enforce_domains="NO_ENFORCE_DOMAINS"
        )
        arcpy.management.CalculateField(
            input0,
            field="Azi_Correc_l20",
            expression="!az_corrected! - 20",
            expression_type="PYTHON3",
            code_block="",
            field_type="TEXT",
            enforce_domains="NO_ENFORCE_DOMAINS"
        )
        arcpy.management.CalculateField(
            input1,
            field="Azi_Correc_l20",
            expression="!az_corrected! - 20",
            expression_type="PYTHON3",
            code_block="",
            field_type="TEXT",
            enforce_domains="NO_ENFORCE_DOMAINS"
        )
    
        arcpy.management.CalculateField(
            input0,
            field="Azi_Correc_p20_corre",
            expression="az_cor(!Azi_Correc_p20!)",
            expression_type="PYTHON3",
            code_block="""def az_cor(az):
                if (az>180):
                    b = az - 180
                    return b
                else:
                    return az""",
            field_type="TEXT",
            enforce_domains="NO_ENFORCE_DOMAINS"
        )
        arcpy.management.CalculateField(
            input1,
            field="Azi_Correc_p20_corre",
            expression="az_cor(!Azi_Correc_p20!)",
            expression_type="PYTHON3",
            code_block="""def az_cor(az):
                if (az>180):
                    b = az - 180
                    return b
                else:
                    return az""",
            field_type="TEXT",
            enforce_domains="NO_ENFORCE_DOMAINS"
        )
        arcpy.management.CalculateField(
            input0,
            field="Azi_Correc_l20_corre",
            expression="az_cor(!Azi_Correc_l20!)",
            expression_type="PYTHON3",
            code_block="""def az_cor(az):
                if (az>-20 and az<0):
                    b = az + 180
                    return b
                else:
                    return az""",
            field_type="TEXT",
            enforce_domains="NO_ENFORCE_DOMAINS"
        )
        arcpy.management.CalculateField(
            input1,
            field="Azi_Correc_l20_corre",
            expression="az_cor(!Azi_Correc_l20!)",
            expression_type="PYTHON3",
            code_block="""def az_cor(az):
                if (az>-20 and az<0):
                    b = az + 180
                    return b
                else:
                    return az""",
            field_type="TEXT",
            enforce_domains="NO_ENFORCE_DOMAINS"

        )


        ### In this step all the line segments are transformed into middle and start/end points, inheriting the attributes from the "mother" input 
        arcpy.management.SplitLine(
            input0,
            out_feature_class=r"NearFeatures0_SplitLine"
        )
        arcpy.management.SplitLine(
            input1,
            out_feature_class=r"NearFeatures1_SplitLine"
        )
        arcpy.management.FeatureVerticesToPoints(
            in_features="NearFeatures0_SplitLine",
            out_feature_class=r"jf0_output_FeatureVerticesTo_ends",
            point_location="BOTH_ENDS"
        )
        arcpy.management.FeatureVerticesToPoints(
            in_features="NearFeatures1_SplitLine",
            out_feature_class=r"jf1_output_FeatureVerticesTo_ends",
            point_location="BOTH_ENDS"
        )
        arcpy.management.FeatureVerticesToPoints(
            in_features="NearFeatures0_SplitLine",
            out_feature_class=r"jf0_output_FeatureVerticesTo_mid",
            point_location="MID"
        )
        arcpy.management.FeatureVerticesToPoints(
            in_features="NearFeatures1_SplitLine",
            out_feature_class=r"jf1_output_FeatureVerticesTo_mid",
            point_location="MID"
        )
        arcpy.management.CalculateGeometryAttributes("jf0_output_FeatureVerticesTo_ends", [["X","POINT_X"],["Y","POINT_Y"]])
        arcpy.management.CalculateGeometryAttributes("jf1_output_FeatureVerticesTo_ends", [["X","POINT_X"],["Y","POINT_Y"]])
        arcpy.management.CalculateGeometryAttributes("jf0_output_FeatureVerticesTo_mid", [["X","POINT_X"],["Y","POINT_Y"]])
        arcpy.management.CalculateGeometryAttributes("jf1_output_FeatureVerticesTo_mid", [["X","POINT_X"],["Y","POINT_Y"]])
        arcpy.management.DeleteIdentical("jf0_output_FeatureVerticesTo_ends", ["ORIG_FID"])
        arcpy.management.DeleteIdentical("jf1_output_FeatureVerticesTo_ends", ["ORIG_FID"])
        arcpy.management.DeleteIdentical("jf0_output_FeatureVerticesTo_mid", ["ORIG_FID"])
        arcpy.management.DeleteIdentical("jf0_output_FeatureVerticesTo_mid", ["ORIG_FID"])


        ### For each product (Grount Truth and Extracted Lineaments)  two point vector files were created representing middle points and start/end points for eache segment. 
        ### On this step each middle-start/end vector is merged into one shapefile. Hence, two products are generated, one for the Ground Truth and the other for Extracted Lineaments  

        arcpy.management.Merge(
            inputs="jf0_output_FeatureVerticesTo_ends;jf0_output_FeatureVerticesTo_mid",
            output=r"jf0_output_FeatureVert_Merge",
            field_mappings='ID "ID" true true false 4 Long 0 0,First,#,jf0_output_FeatureVerticesTo_ends,ID,-1,-1,jf0_output_FeatureVerticesTo_mid,ID,-1,-1;GEOM_LEN "GEOM_LEN" true true false 8 Double 0 0,First,#,jf0_output_FeatureVerticesTo_ends,GEOM_LEN,-1,-1,jf0_output_FeatureVerticesTo_mid,GEOM_LEN,-1,-1;Descripción "Descripción" true true false 250 Text 0 0,First,#,jf0_output_FeatureVerticesTo_ends,Descripción,0,250,jf0_output_FeatureVerticesTo_mid,Descripción,0,250;Azimuth_new "Azimuth_new" true true false 8 Double 0 0,First,#,jf0_output_FeatureVerticesTo_ends,Azimuth_new,-1,-1,jf0_output_FeatureVerticesTo_mid,Azimuth_new,-1,-1;az_corrected "az_corrected" true true false 8 Double 0 0,First,#,jf0_output_FeatureVerticesTo_ends,az_corrected,-1,-1,jf0_output_FeatureVerticesTo_mid,az_corrected,-1,-1;Azi_Correc_p20 "Azi_Correc_p20" true true false 8 Double 0 0,First,#,jf0_output_FeatureVerticesTo_ends,Azi_Correc_p20,-1,-1,jf0_output_FeatureVerticesTo_mid,Azi_Correc_p20,-1,-1;Azi_Correc_l20 "Azi_Correc_l20" true true false 8 Double 0 0,First,#,jf0_output_FeatureVerticesTo_ends,Azi_Correc_l20,-1,-1,jf0_output_FeatureVerticesTo_mid,Azi_Correc_l20,-1,-1;Azi_Correc_p20_corre "Azi_Correc_p20_corre" true true false 8 Double 0 0,First,#,jf0_output_FeatureVerticesTo_ends,Azi_Correc_p20_corre,-1,-1,jf0_output_FeatureVerticesTo_mid,Azi_Correc_p20_corre,-1,-1;Azi_Correc_l20_corre "Azi_Correc_l20_corre" true true false 8 Double 0 0,First,#,jf0_output_FeatureVerticesTo_ends,Azi_Correc_l20_corre,-1,-1,jf0_output_FeatureVerticesTo_mid,Azi_Correc_l20_corre,-1,-1;ORIG_FID "ORIG_FID" true true false 4 Long 0 0,First,#,jf0_output_FeatureVerticesTo_ends,ORIG_FID,-1,-1,jf0_output_FeatureVerticesTo_mid,ORIG_FID,-1,-1;ORIG_SEQ "ORIG_SEQ" true true false 4 Long 0 0,First,#,jf0_output_FeatureVerticesTo_ends,ORIG_SEQ,-1,-1,jf0_output_FeatureVerticesTo_mid,ORIG_SEQ,-1,-1;X "X" true true false 8 Double 0 0,First,#,jf0_output_FeatureVerticesTo_ends,X,-1,-1,jf0_output_FeatureVerticesTo_mid,X,-1,-1;Y "Y" true true false 8 Double 0 0,First,#,jf0_output_FeatureVerticesTo_ends,Y,-1,-1,jf0_output_FeatureVerticesTo_mid,Y,-1,-1;length_new "length_new" true true false 8 Double 0 0,First,#,jf0_output_FeatureVerticesTo_ends,length_new,-1,-1,jf0_output_FeatureVerticesTo_mid,length_new,-1,-1;descriptio "descriptio" true true false 250 Text 0 0,First,#,jf0_output_FeatureVerticesTo_ends,descriptio,0,250,jf0_output_FeatureVerticesTo_mid,descriptio,0,250',
            add_source="NO_SOURCE_INFO"
        )
        arcpy.management.Merge(
            inputs="jf1_output_FeatureVerticesTo_ends;jf1_output_FeatureVerticesTo_mid",
            output=r"jf1_output_FeatureVert_Merge",
            field_mappings='ID "ID" true true false 4 Long 0 0,First,#,jf0_output_FeatureVerticesTo_ends,ID,-1,-1,jf0_output_FeatureVerticesTo_mid,ID,-1,-1;GEOM_LEN "GEOM_LEN" true true false 8 Double 0 0,First,#,jf0_output_FeatureVerticesTo_ends,GEOM_LEN,-1,-1,jf0_output_FeatureVerticesTo_mid,GEOM_LEN,-1,-1;Descripción "Descripción" true true false 250 Text 0 0,First,#,jf0_output_FeatureVerticesTo_ends,Descripción,0,250,jf0_output_FeatureVerticesTo_mid,Descripción,0,250;Azimuth_new "Azimuth_new" true true false 8 Double 0 0,First,#,jf0_output_FeatureVerticesTo_ends,Azimuth_new,-1,-1,jf0_output_FeatureVerticesTo_mid,Azimuth_new,-1,-1;az_corrected "az_corrected" true true false 8 Double 0 0,First,#,jf0_output_FeatureVerticesTo_ends,az_corrected,-1,-1,jf0_output_FeatureVerticesTo_mid,az_corrected,-1,-1;Azi_Correc_p20 "Azi_Correc_p20" true true false 8 Double 0 0,First,#,jf0_output_FeatureVerticesTo_ends,Azi_Correc_p20,-1,-1,jf0_output_FeatureVerticesTo_mid,Azi_Correc_p20,-1,-1;Azi_Correc_l20 "Azi_Correc_l20" true true false 8 Double 0 0,First,#,jf0_output_FeatureVerticesTo_ends,Azi_Correc_l20,-1,-1,jf0_output_FeatureVerticesTo_mid,Azi_Correc_l20,-1,-1;Azi_Correc_p20_corre "Azi_Correc_p20_corre" true true false 8 Double 0 0,First,#,jf0_output_FeatureVerticesTo_ends,Azi_Correc_p20_corre,-1,-1,jf0_output_FeatureVerticesTo_mid,Azi_Correc_p20_corre,-1,-1;Azi_Correc_l20_corre "Azi_Correc_l20_corre" true true false 8 Double 0 0,First,#,jf0_output_FeatureVerticesTo_ends,Azi_Correc_l20_corre,-1,-1,jf0_output_FeatureVerticesTo_mid,Azi_Correc_l20_corre,-1,-1;ORIG_FID "ORIG_FID" true true false 4 Long 0 0,First,#,jf0_output_FeatureVerticesTo_ends,ORIG_FID,-1,-1,jf0_output_FeatureVerticesTo_mid,ORIG_FID,-1,-1;ORIG_SEQ "ORIG_SEQ" true true false 4 Long 0 0,First,#,jf0_output_FeatureVerticesTo_ends,ORIG_SEQ,-1,-1,jf0_output_FeatureVerticesTo_mid,ORIG_SEQ,-1,-1;X "X" true true false 8 Double 0 0,First,#,jf0_output_FeatureVerticesTo_ends,X,-1,-1,jf0_output_FeatureVerticesTo_mid,X,-1,-1;Y "Y" true true false 8 Double 0 0,First,#,jf0_output_FeatureVerticesTo_ends,Y,-1,-1,jf0_output_FeatureVerticesTo_mid,Y,-1,-1;length_new "length_new" true true false 8 Double 0 0,First,#,jf0_output_FeatureVerticesTo_ends,length_new,-1,-1,jf0_output_FeatureVerticesTo_mid,length_new,-1,-1',
            add_source="NO_SOURCE_INFO"
        )
        
        in_features = "random_points"
        random_points1 = "random_points"
        random_points2 = "random_points"
        random_points3 = "random_points"
        random_points4 = "random_points"

        ####On this step, a near table between vectors is calculated. The function calculates the distance and angle between all the sample points randomly generated and the Grount Truth and Measured Points. 
        #### Result is in table format
        
        near_points0="jf0_output_FeatureVert_Merge"
        near_points1="jf1_output_FeatureVert_Merge"
        arcpy.analysis.GenerateNearTable(
            in_features,
            near_points0,
            out_table="near_out_table_jf0",
            search_radius="200 Meters",
            location="LOCATION",
            angle="ANGLE",
            closest="ALL",
            closest_count=1000000,
            method="GEODESIC",
            distance_unit="Meters"
        )
        arcpy.analysis.GenerateNearTable(
            in_features,
            near_points1,
            out_table="near_out_table_jf1",
            search_radius="200 Meters",
            location="LOCATION",
            angle="ANGLE",
            closest="ALL",
            closest_count=1000000,
            method="GEODESIC",
            distance_unit="Meters"
        )
        
        
        ## This part of the scipt joins the near table with the point features
        arcpy.gapro.JoinFeatures(
            target_layer="jf0_output_FeatureVert_Merge",
            join_layer="near_out_table_jf0",
            output="Contactos_Vert",
            join_operation="JOIN_ONE_TO_MANY",
            spatial_relationship="",
            spatial_near_distance=None,
            temporal_relationship="",
            temporal_near_distance=None,
            attribute_relationship="OBJECTID NEAR_FID",
            summary_fields=None,
            join_condition="",
            keep_all_target_features="KEEP_ALL"
        )
        
        arcpy.gapro.JoinFeatures(
            target_layer="jf1_output_FeatureVert_Merge",
            join_layer="near_out_table_jf1",
            output="Measured_Vert",
            join_operation="JOIN_ONE_TO_MANY",
            spatial_relationship="",
            spatial_near_distance=None,
            temporal_relationship="",
            temporal_near_distance=None,
            attribute_relationship="OBJECTID NEAR_FID",
            summary_fields=None,
            join_condition="",
            keep_all_target_features="KEEP_ALL"
        )
    
        
    
        
        ## On this step the Ground Truth and Extracted Lineaemnts are joined. This way the azimuth can be compared for each element of the two feature layers. 
        inFeatures1="Contactos_Vert"
        inFeatures2="Measured_Vert"
        arcpy.management.AddField(
            inFeatures1,
            field_name="Quadrant",
            field_type="DOUBLE",
            field_precision=None,
            field_scale=None,
            field_length=None,
            field_alias="",
            field_is_nullable="NULLABLE",
            field_is_required="NON_REQUIRED",
            field_domain=""
        )
        arcpy.management.CalculateField(
            inFeatures1,
            field="Quadrant",
            expression="az_cor(!NEAR_ANGLE!)",
            expression_type="PYTHON3",
            code_block="""def az_cor(az):
            if (az>0 and az < 90):
                return 1
            if (az>=90 and az < 180):
                return 2
            if (az<=-90 and az > -180):
                return 3
            if (az<=0 and az >-90):
                return 4  """,
            field_type="DOUBLE",
            enforce_domains="NO_ENFORCE_DOMAINS"
        )
        arcpy.management.AddField(
            inFeatures2,
            field_name="Quadrant",
            field_type="DOUBLE",
            field_precision=None,
            field_scale=None,
            field_length=None,
            field_alias="",
            field_is_nullable="NULLABLE",
            field_is_required="NON_REQUIRED",
            field_domain=""
        )
        
        arcpy.management.CalculateField(
            inFeatures2,
            field="Quadrant",
            expression="az_cor(!NEAR_ANGLE!)",
            expression_type="PYTHON3",
            code_block="""def az_cor(az):
            if (az>0 and az < 90):
                return 1
            if (az>=90 and az < 180):
                return 2
            if (az<=-90 and az > -180):
                return 3
            if (az<=0 and az >-90):
                return 4 """,
            field_type="DOUBLE",
            enforce_domains="NO_ENFORCE_DOMAINS"
        )
        ## On this step the Ground Truth and Extracted Lineaemnts are joined. This way the azimuth can be compared for each element of the two feature layers. 

        arcpy.gapro.JoinFeatures(
            inFeatures1,
            inFeatures2,
            output="Contacts_Measured_Join_Quadrant",                         
            join_operation="JOIN_ONE_TO_MANY",
            spatial_relationship="",
            spatial_near_distance=None,
            temporal_relationship="",
            temporal_near_distance=None,
            attribute_relationship="IN_FID IN_FID",
            summary_fields=None,
            join_condition="",
            keep_all_target_features="KEEP_ALL"
        )
        arcpy.gapro.JoinFeatures(
            inFeatures2,
            inFeatures1,
            output="Measured_Contacts_Join_Quadrant",                          ##################### if IN_FID the same and Quadrant the same , join 
            join_operation="JOIN_ONE_TO_MANY",
            spatial_relationship="",
            spatial_near_distance=None,
            temporal_relationship="",
            temporal_near_distance=None,
            attribute_relationship="IN_FID IN_FID",
            summary_fields=None,
            join_condition="",
            keep_all_target_features="KEEP_ALL"
        )
        
        
        arcpy.management.AddField(
            in_table="Contacts_Measured_Join_Quadrant",
            field_name="Quadrant_Match",
            field_type="SHORT",
            field_precision=None,
            field_scale=None,
            field_length=None,
            field_alias="Quadrant_Match",
            field_is_nullable="NULLABLE",
            field_is_required="NON_REQUIRED",
            field_domain=""
        )
        arcpy.management.AddField(
            in_table="Measured_Contacts_Join_Quadrant",
            field_name="Quadrant_Match",
            field_type="SHORT",
            field_precision=None,
            field_scale=None,
            field_length=None,
            field_alias="Quadrant_Match",
            field_is_nullable="NULLABLE",
            field_is_required="NON_REQUIRED",
            field_domain=""
        )
        arcpy.management.CalculateField(
            in_table="Contacts_Measured_Join_Quadrant",
            field="Quadrant_Match",
            expression="qu(!Quadrant!,!join_Quadrant!)",
            expression_type="PYTHON3",
            code_block="""def qu(q1,q2):
            if (q1==q2):
                return 1
            if (q1 == None or q2 == None  ):
                return None
            else:
                return 0""",
            field_type="TEXT",
            enforce_domains="NO_ENFORCE_DOMAINS"
        )
        arcpy.management.CalculateField(
            in_table="Measured_Contacts_Join_Quadrant",
            field="Quadrant_Match",
            expression="qu(!Quadrant!,!join_Quadrant!)",
            expression_type="PYTHON3",
            code_block="""def qu(q1,q2):
            if (q1==q2):
                return 1
            if (q1 == None or q2 == None  ):
                return None
            else:
                return 0""",
            field_type="TEXT",
            enforce_domains="NO_ENFORCE_DOMAINS"
        )
        arcpy.management.AddField(
            in_table="Contacts_Measured_Join_Quadrant",
            field_name="Az_Match",
            field_type="SHORT",
            field_precision=None,
            field_scale=None,
            field_length=None,
            field_alias="",
            field_is_nullable="NULLABLE",
            field_is_required="NON_REQUIRED",
            field_domain=""
        )
        arcpy.management.AddField(
            in_table="Measured_Contacts_Join_Quadrant",
            field_name="Az_Match",
            field_type="SHORT",
            field_precision=None,
            field_scale=None,
            field_length=None,
            field_alias="",
            field_is_nullable="NULLABLE",
            field_is_required="NON_REQUIRED",
            field_domain=""
        )
        ## On this step, Ground Truth and Extracted Lineaments are compared in terms of azimuth match. A tolerance of 20 degrees is given. If the azimuths from both layers
        ### fit inside the tolerance interval, than it's a match. In This case, it's a true positive. 
        arcpy.management.CalculateField(
            in_table="Contacts_Measured_Join_Quadrant",
            field="Az_Match",
            expression="az_cor(!az_corrected!,!join_az_corrected!,!join_Azi_Correc_p20!,!join_Azi_Correc_l20!)",
            expression_type="PYTHON3",
            code_block="""def az_cor(azi, join_azi, join_azi_p20, join_azi_l20):
                # Calcula a menor distância angular
                direct_dist = abs(join_azi - azi)
                wrap_dist = min(
                    abs(180 - max(azi, join_azi) + min(azi, join_azi)),
                    abs(180 - join_azi + azi),
                    abs(180 - azi + join_azi)
                )
                
                # Usa a menor das distâncias
                min_dist = min(direct_dist, wrap_dist)
                
                # Retorna 1 se a menor distância for menor ou igual a 20 graus
                if min_dist <= 20:
                    return 1
                return 0""",
            field_type="TEXT",
            enforce_domains="NO_ENFORCE_DOMAINS"
        )
        arcpy.management.CalculateField(
            in_table="Measured_Contacts_Join_Quadrant",
            field="Az_Match",
            expression="az_cor(!az_corrected!,!join_az_corrected!,!join_Azi_Correc_p20!,!join_Azi_Correc_l20!)",
            expression_type="PYTHON3",
            code_block="""def az_cor(azi, join_azi, join_azi_p20, join_azi_l20):
                # Calcula a menor distância angular
                direct_dist = abs(join_azi - azi)
                wrap_dist = min(
                    abs(180 - max(azi, join_azi) + min(azi, join_azi)),
                    abs(180 - join_azi + azi),
                    abs(180 - azi + join_azi)
                )
                
                # Usa a menor das distâncias
                min_dist = min(direct_dist, wrap_dist)
                
                # Retorna 1 se a menor distância for menor ou igual a 20 graus
                if min_dist <= 20:
                    return 1
                return 0""",
            field_type="TEXT",
            enforce_domains="NO_ENFORCE_DOMAINS"
        )
        
        arcpy.management.AddField(
            in_table="Contacts_Measured_Join_Quadrant",
            field_name="Quadrant_Azimuth_Match",
            field_type="SHORT",
            field_precision=None,
            field_scale=None,
            field_length=None,
            field_alias="",
            field_is_nullable="NULLABLE",
            field_is_required="NON_REQUIRED",
            field_domain=""
        )
        arcpy.management.AddField(
            in_table="Measured_Contacts_Join_Quadrant",
            field_name="Quadrant_Azimuth_Match",
            field_type="SHORT",
            field_precision=None,
            field_scale=None,
            field_length=None,
            field_alias="",
            field_is_nullable="NULLABLE",
            field_is_required="NON_REQUIRED",
            field_domain=""
        )
        arcpy.management.CalculateField(
            in_table="Contacts_Measured_Join_Quadrant",
            field="Quadrant_Azimuth_Match",
            expression="q(!Quadrant_Match!,!Az_Match!)",
            expression_type="PYTHON3",
            code_block="""def q(q1,q2):
                    if (q1==1 and q2 == 1):
                        return 1
                    else:
                        return 0""",
            field_type="TEXT",
            enforce_domains="NO_ENFORCE_DOMAINS"
        )
        arcpy.management.CalculateField(
            in_table="Measured_Contacts_Join_Quadrant",
            field="Quadrant_Azimuth_Match",
            expression="q(!Quadrant_Match!,!Az_Match!)",
            expression_type="PYTHON3",
            code_block="""def q(q1,q2):
                    if (q1==1 and q2 == 1):
                        return 1
                    else:
                        return 0""",
            field_type="TEXT",
            enforce_domains="NO_ENFORCE_DOMAINS"
        )
        arcpy.conversion.ExportTable(
            in_table="Contacts_Measured_Join_Quadrant",
            out_table=r"output0",
            where_clause="Quadrant_Azimuth_Match = 1",
            use_field_alias_as_name="NOT_USE_ALIAS",
            field_mapping='OBJECTID1 "OBJECTID1" true true false 4 Long 0 0,First,#,Contacts_Measured_Join_Merge_with_contacts_with_measured,OBJECTID1,-1,-1;IN_FID "IN_FID" true true false 4 Long 0 0,First,#,Contacts_Measured_Join_Merge_with_contacts_with_measured,IN_FID,-1,-1;Quadrant_Match "Quadrant_Match" true true false 2 Short 0 0,First,#,Contacts_Measured_Join_Merge_with_contacts_with_measured,Quadrant_Match,-1,-1;Az_Match "Az_Match" true true false 2 Short 0 0,First,#,Contacts_Measured_Join_Merge_with_contacts_with_measured,Az_Match,-1,-1;Quadrant_Azimuth_Match "Quadrant_Azimuth_Match" true true false 2 Short 0 0,First,#,Contacts_Measured_Join_Merge_with_contacts_with_measured,Quadrant_Azimuth_Match,-1,-1',
            sort_field=None
        )
        arcpy.conversion.ExportTable(
            in_table="Measured_Contacts_Join_Quadrant",
            out_table=r"output11",
            where_clause="Quadrant_Azimuth_Match = 1",
            use_field_alias_as_name="NOT_USE_ALIAS",
            field_mapping='OBJECTID1 "OBJECTID1" true true false 4 Long 0 0,First,#,Contacts_Measured_Join_Merge_with_contacts_with_measured,OBJECTID1,-1,-1;IN_FID "IN_FID" true true false 4 Long 0 0,First,#,Contacts_Measured_Join_Merge_with_contacts_with_measured,IN_FID,-1,-1;Quadrant_Match "Quadrant_Match" true true false 2 Short 0 0,First,#,Contacts_Measured_Join_Merge_with_contacts_with_measured,Quadrant_Match,-1,-1;Az_Match "Az_Match" true true false 2 Short 0 0,First,#,Contacts_Measured_Join_Merge_with_contacts_with_measured,Az_Match,-1,-1;Quadrant_Azimuth_Match "Quadrant_Azimuth_Match" true true false 2 Short 0 0,First,#,Contacts_Measured_Join_Merge_with_contacts_with_measured,Quadrant_Azimuth_Match,-1,-1',
            sort_field=None
        )
        
        ###########True Negatives are calculated on this step. If no point is identified on the radius search, then it's a true negative################
        arcpy.analysis.Near(
            in_features="random_points",
            near_features="Contactos_Vert;Measured_Vert",
            search_radius="200 Meters",
            location="LOCATION",
            angle="ANGLE",
            method="PLANAR",
            field_names="NEAR_FID NEAR_FID;NEAR_DIST NEAR_DIST;NEAR_X NEAR_X;NEAR_Y NEAR_Y;NEAR_ANGLE NEAR_ANGLE;NEAR_FC NEAR_FC",
            distance_unit="Meters"
        )

        arcpy.conversion.ExportTable(
            in_table="random_points",
            out_table=r"output1",
            where_clause="",
            use_field_alias_as_name="NOT_USE_ALIAS",
            field_mapping='CID "CID" true true false 4 Long 0 0,First,#,random_points,CID,-1,-1;NEAR_FID "NEAR_FID" true true false 4 Long 0 0,First,#,random_points,NEAR_FID,-1,-1;NEAR_DIST "NEAR_DIST" true true false 8 Double 0 0,First,#,random_points,NEAR_DIST,-1,-1;NEAR_X "NEAR_X" true true false 8 Double 0 0,First,#,random_points,NEAR_X,-1,-1;NEAR_Y "NEAR_Y" true true false 8 Double 0 0,First,#,random_points,NEAR_Y,-1,-1;NEAR_ANGLE "NEAR_ANGLE" true true false 8 Double 0 0,First,#,random_points,NEAR_ANGLE,-1,-1;NEAR_FC "NEAR_FC" true true false 255 Text 0 0,First,#,random_points,NEAR_FC,0,255',
            sort_field=None
        )
        self.export_to_csv("Contacts_Measured_Join_Quadrant", out_contacts_measured_join)
        self.export_to_csv("Contactos_Vert", out_contactos_vert)
        self.export_to_csv("Measured_Vert", out_measured_vert)
        self.export_to_csv("random_points", out_random_points)
        self.export_to_csv("Measured_Contacts_Join_Quadrant", out_measured_contacts_join)
        return
        

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return

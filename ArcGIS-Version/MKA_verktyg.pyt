##########################################################
#2019-01-02
#Created by:
#Victor Mackenhauer Olsen
#victor.olsen@hotmail.com

#Created for:
#Ovanåker Municipality, Sweden

#Description:
#Multicriteria tool for local planning
#Improving urban energy efficiency throuh optimised location allocation of infrastructure
##########################################################

import arcpy


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "MCA Calculator"
        self.alias = "MCA Calculator"

        # List of tool classes associated with this toolbox
        self.tools = [MCA]


class MCA(object): # class containing everything in the tool
    def __init__(self): # initializing the class with this first function
        """Define the tool (tool name is the name of the class)."""
        self.label = "Multikriterieanalys"
        self.description = "Calculates optimal location for new infrastructure"         # Text shown in help menu
        self.canRunInBackground = False

    def getParameterInfo(self):# first function, prepares parameters

        param0 = arcpy.Parameter(
            displayName='Omraade',
            name='extent',
            datatype="GPFeatureLayer",
            parameterType='Optional',
            direction='Input')
        #param0.value = "edsbyn_extent"  #assigning a value to the first parameter


        param1 = arcpy.Parameter(
            displayName='Avstaandsvariabler',
            name='factor_variables',
            datatype="GPValueTable",
            parameterType='Required',
            direction='Input',
            multiValue=True)            # enables the parameter to handle a list of values

        param1.columns = [['GPLayer', 'Avstaandsvariabler'], ['GPDouble', 'Vikt']]      # defining column number, type, and title, for value table. 2 columns.            #GPFeatureLayer
        #param1.values = "Vaegar 20; Fjaerrvaerme 70; Vattenledningar 10"  #assigning values to param1


        param2 = arcpy.Parameter(
            displayName='Restriktionsvariabler',
            name='restriction_variables',
            datatype="GPValueTable",
            parameterType='Optional',
            direction='Input',
            multiValue=True)

        param2.columns = [['GPLayer', 'Restriktionsvariabler']]
        #param2.values = "Oeversvaemningsomraaden_Q100; Aakermark"


        param3 = arcpy.Parameter(
            displayName='Workspace (maalplats foer resultat)',
            name='output workspace',
            datatype="DEWorkspace",   #DEWorkspace can be a database or a folder
            parameterType='Required',
            direction='Input',
            multiValue=False)
        #param3.values = r"C:\Users\SBF-Praktikant\Desktop\Workspace_folder"


        param4 = arcpy.Parameter(
            displayName='Maalplats foer PDF-karta och rapport',
            name='PDF',
            datatype="DEFolder",
            parameterType='Optional',
            direction='Input',
            multiValue=False)
        #param4.values = "C:\Users\SBF-Praktikant\Desktop\Workspace_folder"


        param5 = arcpy.Parameter(
            displayName='Projektnamn - Max 10 tecken av type A-Z',
            name='Project name',
            datatype="GPString",
            parameterType='Required',
            direction='Input',
            multiValue=False)
        param5.values = "MKA"   # default project name


        param6 = arcpy.Parameter(
            displayName='Referenslager med styling',
            name='Symbology reference layer',
            datatype="GPLayer",
            parameterType='Optional',
            direction='Input',
            multiValue=False)
        #param6.values = "C:\Users\SBF-Praktikant\Desktop\MKA_v3\Stylingsreferens.lyr"



        parameters = [param0, param1, param2, param5, param3, param4, param6]           # putting all parameters into a list from which they can be retrieved
        # OBS! Parameters list order doesnt match parameter naming sequence atm!
        return parameters




    def isLicensed(self):
        """Set whether tool is licensed to execute."""

        """Allow the tool to execute, only if the ArcGIS Spatial Analyst extension 
        is available."""
        try:
            if arcpy.CheckExtension("Spatial") != "Available":
                raise Exception
        except Exception:
            return False  # tool cannot be executed

        return True  # tool can be executed


    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""


    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        # Checks to see if sum of weights equal 100. Executed before tool runs.
        if parameters[1].value:
            sum = 0
            for x in range(len(parameters[1].value)):
                w = parameters[1].value[x][1]
                sum += w
            if sum != 100:
                parameters[1].setErrorMessage("Sum not equal to 100")
        return



################################  PARAMETER SYNTAX (for reference)  ##############################################
#    parameter = [extent, [layer, weight], restriction]
#    multi_parameter = [extent, [[layer, weight],[layer2, weight2],[layer3, weight3]],[restriction, restriction2]]
##################################################################################################################



    def execute(self, parameters, messages):
        """The source code of the tool."""

        import arcpy, os, sys, datetime
        import unicodedata  # used for str/unicode transformations for variable names in report

        arcpy.env.overwriteOutput = True
        arcpy.env.workspace = parameters[4].value
        workspace = arcpy.env.workspace
        workspacetype = arcpy.Describe(parameters[4].value).workspaceType

        mxd = arcpy.mapping.MapDocument("CURRENT")
        df = arcpy.mapping.ListDataFrames(mxd)[0]



        # Extent determinator
        if parameters[0].value is not None:                     # uses polygon if available
            arcpy.env.extent = parameters[0].value.extent
        else:
            extent_coordinates = str(df.extent)     # else, takes current work data frame view and uses that
            arcpy.env.extent = str(' '.join(extent_coordinates.split()[0:4]))



        #Factor variables (aka. distance variables)
        #Makes list of factor variables
        weights = []
        factorvariables = []
        counter = 0
        for n in range(len(parameters[1].value)):
            variable = parameters[1].value[n][0]
            weight = parameters[1].value[n][1]
            factorvariables.append(variable)
            weights.append(weight)
            counter += 1



        #Restriction variables
        #Makes a list of restriction variables
        restrictionvariables = []
        counter = 0
        if parameters[2].value:
            for n in range(len(parameters[2].value)):
                variable = parameters[2].value[n][0]
                restrictionvariables.append(variable)
                counter += 1

        #messages.addErrorMessage("{}".format(str(restrictionvariables[0].baseName)))
        #raise arcpy.ExecuteError




        ##Processing Factor variables - Euclidean distance and weights
        ##messages.addMessage("\nProcessing factor variables...\n")

        variable_list = []

        def factorprocessor2(inRaster, weight):

            #vector_count = 0
            vector_name = "pro_{}".format(str(vector_count))

            arcpy.CheckOutExtension("Spatial")
            inRaster_dis = arcpy.sa.EucDistance(inRaster, "", 5)        #Line 223 in v3
            inRaster_weighted = inRaster_dis * (weight/100)


         #saving to correct format depending on workspace type and data type
            if workspacetype == "LocalDatabase":
                try:
                    inRaster_weighted.save(vector_name)
                except:
                    arcpy.RasterToGeodatabase_conversion(inRaster_weighted, vector_name)

            if workspacetype == "FileSystem":
                try:
                    inRaster_weighted.save(vector_name)
                except:
                    arcpy.CopyRaster_management(inRaster_weighted, vector_name)         #Line 238 in v3

            arcpy.CheckInExtension("Spatial")
            variable_list.append(vector_name)
            #vector_count += 1

        #Executes function

        vector_count = 0
        for x in range(len(factorvariables)):  # takes values and keys in dictionary and runs function on them
            factorprocessor2(factorvariables[x], weights[x])        #Line 246 in v3
            vector_count += 1





        ##Processing Restriction variables - Rasterize and Reclassify
        messages.addMessage("Processing restriction variables...\n")

        def restrictionprocessor(inVector):
            arcpy.CheckOutExtension("Spatial")
            fields = arcpy.ListFields(inVector)

            # Loops through fields finding one that works for rasterizing
            field_count = 0
            #ras_count = 1
            while True:
                ras_name = "ras_{}".format(str(ras_count))
                try:
                    arcpy.FeatureToRaster_conversion(inVector, fields[field_count].name, ras_name, 5)  # making raster of restriction variable
                    outCon = arcpy.sa.Con(arcpy.sa.IsNull(ras_name), 0, "")  # changing values to Nodata, and NoData to 0
                    break
                except:
                    field_count += 1
                    if field_count > 50:
                        messages.addErrorMessage(ras_name)
                        raise arcpy.ExecuteError



            # saving to correct format depending on workspace type and data type
            if workspacetype == "LocalDatabase":
                try:
                    outCon.save(ras_name + "_pro")
                except:
                    arcpy.RasterToGeodatabase_conversion(outCon, ras_name + "_pro")

            if workspacetype == "FileSystem":
                try:
                    outCon.save(ras_name + "_pro")
                except:
                    arcpy.CopyRaster_management(outCon, ras_name + "_pro")

            arcpy.Delete_management(ras_name)      # Deleting temporary layer

            arcpy.CheckInExtension("Spatial")
            variable_list.append(ras_name + "_pro")

            #ras_count += 1


        #Executes function
        ras_count = 1
        for variable in restrictionvariables:  # applies function on all restrictionvariables
            restrictionprocessor(variable)
            ras_count += 1


        #messages.addErrorMessage("{}".format(str(variable_list)))
        #raise arcpy.ExecuteError



        #Map Algebra - Summing Rasters
        messages.addMessage("Map algebra calculation...\n")

        arcpy.CheckOutExtension("Spatial")
        i = 0
        for x in range(len(variable_list)):

            out1 = arcpy.sa.Raster(variable_list[x])
            if i == 0:
                out2 = out1  # first iteration: out2 becomes first dataset
                i += 1
            else:
                out2 = out2 + out1  # subsequent interations: out2 becomes summed dataset plus current iterated raster
                i += 1
        arcpy.CheckInExtension("Spatial")




        # Saving result - looping through available file names (dealing with'result'-folder issue)
        messages.addMessage("Saving raster output...\n")

        i = 1
        while True:

            if workspacetype == "FileSystem":
                if str(os.path.isfile(str(workspace + "\\" + str(parameters[3].value) + str(i) + ".tif"))) == "True":   #
                    i += 1
                else:
                    try:
                        out2.save(workspace + "\\" + str(parameters[3].value) + str(i) + ".tif")
                        break
                    except:
                        i += 1

            if workspacetype == "LocalDatabase":
                if str(arcpy.Exists("{}{}".format(parameters[3].value, str(i)))) == "True":
                    i += 1
                else:
                    try:
                        out2.save(workspace + "\\" + str(parameters[3].value) + str(i))
                        break
                    except:
                        i += 1

            if i > 1000:
                messages.addErrorMessage("Unable to save file. Try different filename")
                raise arcpy.ExecuteError


        if workspacetype == "FileSystem":
            result = arcpy.Raster(workspace + "\{}{}".format(str(parameters[3].value), str(i) + ".tif"))

        elif workspacetype == "LocalDatabase":
            result = arcpy.Raster(workspace + "\{}{}".format(str(parameters[3].value), str(i)))



        # Deleting temporary layers
        messages.addMessage("Deleting temporary layers...\n")

        for x in range(len(variable_list)):
            arcpy.Delete_management(variable_list[x])



        # Symbology
        layer_name = arcpy.Describe(result).baseName
        layer = arcpy.MakeRasterLayer_management(result, "{}_layer".format(layer_name))
        arcpy.SaveToLayerFile_management(layer, workspace + "\{}_layer".format(layer_name))              # maybe a problem to save .lyr to database??


        # Adding a layer to the mxd
        addLayer = arcpy.mapping.Layer("{}_layer".format(layer_name)) #"result_layer")
        arcpy.mapping.AddLayer(df, addLayer, "TOP")



        # Enabling the UpdateLayer function to reference symbology layer
        if parameters[6].value is not None:
            messages.addMessage("Adding symbology from reference layer...\n")
            updateLayer = arcpy.mapping.ListLayers(mxd)[0]
            sourceLayer = arcpy.mapping.Layer(str(parameters[6].value))       # Getting symbology from reference .lyr file

            arcpy.mapping.UpdateLayer(df, updateLayer, sourceLayer, True)

        mxd.save()



        # Parameter documentation creator
        # Export map and report
        path = str(parameters[4].value) + "\{}".format(str(parameters[3].value) + str(i))
        path_to_PDF = str(parameters[5].value) + "\{}".format(str(parameters[3].value) + str(i))

        if parameters[5].value is not None:
            messages.addMessage("Generating map and report...\n")
            arcpy.mapping.ExportToPDF(mxd, path)

            if os.path.isfile(path + ".txt") == True:
                os.remove(path + ".txt")

            f = open(path + ".txt", "a+")
            f.write("MKA-RAPPORT\n{}\n".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
            f.write("Projektnamn: {}\n\n\n\n".format(layer_name))

            dash = '-' * 44

            for x in range(len(factorvariables)):
                variable_name1 = unicodedata.normalize('NFKD', factorvariables[x].name).encode('ascii', 'ignore')

                if x == 0:
                    f.write("{:<40}{}".format("Avstaandsvariabler", "Vikt") + "\n" + str(dash) + "\n")
                    f.write("{:<40}".format(variable_name1))
                    f.write("{}\n".format(int(weights[x])))
                else:
                    f = open(path + ".txt", "a")
                    f.write("{:<40}".format(variable_name1))
                    f.write("{}\n".format(int(weights[x])))
            f.write("\n\n\n\n")

            for x in range(len(restrictionvariables)):
                variable_name2 = unicodedata.normalize('NFKD', restrictionvariables[x].name).encode('ascii', 'ignore')
                if x == 0:
                    f.write("{}".format("Restriktionsvariabler") + "\n" + str(dash) + "\n")
                    f.write("{}\n".format(variable_name2))

                else:
                    f.write("{}\n".format(variable_name2))
            f.close()


        messages.addMessage("Execution finished!\n\n")


        messages.addMessage("Raster output:  {}".format(str(workspace + "\{}".format(str(parameters[3].value)) + str(i))))

        if parameters[5].value is not None:
            messages.addMessage("PDF:            {}.pdf".format(path_to_PDF))
            messages.addMessage("Rapport:        {}.txt".format(path_to_PDF))

        messages.addMessage("\n\n\n")


        return




    ###### Syntax for adding messages to display for trouble shooting: #########
    # messages.addErrorMessage("{}".format("Input message or variable"))
    # raise arcpy.ExecuteError
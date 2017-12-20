# Rocco Haro & brandon sayers
# the supermodel class abstracts renewable models for one particular town

import stackedLSTM as modelBuilder_LSTM
import pandas as pd
import random
import workingNN as NN
import numpy as np
import csv
import math
import matplotlib
import matplotlib.pyplot as plt
from pathlib import Path

class GeneticAlg:
    def __init__(self, popSize, modelName):
        """ Genetic algorithm that finds optimal parameters.
            Input the size of a population
        """
        self.pop = [] # the population
        self.fitnessVals = [0 for x in range(len(self.pop))] # matched indexed with population

        self.modelName = modelName
        self.dataFrame = self.loadData()
        self.model = None
        self.popSize = popSize

        self.initPop()

    def loadData(self):
        # Pull all data from CSV file and
        # push into a dataframe for portability.

        df = pd.read_csv(self.modelName, index_col=0, skiprows=[1])
        df.index = pd.to_datetime(df.index)

        return df

    def getLoss(self, idx):
        """ return loss
        """
        self.model = modelBuilder_LSTM.StackedLSTM(dataFrame=self.dataFrame[self.modelName], modelName=(column + "/" + column + self.testNum))
        params = self.pop[idx]
        # This dictionary needs to be unpacked into the networkParams function
        self.model.networkParams(params['ID'], n_input=params['n_input'],n_steps=params['n_steps'], n_hidden=params['n_hidden'], n_outputs=params['n_outputs'], n_layers=params['n_layers']   ) # should look like: networkParams(n_steps = params['n_steps'], n_layers = params['n_layers'] , ....)
        popOutAt = 0.5
        loss = self.model.trainKickOut(popOutAt) # Neeed to be implemented
        self.model = None
        return loss

    def runFitness(self):
        allLosses = []
        for i in range(len(self.pop)):
            loss = self.getLoss(i)
            allLosses.append(loss)

        maxVal = np.amax(allLosses)
        return [(1- (x/maxVal)) for x in allLosses] # lower loss, greater fitness

    def mate(self, p1, p2):
        holder = []
        childParams = dict()
        for key_p1, key_p2 in enumerate(p1, p2):
            whichPerson = self.randNum(0, "","") # return a number between 0 and 1
            if (whichPerson < 0.5):
                childParams[key_p1] = p1[key_p1]
            else:
                childParams[key_p2] = p2[key_p2]
        return childParams

    def randNum(self, typeR, _min, _max):
        # https://stackoverflow.com/questions/33359740/random-number-between-0-and-1-in-python
        x = int.from_bytes(os.urandom(8), byteorder="big") / ((1 << 64) - 1)
        if (typeR == "0"):
            return x
        else:
            return random.randint(_min, _max) * x

    def pickPerson(self):
        totalLossInPi = math.fsum(self.fitnessVals)
        maxNum = math.ceil(totalLossInPi)
        personAt = self.randNum(1, 0, maxNum)
        currFit = 0
        for i in range(self.fitnessVals):
            if currFit > personAt:
                return i
            currFit+= self.fitnessVals[0]

    def getNextGen(self):
        children = []
        person1 = -1
        person2 = -1
        for i in range(self.popSize):
            while(person1 == person2):
                # TODO based off of their fitness values, not just randomly
                person1 = self.pickPerson()
                person2 = self.pickPerson()
                x=0
            child = self.mate(person1, person2)
            children.append(child)
        return children

    def runToGeneration(self, maxGens):
        newPopulation = None
        for gen in range(maxGens):
            self.fitnessVals = self.runFitness()
            self.pop = self.getNextGen()
            return 0

    def createIndividual(self):
        # return an individual with a random set of network params
        # LSTM network params (self,ID, n_input = 1,n_steps = 11, n_hidden= 2, n_outputs = 5 , n_layers = 2, loading=False):
        params = dict()
        n = "" # nothing but a place holder of "nothing"
        params['id'] = -1 # denotes that its an LSTM used for genetic algorithm
        params['n_input'] = 1
        params['n_steps'] = self.randNum(n, 5, 100) # typeR, min, max
        params['n_hidden']= self.randNum(n, 1, 15)
        params['n_outputs'] = self.randNum(n, 1, 15)
        params['n_layers'] = self.randNum(n, 1, 10)

        return params

    def initPop(self):
        try:
            for x in range(self.popSize):
                indiv = createIndividual()
                self.pop.append(indiv)
        except:
            print("GeneticAlg says: Failed to initialize the population")

class renewableModel:
    def __init__(self, _id, dataFileTarget):
        self.id = _id
###
        self.NN = None
        self.NN_Models = []
###
        self.LSTM_Models = []
        self.dataFileTarget = Path.cwd().parent.joinpath(dataFileTarget)
        self.renewableModel_Test_accuracy = 0
        self.reTrainLSTM = False
        self.dataFrame = self.loadData()
        # TODO
        # Have this decrease each time its called
        self.testNum            = "20"      # Increase this each time
        self.highNoiseTarget    = .0009
        self.medNoiseTarget     = .0002
        self.lowNoiseTarget     = .00004
        self.anomalyTarget      = .000005
        self.highNoiseFeatures  = ["events", "gust_speed", "power_EMA60", "power_EMA90", "conditions", "wind_dir", "power_out_prev"]
        self.medNoiseFeatures   = ["power_MA10", "power_MA25", "dew_point", "visibility", "wind_speed" , "humidity"]
        self.lowNoiseFeatures   = ["pressure", "power_EMA30", "power_MA50", "temp"]
        self.anomalyFeatures    = ["precip"]

        self.config()

    def loadData(self):
        # Pull all data from CSV file and
        # push into a dataframe for portability.

        df = pd.read_csv(self.dataFileTarget, index_col=0, skiprows=[1])
        df.index = pd.to_datetime(df.index)

        return df

    def getNumOfFeats(self):
        # Return the number of features in the data
        return len([0 for x in self.dataFrame] - 1)  # -1 to remove power_output from the count

    def getSuperTestData(self, lookBackSize, ySize):
        # Grab a batch-sized batch of data

        arr_lookBack = []
        arr_futureFeature = []
        sizeof_dataframe = self.dataFrame.shape[0]
        sizeof_dataToPull = ySize + lookBackSize
        # print(sizeof_dataframe)

        # self.dataFrame location to pull data from
        start = int(sizeof_dataframe * np.random.rand())
        while (sizeof_dataframe < start + sizeof_dataToPull):
            start = int(sizeof_dataframe * np.random.rand())

        end_lookBack = start + lookBackSize
        end_actualY = start + sizeof_dataToPull

        for column in self.dataFrame:
            if column != "power_output":
                temp_arr = np.asarray(list(self.dataFrame[column][start:end_lookBack]))
                temp_arr = temp_arr.reshape(1,lookBackSize, 1)
                arr_lookBack.append(temp_arr)

                temp_future = np.asarray(list(self.dataFrame[column][end_lookBack:end_actualY]))
                arr_futureFeature.append(temp_future)


        arr_actualY = np.asarray(list(self.dataFrame["power_output"][end_lookBack:end_actualY]))
        arr_actualY = arr_actualY.reshape(ySize, 1)

        return arr_lookBack, arr_futureFeature, arr_actualY

    
    def getMaxLSTMParams(self):
        # Find max number of n_steps and n_outputs amongst all LSTMs
        maxBatchSize =  -100000 #self.LSTM_Models[0].n_steps
        maxYSize = -100000      # self.LSTM_Models[0].n_outputs

        for i in range(self.getNumOfFeats()):
            if (self.LSTM_Models[i].n_steps > maxBatchSize):
                maxBatchSize = self.LSTM_Models[i].n_steps
            if (self.LSTM_Models[i].n_outputs > maxYSize):
                maxYSize = self.LSTM_Models[i].n_outputs
        return maxBatchSize, maxYSize

    def masterTest(self):
        # batchSize:           number of past prediction to consider
        # ySize:               number of future predictions to consider
        # lookBackDataFeature: list of each LSTM's timestep data
        # futureFeature:       list of what each LSTM's future values should be
        # actual_Y:            list of power_output for each timestep

        maxBatchSize, maxYSize = self.getMaxLSTMParams()
        #lookBackDataFeature, futureFeature, actual_Y = self.getSuperTestData(maxBatchSize, maxYSize)

        numTests = 10
        masterTest_Accuracy_Avg = 0
        for k in range(numTests):
            numOfFeats = self.getNumOfFeats()
            features_forecasts = []
            lookBackDataFeature, futureFeature, actual_Y = self.getSuperTestData(maxBatchSize, maxYSize)

            for i in range(numOfFeats):
                steps = self.LSTM_Models[i].n_steps
                print("loobackdata: ", lookBackDataFeature[i] )
                # l, _, _ =  self.getSuperTestData(self.LSTM_Models[i].n_steps, self.LSTM_Models[i].n_outputs)  #lookBackDataFeature[i]
                lookBackData = np.array(lookBackDataFeature[i][0][maxBatchSize-steps:]) # to feed in the correct amount of values .. we have varying lookback for the LSTM_Models
                lookBackData = lookBackData.reshape(1, steps, 1)
                #print(lookBackDataFeature[i][0])
                #print(lookBackData)
                # TODO
                # NOTE: You can modify the codde in the forecastGiven
                # and add in the actual_Y.csv so that you can draw a graph
                # of the accuracy for each LSTM model.
                # investigate the code to figure out how to get it to work...
                # OR you can just do a straight up comparison in excel... but i woulnd't recommend that lol
                forecastForFeat_i = self.LSTM_Models[i].forecastGiven(lookBackData, futureFeature[i], self.testNum, k)
                features_forecasts.append(forecastForFeat_i)

            print("features_forecasts:", features_forecasts)

            forecasted_Power = []
            NNOnlyForecast = []
            testResults = []
            num_timeSteps = maxYSize
            difference = []
            graphTheTest = True
#            
            logFile = str(Path.cwd().parent.joinpath('superModelResults/resultsFor_'+str(self.testNum) + "_" + str(k)))
#
            with open(logFile, 'w') as csvFile:
                wr = csv.writer(csvFile, delimiter=",")
                renewableModel_Test_accuracy_MA = self.renewableModel_Test_accuracy
                # while renewableModel_Test_accuracy_MA < 0.50

                for timestep in range(num_timeSteps):
                    currFeatsInTimestep = []
                    actualFeatsInTimestep = []
                    for feature in features_forecasts:
                        currFeatsInTimestep.append(feature[0][timestep])
                    for act_feature in futureFeature:
                        actualFeatsInTimestep.append(act_feature[timestep])

                    currFeatsInTimestep.append(feature[0][0]) # Shouldnt have to do this but just a quick hack to get it to work..
                    actualFeatsInTimestep.append(feature[0][0])
                    wr.writerow([["currFeatsInTimestep_"+str(timestep)], currFeatsInTimestep])
                    #print("Feats in timestep: " + str(timestep), currFeatsInTimestep)
                    #print("currFeatsInTimestep :", currFeatsInTimestep)

###
                    curr_classification = self.NN.classifySetOf(currFeatsInTimestep)
###
                    # run the actual features in the future through the NN
                    prep = np.squeeze(actualFeatsInTimestep).tolist()
###
                    withRealFeatsClassification = self.NN.classifySetOf(prep)
###
                    NNOnlyForecast.append(withRealFeatsClassification)

                    act_Y = actual_Y[timestep][0]
                    pred_Y = curr_classification[0]
                    eclud_distance = math.sqrt((math.fabs((act_Y-pred_Y)**2 -  timestep)))
                    difference.append(eclud_distance)

                    wr.writerow([["curr_classification_"+str(timestep) + "_testNumer: " + str(k)], curr_classification])
                    forecasted_Power.append(curr_classification)

                wr.writerow([["Actual y: "], actual_Y])
                wr.writerow([["Actual features: "], futureFeature])

                if (graphTheTest):
                    #plt.subplot(numTests, 1, k)
                    time = [x for x in range(num_timeSteps)]
                    actY = np.squeeze(actual_Y)
                    actY = actY.tolist()

                    plt.plot(time,actY, color='green')
                    forecasts = np.squeeze(forecasted_Power).tolist()
                    plt.plot(time,forecasts, color='red' , linestyle=':')
                    NNOnlyResults = np.squeeze(NNOnlyForecast).tolist()
                    plt.plot(time, NNOnlyResults, color='blue', linestyle=':')
                    plotName = "ActualY_vs_Predicted_NN_"+self.testNum+"_"+str(k)+".svg"
                    plt.xlabel('time')
                    plt.ylabel('poweroutput')
                    plt.title(plotName)

                    
                    # plt.savefig("graphs/NN/"+plotName, format="svg" )
                    plt.savefig(str(Path.cwd().parent.joinpath('LOG/Graphs/NN/' + 'plotName')), format="svg" )
                    
                    #plt.show()
                masterTest_Accuracy_Avg+= math.fsum(difference)

            print("forecasted_Power: ", forecasted_Power)

        errorThreshold = 13.48 # error froom seq off by 1 , 2 , 3 , 4 ... N respective to time
        masterTest_Accuracy_Avg/=numTests
        if (errorThreshold <= masterTest_Accuracy_Avg):
            self.reTrainLSTM = True
            print("Accuracy hit! time to celebrate")

            # self.train(1)
        else:
            time = [x for x in range(num_timeSteps)]
            actY = np.squeeze(actual_Y)
            actY = actY.tolist()
            plt.plot(time,actY, color='green', linestyle=':')
            forecasts = np.squeeze(forecasted_Power).tolist()
            plt.plot(time,forecasts, color='red')
            plt.show()
###
        self.NN.closeSession()
###
        return 0

    def train(self, state):
        # thread each model for training
        # continue training until NN > 95%
        if (state == 0):
            NN_targetAcc = .95
###     
        for i in range(12):
            #self.NN.train(NN_targetAcc)
            self.NN_Models[i].train(NN_targetAcc)
###
        i = 0;
        for column in self.dataFrame:

            if column in self.highNoiseFeatures:
                self.LSTM_Models[i].train(target_loss=self.highNoiseTarget)
                i += 1
            elif column in self.medNoiseFeatures:
                self.LSTM_Models[i].train(target_loss=self.medNoiseTarget)
                i += 1
            elif column in self.lowNoiseFeatures:
                self.LSTM_Models[i].train(target_loss=self.lowNoiseTarget)
                i += 1
            elif column in self.anomalyFeatures:
                self.LSTM_Models[i].train(target_loss=self.anomalyTarget)
                i += 1

        self.masterTest()

    def findOptimalParametersForLSTMS(self):
        populationSize = 10
        maxGeneration = 5
        for column in self.dataFrame:
            modelName = column
            population = GeneticAlg(populationSize, modelName)
            optimalVals = population.runToGeneration(maxGeneration)
            self.optimalLSTMParamsFor[column] = optimalVals

    def config(self):
        # initialize the NN
            # selecting network parameters?
        # trainingDataPath = self.dataFileTarget # 12 is the most recent data with richer features (EMA)   
####
        currentRow = 0
        totalRows = len(self.dataFrame.index)
        rowBatch = int(totalRows/12)
        for i in range(12):
            nn_dataFrame = self.dataFrame[currentRow:rowBatch+currentRow]
            currentRow += rowBatch
            #self.NN = NN.neuralNetwork(self.id, dataFileTarget=trainingDataPath) # configure options for NN ==  dataFileTarget="", LOG_DIR="LSTM_LOG/log_tb/temp", batchSize=144, hiddenSize=256, displaySteps=20):
            self.NN_Models.append(NN.neuralNetwork(i, dataFrame=nn_dataFrame))     
        # trainingDataPath = self.dataFileTarget # 12 is the most recent data with richer features (EMA)
        # self.NN = NN.neuralNetwork(self.id, dataFileTarget=trainingDataPath) # configure options for NN ==  dataFileTarget="", LOG_DIR="LSTM_LOG/log_tb/temp", batchSize=144, hiddenSize=256, displaySteps=20):
        self.optimalLSTMParamsFor = dict()
        self.findOptimalParametersForLSTMS()
####
        # initialize the LSTMS
            # couont how many features there are
        for column in self.dataFrame:
            if column != "power_output": # TODO maybe don't include moving averages
                curr_lstm = modelBuilder_LSTM.StackedLSTM(dataFrame=self.dataFrame[column], modelName=(column + "/" + column + self.testNum))
                if column in self.highNoiseFeatures:
                    generatedNetworkParams = self.optimalLSTMParamsFor[column]
                    # TODO
                    # Pass in the generatedNetworkParams from genetic algorithm
                    curr_lstm.networkParams(column, n_steps=20, n_layers=5) # can pass in custom configurations Note: necessary to call this function
                    self.LSTM_Models.append(curr_lstm)
                elif column in self.medNoiseFeatures:
                    curr_lstm.networkParams(column, n_steps=42, n_layers=3) # can pass in custom configurations Note: necessary to call this function
                    self.LSTM_Models.append(curr_lstm)
                elif column in self.lowNoiseFeatures:
                    curr_lstm.networkParams(column, n_steps=12, n_layers=4) # can pass in custom configurations Note: necessary to call this function
                    self.LSTM_Models.append(curr_lstm)
                elif column in self.anomalyFeatures:
                    curr_lstm.networkParams(column, n_steps=10, n_layers=5) # can pass in custom configurations Note: necessary to call this function
                    self.LSTM_Models.append(curr_lstm)

        # start training the models
        self.train(0)

    def printID(self):
        print("ID: ", self.id)

class superModel:
    """ This class represents a single town, where the town may contain more than
        one renewable source of energy. Each source has a unique Neural Net dedicated
        to classifying environmental features.
    """
    def __init__(self, numOfRenewables):
        self.renewableModels = []
        for i in range(numOfRenewables):
            self.renewableModels.append(renewableModel(i, "prod_Data/training_Data12.csv"))
        self.renewableModels[0].printID()

if __name__ == "__main__":
    numOfRenewables = 1
    SM = superModel(numOfRenewables)

            # w/ lstm configuration of : def networkParams(self,ID, n_input = 1,n_steps = 11, n_hidden= 2, n_outputs = 5 , n_layers = 2, loading=False  ):
            # 1 - .20 % NN, .5 loss LStm
            # 2 - 0.90 % NN, 0.01 loss LSTM
            # w/ lstm configuration of :     def networkParams(self,ID, n_input = 1,n_steps = 11, n_hidden=20, n_outputs = 5 , n_layers = 5, loading=False  ):
            # 3 - 0.95 % NN, 0.001 loss LSTM
            # 4 - 0.97 % NN, 0.0001 loss lstm

            # 5 - 0.95  % NN, 0.05 lss lstm decrements by 0.01 if testing does not meet requirements
            # 6 - 0.965 % NN, 0.003 loss lstm decrements by 0.01 if testing does not meet requirements
            #     n_steps=18, n_layers=18
            # 7 - 0.97  % NN, .003 loss lstm decrements by 0.01 if testing does not meet requirements
            #     n_steps=12,n_layers=4
            # 8   0.97  % NN, .002 loss lstm decrements by 0.01 if testing does not meet requirements
            #     n_steps=24,n_layers=4
            # 9   0.97  % NN, .001 loss lstm decrements by 0.01 if testing does not meet requirements
            #     n_steps=36,n_layers=4
            # 10
            #     Noisy events | gust_speed
            #     0.97  % NN, .001 loss lstm decrements by 0.01 if testing does not meet requirements
            #     n_steps=40,n_layers=4
            #     Smooth
            #     0.97  % NN, .0001 loss lstm decrements by 0.01 if testing does not meet requirements
            #     n_steps=18,n_layers=4
            # 11
            #* self.highNoiseTarget    = .001            n_steps=20, n_layers=4
            #* self.medNoiseTarget     = .0001           n_steps=40, n_layers=4
            # self.lowNoiseTarget     = .00001          n_steps=18, n_layers=3
            # self.highNoiseFeatures  = ["events", "gust_speed", "power_EMA60", "power_EMA90", "conditions", "wind_dir", "power_out_prev"]
            # self.medNoiseFeatures   = ["power_MA10", "power_MA25", "dew_point", "visibility", "wind_speed", "temp", "humidity"]
            # self.lowNoiseFeatures   = ["pressure", "precip", "power_EMA30", "power_MA50"]
            # 12
            # self.highNoiseTarget    = .0009           n_steps=8, n_layers=4
            # self.medNoiseTarget     = .0001           n_steps=24, n_layers=4
            #* self.lowNoiseTarget     = .00001          n_steps=11, n_layers=4
            # self.highNoiseFeatures  = ["events", "gust_speed", "power_EMA60", "power_EMA90", "conditions", "wind_dir", "power_out_prev"]
            # self.medNoiseFeatures   = ["power_MA10", "power_MA25", "dew_point", "visibility", "wind_speed" , "humidity"]
            # self.lowNoiseFeatures   = ["pressure", "precip", "power_EMA30", "power_MA50", "temp"]
            # 13
            # self.highNoiseTarget    = .0009           n_steps=14, n_layers=4
            # self.medNoiseTarget     = .0002           n_steps=12, n_layers=4
            # self.lowNoiseTarget     = .00004          n_steps=7, n_layers=4
            # self.highNoiseFeatures  = ["events", "gust_speed", "power_EMA60", "power_EMA90", "conditions", "wind_dir", "power_out_prev"]
            # self.medNoiseFeatures   = ["power_MA10", "power_MA25", "dew_point", "visibility", "wind_speed" , "humidity"]
            # self.lowNoiseFeatures   = ["pressure", "precip", "power_EMA30", "power_MA50", "temp"]
            # 14 
            # self.highNoiseTarget    = .0009           n_steps=144, n_layers=3
            # self.medNoiseTarget     = .0002           n_steps=42, n_layers=3
            # self.lowNoiseTarget     = .00004          n_steps=12, n_layers=4
            # self.anomalyTarget      = .000005         n_steps=10, n_layers=5
            # self.highNoiseFeatures  = ["events", "gust_speed", "power_EMA60", "power_EMA90", "conditions", "wind_dir", "power_out_prev"]
            # self.medNoiseFeatures   = ["power_MA10", "power_MA25", "dew_point", "visibility", "wind_speed" , "humidity"]
            # self.lowNoiseFeatures   = ["pressure", "power_EMA30", "power_MA50", "temp"]
            # self.anomalyFeatures    = ["precip"]
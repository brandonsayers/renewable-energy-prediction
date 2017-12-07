# Rocco Haro
class renewableModel:
    def __init__(self, _id):
        self.id = _id
        self.NN = None
        self.LSTM_Models = None
        self.config()

    def masterTest(self):
        # for n number of test:
            # y, testInput = getSample()
            # for each feature in batch:
                #feat_forecast.append(sess.run(self.LSTM_Models[feature], stripFeatureSequence(feature/idx, testInput)))
            # for t in timeSteps:
                # curr_forecast = formatFeatureSet(feat_forecast, timestep)
                # power_forecast.append(self.NN, curr_forecast)
            # display(power_forecast, y)
        return 0

    def train(self):
        # thread each model for training
        # continue training until NN > 95%
        # and loss over all feature models are satisfactory
        self.masterTest()

    def config(self):
        # initialize the NN
            # selecting network parameters?

        # initialize the LSTMS
            # couont how many features there are

        # for each F in len(features):
            # create lstm model for each feature

        # start training the models
        self.train():

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
            self.renewableModels.append(renewableModel(i))

        self.renewableModels[0].printID()

if __name__ == "__main__":
    numOfRenewables = 1
    SM = superModel(numOfRenewables)

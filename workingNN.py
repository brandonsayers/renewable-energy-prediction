# Implementation of a simple MLP network with one hidden layer. Tested on the iris data set.
# Requires: numpy, sklearn>=0.18.1, tensorflow>=1.0

# NOTE: In order to make the code simple, we rewrite x * W_1 + b_1 = x' * W_1'
# where x' = [x | 1] and W_1' is the matrix W_1 appended with a new row with elements b_1's.
# Similarly, for h * W_2 + b_2

# code from https://gist.github.com/vinhkhuc/e53a70f9e5c3f55852b0

import tensorflow as tf
import numpy as np
import pandas as pd
import random
from pathlib import Path
from sklearn import datasets
from sklearn.model_selection import train_test_split

RANDOM_SEED = 42
tf.set_random_seed(RANDOM_SEED)

# Added dataFrame to parameters
# Added ID to end of LOG_DIR
# Made num_labels dynamic to dataframe passed in


class neuralNetwork:
    def __init__(self, ID, dataFrame=None, dataFileTarget=None, batchSize=576, hiddenSize=256, displaySteps=20):
        self.ID  = ID
        self.dataFileTarget = dataFileTarget
        self.LOG_DIR = str(self.getLogFilePath('NN_LOG/NN'+str(ID)))

        self.batchSize = batchSize
        self.hiddenSize = hiddenSize
        self.displaySteps = displaySteps

        if dataFrame is None:
            self.df = self.loadFile()
        else:
            self.df = dataFrame

        #self.train(1)

    def getLogFilePath(self, ID):
        # Path to project log file
        logFile = Path.cwd().parent.joinpath('LOG/' + ID)

        print('NN logfile path: ' + str(logFile))
        return logFile

    def loadFile(self):
        # File path to the input data
        trainLink = Path.cwd().parent.joinpath(str(self.dataFileTarget))
        print('NN loadfile path: ' + str(trainLink))

        # Load all data into dataframe
        df = pd.read_csv(trainLink, index_col=0, skiprows=[1], encoding='utf-8', engine='python')
        df.index = pd.to_datetime(df.index)

        return df

    def init_weights(self, shape):
        """ Weight initialization """
        weights = tf.random_normal(shape, stddev=0.1)
        return tf.Variable(weights)

    def forwardprop(self, X, w_1, w_2):
        """
        Forward-propagation.
        IMPORTANT: yhat is not softmax since TensorFlow's softmax_cross_entropy_with_logits() does that internally.
        """
        h    = tf.nn.sigmoid(tf.matmul(X, w_1))  # Sigmoid function [0, 1]
        yhat = tf.matmul(h, w_2)  # The \varphi function
        return yhat

    def getOneBatch(self):
        arrX = []
        arrY = []

        totalRows = len(self.df.index)

        # Randomly select a day
        start = random.randrange(0, totalRows)
        while(start > self.df.shape[0] - self.batchSize):   # Out of bounds exception
            start = random.randrange(0, totalRows)
        end = start + self.batchSize

        # Pull the day's data
        arrX = self.df.ix[start:end,'temp':].values
        arrY = self.df['power_output'][start:end].astype(int)

        return np.array(arrX), np.array(arrY)

    def get_data(self):
        """  """
        data, target = self.getOneBatch()

        # Prepend the column of 1s for bias
        N, M  = data.shape
        all_X = np.ones((N, M + 1))
        all_X[:, 1:] = data

        # Convert into one-hot vectors
        num_labels = self.df['power_output'].max() + 1
        ############## num_labels = Number of unique power prediction numbers

        # One liner trick!
        all_Y = np.eye(num_labels)[target]
        return train_test_split(all_X, all_Y, test_size=0.2, random_state=RANDOM_SEED)

    def train(self, targetAcc):
        train_X, test_X, train_y, test_y = self.get_data()
        # Layer's sizes
        x_size = train_X.shape[1]   # Number of input nodes
        h_size = self.hiddenSize    # Number of hidden nodes
        y_size = train_y.shape[1]   # Number of outcomes

        # Symbols
        self.X = tf.placeholder("float", shape=[None, x_size])
        self.y = tf.placeholder("float", shape=[None, y_size])

        # Weight initializations
        w_1 = self.init_weights((x_size, h_size))
        w_2 = self.init_weights((h_size, y_size))

        # Forward propagation
        yhat    = self.forwardprop(self.X, w_1, w_2)
        self.predict = tf.argmax(yhat, axis=1)

        # Backward propagation
        cost    = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(labels=self.y, logits=yhat))
        updates = tf.train.GradientDescentOptimizer(0.07).minimize(cost)

        # Run SGD
        self.sess = tf.Session()
        init = tf.global_variables_initializer()
        self.sess.run(init)
        test_accuracy = 0
        ema_train_acc = 0
        ema_test_acc = 0
        epoch = 0

        # Run Tensorboard
        writer = tf.summary.FileWriter(self.LOG_DIR, self.sess.graph)

        while (ema_test_acc < targetAcc):
            train_X, test_X, train_y, test_y = self.get_data()
            # Train with each example
            for i in range(len(train_X)):
                self.sess.run(updates, feed_dict={self.X: train_X[i: i + 1], self.y: train_y[i: i + 1]})

            train_accuracy = np.mean(np.argmax(train_y, axis=1) ==
                                     self.sess.run(self.predict, feed_dict={self.X: train_X, self.y: train_y}))
            test_accuracy  = np.mean(np.argmax(test_y, axis=1) ==
                                     self.sess.run(self.predict, feed_dict={self.X: test_X, self.y: test_y}))

            ema_train_acc = ( (10*train_accuracy) + (ema_train_acc * 90) ) / 100
            ema_test_acc = ( (10*test_accuracy) + (ema_test_acc * 90) ) / 100

            test_sum = tf.Summary(value=[tf.Summary.Value(tag="test_accuracy", simple_value=test_accuracy),])
            writer.add_summary(test_sum, epoch)
            #train_summ = tf.Summary(value=[tf.Summary.Value(tag="train_accuracy", simple_value=train_accuracy),])
            #writer.add_summary(train_summ, epoch)
            writer.flush()

            print("Epoch = %d, train accuracy = %.2f%%, test accuracy = %.2f%% | %.2f%%"
                  % (epoch + 1, 100. * train_accuracy, 100. * test_accuracy, 100. * ema_test_acc))
            epoch+=1


    def closeSession(self):
        self.sess.close()

    def classifySetOf(self, feats):
        # start a new session and run a classification with the already created model
        # against the passes in feats
        
        train_X, test_X, train_y, test_Y = self.get_data()
        #print("test_X: ", test_X[0])
        #print("test_Y: ", test_Y[0])
        print(" feats running through NN: ", feats)
        p = self.sess.run(self.predict, feed_dict={self.X: [feats], self.y: [test_Y[0]]})
        #print("argmax: ", np.argmax([test_Y[0]], axis=1))
        val = np.mean(np.argmax([test_Y[0]], axis=1) == p)
        #print("val: ", val)
        return p


# trainLink = Path.cwd().parent.joinpath('prod_Data/training_Data12.csv')
# df = pd.read_csv(trainLink, index_col=0, skiprows=[1], encoding='utf-8', engine='python')
# df.index = pd.to_datetime(df.index)
# neuralNetwork(1, df, 'prod_Data/training_Data12.csv')


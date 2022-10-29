from sklearn.cluster import KMeans
from tensorflow import keras

#import random 
#from random import seed

import time
import numpy as np
from lib.EvalMetrics import *

#def cluster_label_count(clusters, labels):
 #   count = {}

    # Get unique clusters and labels
#    unique_clusters = list(set(clusters))
#    unique_labels = list(set(labels))

    # Create counter for each cluster/label combination and set it to 0
 #   for cluster in unique_clusters:
 #       count[cluster] = {}

 #       for label in unique_labels:
 #           count[cluster][label] = 0
#
    # Let's count
#    for i in range(len(clusters)):
 #       count[clusters[i]][labels[i]] += 1

 #   cluster_df = pd.DataFrame(count)

 #   return cluster_df, count

'''Function to compute softmax of the custom layer'''
def softmax(array):
    
    if(len(array.shape)==2):
        array = array[0]
        
    size    = len(array)
    ret_ary = np.zeros([len(array)])
    m       = array[0]
    sum_val = 0

    for i in range(0, size):
        if(m<array[i]):
            m = array[i]

    for i in range(0, size):
        sum_val += np.exp(array[i] - m)

    constant = m + np.log(sum_val)
    for i in range(0, size):
        ret_ary[i] = np.exp(array[i] - constant)
        
    return ret_ary


''' Function to transform a label saved as a char to an hot-one encoded array where the 1 is put in the correct label position '''
def DigitToSoftmax(current_label, known_labels):
    ret_ary = np.zeros(len(known_labels))

    # known_labels_2 = [0,1,2,3,4,5]
                       
    for i in range(0, len(known_labels)):
        if(current_label == known_labels[i]):
            ret_ary[i] = 1

    return ret_ary  

#def NumberToSoftmax(current_label, known_labels):
#    ret_ary = np.zeros(len(known_labels))
#                     
#    for i in range(0, len(known_labels)):
#        if(current_label == known_labels[i]):
#            ret_ary[i] = 1
#
#    return ret_ary






''' Function that initializes a KMean clustering object and trains it on the dataset provided'''
def create_k_mean(data, number_of_clusters, verbose = False):

    # n_jobs is set to -1 to use all available CPU cores. This makes a big difference on an 8-core CPU
    # especially when the data size gets much bigger. #perfMatters

    k = KMeans(n_clusters=number_of_clusters, n_init=100)
    # k = KMeans(n_clusters=number_of_clusters, n_init=20, max_iter=500)

    # Let's do some timings to see how long it takes to train.
    start = time.time()

    # Train it up
    k.fit(data)

    # Stop the timing
    end = time.time()

    # And see how long that took
    if verbose:
        print("Training took {} seconds".format(end - start))

    return k



  

'''Function to compute confusion matrix between cluster and labels'''
def confusion_matrix2(clusters_features_saved, labels_features_saved_init, cluster_list, labels_list):

  cmtx = np.zeros([len(labels_list), len(cluster_list)])

  for i in range(0, len(clusters_features_saved)):

    cluster = clusters_features_saved[i]
    label = labels_features_saved_init[i]

    # Find indices
    m = labels_list.index(label)
    n = cluster_list.index(cluster)
    cmtx[m,n] += 1
  return cmtx

'''Function to map the cluster index with the pseudo labels. The function must be run only on the saved_dataset'''
def cluster_to_label(clusters_features, labels_features, cluster_list, labels_init_list):

  # 1: Compute Confusion matrix (for the saved features)
  cmtx = confusion_matrix2(clusters_features, labels_features, cluster_list, labels_init_list)

  # 2: Find max in each row -> cluster corresponding to each label
  map_idx = np.argmax(cmtx, axis = 1)  

  # print(map_idx)

  # Fill dictionary with map
  map_clu2lbl = {}
  map_lbl2clu = {}
  # labels_init_list_sorted = labels_init_list.sort()
  labels_init_list.sort()
  for i in range(0, len(map_idx)):
    map_clu2lbl[map_idx[i]] = labels_init_list[i]
    map_lbl2clu[labels_init_list[i]] = map_idx[i]
  
  # Mapping dictionary
  # map_clu2lbl -> cluster: label
  # map_lbl2clu -> label: cluster

  #print("LABEL: CLUSTER", map_lbl2clu)
  #print("CLUSTER: LABEL", map_clu2lbl)

  # DEBUG
  #if len(map_clu2lbl) < 10:
  #  print(cmtx)

  return map_clu2lbl, map_lbl2clu


class Custom_Layer(object):
    def __init__(self, model):

        # Related to the layer
        self.ML_frozen = keras.models.Sequential(model.layers[:-1])  # extract the last layer from the original model
        self.ML_frozen.compile()
        
        self.W = np.array(model.layers[-1].get_weights()[0])    # extract the weights from the last layer
        self.b = np.array(model.layers[-1].get_weights()[1])    # extract the biases from the last layer
               
        self.W_2 = np.zeros(self.W.shape)
        self.b_2 = np.zeros(self.b.shape)
        
        self.label     = [0,1,2,3,4,5]              
        self.std_label = [0,1,2,3,4,5,6,7,8,9]
        
        self.l_rate = 0                                         # learning rate that changes depending on the algorithm        

        self.batch_size = 0
        
        # Related to the results fo the model
        self.conf_matr = np.zeros((10,10))    # container for the confusion matrix       
        self.macro_avrg_precision = 0       
        self.macro_avrg_recall = 0
        self.macro_avrg_F1score = 0
        
        self.title = ''       # title that will be displayed on plots
        self.filename = ''    # name of the files to be saved (plots, charts, conf matrix)
        
    # Function that is used for the prediction of the model saved in this class
    def predict(self, x):
        mat_prod = np.array(np.matmul(x, self.W) + self.b)
        return softmax(mat_prod) # othwerwise do it with keras|also remove np.array()| tf.nn.softmax(mat_prod) 
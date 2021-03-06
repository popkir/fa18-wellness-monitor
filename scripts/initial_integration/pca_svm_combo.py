import numpy as np
import pandas as pd  
import itertools as it

from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn import datasets
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.svm import SVC
from sklearn.multiclass import OneVsRestClassifier
from sklearn.multiclass import OutputCodeClassifier

#########################################
# Setting of the parameters
#########################################

# should I do PCA or not?
do_pca = 1
# number of final features after dimensionality reduction
dimensions = 3

# set the kernel here: poly, rbf, linear is basically poly at degree 1
kernel = 'poly'
# these are for the polynomial kernel only
degree = 1
coef = 0
# how many classes?
classes = 2
# set the classifier type: ovr, ovo, ecoc
class_type = 'ovr'

# what dataset to use? 'actual' or 'toy' data?
dataset = 'actual'
# test using the train data?
cheat_test = 0


#########################################
# Load the dataset
#########################################

# Replace this block with your data
# Make sure that the data is a 2D array of size nSamples x nFeatures

if classes == 2:
    #Load dataset
    cancer = datasets.load_breast_cancer()
    X = cancer.data
    y = cancer.target

elif classes == 3 or classes == 4:
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data"
    # Assign colum names to the dataset
    colnames = ['sepal-length', 'sepal-width', 'petal-length', 'petal-width', 'Class']
    # Read dataset to pandas dataframe
    irisdata = pd.read_csv(url, names=colnames)
    X = irisdata.drop('Class', axis=1)  
    y = irisdata['Class']
    y = np.array(pd.Categorical(pd.factorize(y)[0]))
    if classes == 4:
        y[120:129] = [3,3,3,3,3,3,3,3,3] # just messing around to check my algo for 4 classes

#########################################
# Splitting of the dataset
#########################################

if cheat_test == 1:
    # Split dataset into training set and test set
    # 70% training and 30% test
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.3, random_state=109) 
else:
    X_train = X
    X_test = X
    y_train = y
    y_test = y

#########################################
# Normalization of the training dataset
#########################################

# we must transform the data to 0 mean and 1 std
# for conventional machine learning algorithms to work
params = StandardScaler().fit(X_train)
X_train_mean = params.mean_
X_train_var = params.var_

# normalization is basically (x - mean) / std
X_train = (X_train - X_train_mean)/np.sqrt(X_train_var)

#########################################
# Perform PCA on the training set
#########################################

if do_pca == 1:

    # pick the number of components to retain, top 3 in this case
    pca = PCA(n_components=dimensions)
    
    # perform the transformation to the new dimension
    # use this to verify that you got the correct dot product
    principalComponents = pca.fit_transform(X_train)
    
    # this gives you the weights per feature for the new transformed space
    # principal components x number of features
    # this is what will be provided for the system
    # this is a p x f matrix:
    # p = number of principal components you select (reduced dimension target)
    # f = number of original features (the original dimension)
    pca.components_
    
    ##############################################################
    # mapping the new sample to the new set of dimensions is simply a dot product
    # the only thing that you have to do in chisel?
    # x is the data that needs to be projected, s x f matrix:
    # s = number of samples to be projected
    # f = number of original features
    # s x f dot product with f x p, gives us s x p, the samples in the reduced dimension space
    X_train = np.matmul(X_train,pca.components_.T)

    # you can compare principalComponents and transformed,
    # they should be approximately equal

#########################################
# Create a SVM Classifier
#########################################

# for more information, check out this link: http://scikit-learn.org/stable/modules/multiclass.html
if class_type == 'ovr':
    clf = OneVsRestClassifier(SVC(kernel=kernel, gamma=1, coef0=coef, degree=degree, max_iter=1e4))
elif class_type == 'ovo':
    clf = SVC(kernel=kernel, gamma=1, coef0=coef, degree=degree, max_iter=1e4) # SVC is ovo by default, contrary to documentation
elif class_type == 'ecoc':
    clf = OutputCodeClassifier(SVC(kernel=kernel, gamma=1, coef0=coef, degree=degree, max_iter=1e4), random_state=109)

# Train the model using the training sets
clf.fit(X_train, y_train)

#########################################
# Normalization of the testing dataset
#########################################

# Before projecting the test set, it must also be normalized
# However, it should be normalized using the training set data
# This avoids future data leaking into the algorithm
X_test = np.array(X_test)   # we're using numpy here
X_test = (X_test - X_train_mean)/np.sqrt(X_train_var)

#########################################
# Projection of the test set to the new principal axes
#########################################
if do_pca == 1:
    X_test = np.matmul(X_test,pca.components_.T)

#########################################
# Now do the classification. 
# This is the preprocessing step so that you just feed data to the generator
# It creates the alpha vector, support vector, and intercepts 
#########################################

# one vs one classification creates pairwise combinations of all classes as classifier
# we need to create a classifier map for these pairwise combinations
# we will also arrange the alphas accordingly, since the SVC function from sklearn is too optimized...
if class_type == 'ovo':
    # extract parameters from the SVC function
    alphas = clf.dual_coef_
    supports = clf.support_vectors_
    intercept = clf.intercept_

    # create the indices for the alpha vector expansion
    support_index = np.concatenate(([0],np.cumsum(clf.n_support_)))
    
    # generate the combination maps for the alphas
    combo_map = np.zeros((classes,classes-1,2))
    for i in range(classes):
        for j in range(i+1,classes):
            # i and j contains the combination
            combo_map[i,j-1] = [i,j]
            combo_map[j,i] = [i,j]
    
    # generate the mask to extract the corresponding alpha array, per combination
    # read the sklearn SVC documentation for more details on how the alphas are arranged
    # http://scikit-learn.org/stable/modules/svm.html#svm-classification
    class_pairs = np.array(list(it.combinations(list(range(classes)),2)))
    alpha_vector = np.zeros((len(class_pairs),len(alphas[0])))
    
    for x in range(len(class_pairs)):
        mask_map = np.zeros((classes,classes-1))
        for i in range(classes):
            for j in range(classes-1):
                mask_map[i,j] = (combo_map[i,j] == class_pairs[x]).all()
                if(mask_map[i,j]):
                    alpha_vector[x,support_index[i]:support_index[i+1]] = alphas[j,support_index[i]:support_index[i+1]]

    num_classifiers = len(class_pairs) # also classes * (classes - 1) /2
    
    # this is the raw votes, test for equality here
    decision1 = clf.decision_function(X_test)

# one vs rest classification creates 1 classifier per class
# we just need to combine all support vectors and setup the corresponding alpha vector
elif class_type == 'ovr':
    if classes == 2:
        classes = 1     # pseudo fix since 2 classes = 1 classifier, 3 classes = 3 classifiers, so 2 is a special case

    support_index = np.array([0])
    for i in range(classes):    # count the number of alphas and extract the indices
        support_index = np.concatenate((support_index,[support_index[-1]+clf.estimators_[i].dual_coef_.shape[1]]))
        
    alpha_vector = np.zeros((classes,support_index[-1]))
    # get initial values, at index 0
    alpha_vector[0,support_index[0]:support_index[1]] = clf.estimators_[0].dual_coef_
    supports = clf.estimators_[0].support_vectors_
    intercept = clf.intercept_
    
    # create the alpha vector and support vector list by iterating through the estimators
    for i in range(1,classes):
        alpha_vector[i,support_index[i]:support_index[i+1]] = clf.estimators_[i].dual_coef_
        supports = np.concatenate((supports,clf.estimators_[i].support_vectors_))
        
    num_classifiers = classes
    
    # this is the raw votes, test for equality here
    decision1 = clf.decision_function(X_test)

# error-correcting output codes utilize some code book which is a binary permutation to represent each class
# the number of classifiers will depend on the user, the more classifiers, the more robust it becomes
# this is because classification is performed by calculating the hamming distances
# setup if almost similar to the one vs rest, where we just combine all support vectors and corresponding alphas
elif class_type == 'ecoc':
    codes = clf.code_book_ # the generated table by the algorithm, pass this as a parameter to the generator
    #codes[codes == -1] = 0 # just to make it 0 and 1
    num_classifiers = codes.shape[1]
    
    # ok, we will assume that there's no constant predictor, else it will mess up with the logic
    # the following block is somewhat similar to the one vs rest code above
    support_index = np.array([0])
    for i in range(num_classifiers):    # count the number of alphas
        support_index = np.concatenate((support_index,[support_index[-1]+clf.estimators_[i].dual_coef_.shape[1]]))
        
    alpha_vector = np.zeros((num_classifiers,support_index[-1]))
    # get initial values, at index 0
    alpha_vector[0,support_index[0]:support_index[1]] = clf.estimators_[0].dual_coef_
    supports = clf.estimators_[0].support_vectors_
    intercept = clf.estimators_[0].intercept_
    
    for i in range(1,num_classifiers): 
        alpha_vector[i,support_index[i]:support_index[i+1]] = clf.estimators_[i].dual_coef_
        supports = np.concatenate((supports,clf.estimators_[i].support_vectors_))
        # extract the intercept from every estimator
        intercept = np.concatenate((intercept,clf.estimators_[i].intercept_))

########################################################################################
# Here's what will be passed to the generator
# pca.components_ = the transformation matrix to reduce the dimensions (PCA)
# supports = the support vectors s x f, s=number of vectors, f=features
# intercept = the training intercept 1 x c, c=number of classifiers to create
# alpha_vector = the support vector weights c x f
# must also pass the clf.code_book_ as an argument
########################################################################################

# function to translate the array to string, then format it to be compatible with C code
def print_array_to_file(f,array_name):
    array_container = repr(array_name)
    array_container = array_container.replace('array','').replace('(','').replace(')','')
    array_container = array_container.replace('[','{').replace(']','}')
    array_container = array_container.replace('. ','')
    f.write(array_container)
    f.write(";\n\n")

f = open("generated_files/C_arrays.txt","w")

# the PCA transformation matrix
f.write("double PCAComponents[][] = ")
print_array_to_file(f,pca.components_)

# the support vector weights, the alpha vector
f.write("double SVMAlphaVector[][] = ")
print_array_to_file(f,alpha_vector)

# the actual support vectors
f.write("double SVMSupportVector[][] = ")
print_array_to_file(f,supports)

# the SVM intercept
f.write("double SVMIntercept[] = ")
print_array_to_file(f,intercept)

f.close()

# the codebook for ECOC, to be passed as a Scala parameter
if (class_type == "ecoc"):
    f = open("generated_files/Scala_codebook.txt","w")
    f.write("val codeBook = ")
    array_container = repr(codes)
    array_container = array_container.replace('array','').replace('(','').replace(')','')
    array_container = array_container.replace('[','Seq(').replace(']',')')
    array_container = array_container.replace('.,',',').replace('.)',')')
    f.write(array_container)
    f.close()

########################################################################################
# This is the part that will be implemented in Chisel
########################################################################################
                
# This is where the kernel goes
# Select the corresponding kernel calculation
if kernel == 'poly':
    # polynomial kernel, varying degrees
    # if you want linear, set coef = 0, degree = 1
    kernel_dotproduct = np.power((coef + np.matmul(supports,X_test.T)),degree) 

elif kernel == 'rbf': # this is so tricky!
    # rbf kernel
    kernel_dotproduct = np.zeros((len(supports),len(X_test)))
    for i in range(len(supports)): # loop for all support vectors
        for j in range(len(X_test)): # loop for all test data samples
            kernel_dotproduct[i,j] = np.exp(-sum((supports[i] - X_test[j]) ** 2))
            
else:
    kernel_dotproduct = np.matmul(supports,X_test.T)
    
# kernel_dotproduct will be computed given the test set and support vectors
decision2 = np.matmul(alpha_vector,kernel_dotproduct)
# add the intercept after doing the dot product with the alphas
decision2 = decision2 + np.matmul(intercept.reshape((num_classifiers,1)),np.ones((1,len(X_test.T[0]))))
decision2 = decision2.T

# set votes to 0 or 1
vote = decision2 > 0
# change boolean to int, then convert as list
vote = np.ndarray.tolist(vote.astype(int))
# initialize container of final predicted classes using manual calculation
y_manual = np.zeros((len(vote),1))

if class_type == 'ovo':
    # create the votes from the values of the decision function (vote)
    for i in range(len(X_test)):
        for j in range(num_classifiers):
            if classes > 2:     # binary classification is a special case since that only has 1 classifier
                vote[i][j] = class_pairs[j][1-vote[i][j]]
            else:
                vote[i][j] = class_pairs[j][vote[i][j]]
            # I did 1-x since 1 must correspond to the first of the pair
            # this is just index manipulation, 0 -> 1, 1 -> 0
            
        # find the max votes, that will be the final class
        y_manual[i] = max(set(vote[i]), key=vote[i].count)

elif class_type == 'ovr':
    for i in range(len(X_test)):  # number of test data
        if classes != 1:    # classes has been updated to -1 earlier (determines the # of classifiers)
            y_manual[i] = decision2[i].argmax(axis=0)   # check actual values since there might be a tie
        else:
            y_manual[i] = decision2[i] > 0  # special case for 2 classes
    
elif class_type == 'ecoc':
    # create a temp array (not required for chisel since we detect 1 sample), that will contain per class votes
    tempvote = np.zeros((len(X_test),classes))
    
    # use the code book to lay out the array of votes
    for i in range(len(X_test)): # number of test data
        for j in range(classes):
            tempvote[i][j] = sum(vote[i] == codes[j]) # hamming distance of every data to the code book 
            
        y_manual[i] = tempvote[i].argmax(axis=0) # pick the class with the largest hamming distance, will there be a tie?

    # OK, apparently we shouldn't clip the value before getting the distance
    # the distance is apparently defined as the euclidean distance to [-1,1], using the raw decision function value
    # this is a little problematic since that is computationally expensive
    
    # let's try creating a pseudo euclidean distance metric
    for i in range(len(X_test)): # number of test data
        for j in range(classes):
            tempvote[i][j] = -1*sum(np.power(decision2[i] - clf.code_book_[j],2)) # sum of squares, instead of euclidean
            
        y_manual[i] = tempvote[i].argmax(axis=0) # pick the minimum distance, using this distance metric
    
    # here's the actual operation required:
    #y_manual = euclidean_distances(decision2,codes).argmin(axis=1) # override if ever
    
    # we'll cheat a bit lol, this gets the distance between the clamped values already
    #y_pred = euclidean_distances(vote,codes).argmin(axis=1)
    
#########################################
# Model Accuracy: how often is the classifier correct?
#########################################
    
# Using the sklearn library, we get obtain the actual prediction
y_pred = clf.predict(X_test)

print("Accuracy fun:",accuracy_score(y_test, y_pred))
print("Accuracy man:",accuracy_score(y_test, y_manual))

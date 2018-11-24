import numpy as np
import itertools as it

def config_matrix(clf,class_type,classes):
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
        #decision1 = clf.decision_function(X_test)
    
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
        #decision1 = clf.decision_function(X_test)
    
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
            
    return alpha_vector, supports, intercept, num_classifiers

def get_decision(X_test, kernel, coef, degree, alpha_vector, supports, intercept, num_classifiers):
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
    decision = np.matmul(alpha_vector,kernel_dotproduct)
    # add the intercept after doing the dot product with the alphas
    decision = decision + np.matmul(intercept.reshape((num_classifiers,1)),np.ones((1,len(X_test.T[0]))))
    decision = decision.T
    
    # set votes to 0 or 1
    vote = decision > 0
    # change boolean to int, then convert as list
    vote = np.ndarray.tolist(vote.astype(int))
    
    return decision, vote

def predict (X_test, clf, class_type, classes, num_classifiers, decision, vote):
    # initialize container of final predicted classes using manual calculation
    y_manual = np.zeros((len(vote),1))
    
    if class_type == 'ovo':
        class_pairs = np.array(list(it.combinations(list(range(classes)),2)))
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
            if classes != 2:    # classes has been updated to -1 earlier (determines the # of classifiers)
                y_manual[i] = decision[i].argmax(axis=0)   # check actual values since there might be a tie
            else:
                y_manual[i] = decision[i] > 0  # special case for 2 classes
        
    elif class_type == 'ecoc':
        # create a temp array (not required for chisel since we detect 1 sample), that will contain per class votes
        tempvote = np.zeros((len(X_test),classes))
        
        # use the code book to lay out the array of votes
        for i in range(len(X_test)): # number of test data
            for j in range(classes):
                tempvote[i][j] = sum(vote[i] == clf.code_book_[j]) # hamming distance of every data to the code book 
                
            y_manual[i] = tempvote[i].argmax(axis=0) # pick the class with the largest hamming distance, will there be a tie?
    
        # OK, apparently we shouldn't clip the value before getting the distance
        # the distance is apparently defined as the euclidean distance to [-1,1], using the raw decision function value
        # this is a little problematic since that is computationally expensive
        
        # let's try creating a pseudo euclidean distance metric
        for i in range(len(X_test)): # number of test data
            for j in range(classes):
                tempvote[i][j] = -1*sum(np.power(decision[i] - clf.code_book_[j],2)) # sum of squares, instead of euclidean
                
            y_manual[i] = tempvote[i].argmax(axis=0) # pick the minimum distance, using this distance metric
        
        # here's the actual operation required:
        #y_manual = euclidean_distances(decision2,codes).argmin(axis=1) # override if ever
        
        # we'll cheat a bit lol, this gets the distance between the clamped values already
        #y_pred = euclidean_distances(vote,codes).argmin(axis=1)
        
    return y_manual
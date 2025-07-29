import numpy as np
import tensorflow as tf

# Note if you don't want to change the original labels, you can apply a modification to y_true inside the function
# For example, if you want ages with decimal points (e.g. 10.5), you can multiply by 10 and cast to int and use 990*2 neurons for you network

def calculate_lambda(y_true, min_classifier, max_classifier):
    """ 
    This function calculates the weight of each possible value in th dataset. It implements
    the lambda as described in the paper.
    
    Parameters:
        y_true: GT labels in the dataset
        min_classifier: value of the minimum classifer of the network usually set to 1
        max_classifier: value of the max classifier of the network
    Returns:
        lambda: np.array with the lambda values
    """
        
    y_true_adapted = (y_true).astype(int)
    min_rank = int(min(y_true))
    max_rank = int(max(y_true))
    counts = np.bincount(y_true_adapted)
    
    zeros_before = min_rank - min_classifier
    zeros_after = max_classifier - max_rank    
    
    #print(max_rank)
    #print(counts[min_rank:max_rank])
    #print(counts[max_rank])
    #print(counts)
    
    frequency = np.sqrt(counts[min_rank:max_rank+1])
    total = np.sum(counts[min_rank:max_rank+1])
    lambda_t = frequency / total
    #print(lambda_t)
    return(np.concatenate([np.zeros(zeros_before, dtype=np.float32),lambda_t, np.zeros(zeros_after, dtype=np.float32)]))

def importance_cross_entropy(y_true, y_pred, offset=0, max_classifier=99):
    """
    This function implements the importance cross entropy loss function for tensorflow.
    The loss function can be called as any other tensorflow loss function.

    Parameters:
        y_true: tf tensor with the ground truth values in each batch 
        y_pred: tf tensor with the predicted values in each batch 
        offset: If you wish to not start at 1 the first pair of neurons, you can set the offset to the desired value.
        max_classifier: Integer corresponding to the maximum value output
    Returns:
        loss: tf tensor with the loss value
    """
    #importance is constant

    n_neurons = (tf.shape(y_pred)[1])
    batch_size = int(tf.shape(y_pred)[0])
    y_pred_clip = tf.maximum(y_pred, 1e-7)
    masking_index = ((y_true - offset) * 2) -1
    
    mask = tf.cast(tf.less(tf.cast(tf.expand_dims(masking_index, axis=1), dtype=tf.int32), tf.range(n_neurons)), dtype=tf.float32)
    mask = tf.squeeze(mask, axis=1)

    even_mask = tf.tile(tf.expand_dims([1.0, 0.0], axis=0), [batch_size, int(max_classifier)-1-offset])

    xor_result = tf.cast(tf.math.not_equal(mask, even_mask), dtype=tf.float32)

    # cross_entropy = tf.reduce_sum((tf.cast(lambda_t_batch,dtype=tf.float32))*-1*xor_result*tf.math.log(y_pred_clip),axis=1)
    cross_entropy = tf.reduce_sum(-1*xor_result*tf.math.log(y_pred_clip),axis=1)

    loss = tf.reduce_sum(cross_entropy)/(tf.cast(batch_size, dtype=tf.float32))
    
    # tf.print("\nn_neurons is:", (n_neurons), summarize=-1)
    # tf.print("\nbatch_size is:", (batch_size), summarize=-1)
    # tf.print("\ny_true is:", (y_true), summarize=-1)
    # tf.print("\noffset is:", (offset), summarize=-1)
    # tf.print("\nmasking_index is:", (masking_index), summarize=-1)  
    # tf.print("\nmask is:", (mask), summarize=-1)
    # tf.print("\neven_mask is:", (even_mask), summarize=-1)
    # tf.print("\nxor_result is:", (xor_result), summarize=-1)
    # tf.print("\nlambda_t is:", (lambda_t), summarize=-1)
    # tf.print("\nlambda_t batch is:", (lambda_t_batch), summarize=-1)
    # tf.print("\ncross_entropy is:", (cross_entropy), summarize=-1)
    # tf.print("\nloss is:", (loss), summarize=-1)

    return loss

def importance_cross_entropy_lambda(y_true, y_pred, lambda_t, offset=0, max_classifier=99):
    """
    This function implements the importance cross entropy loss function for tensorflow.
    The loss function can be called as any other tensorflow loss function.

    Parameters:
        y_true: tf tensor with the ground truth values in each batch 
        y_pred: tf tensor with the predicted values in each batch
        lambda_t: tf tensor with the lambda values
        offset: If you wish to not start at 1 the first pair of neurons, you can set the offset to the desired value.
        max_classifier: Integer corresponding to the maximum value output
    Returns:
        loss: tf tensor with the loss value
    """
    #importance is constant

    n_neurons = (tf.shape(y_pred)[1])
    batch_size = int(tf.shape(y_pred)[0])
    y_pred_clip = tf.maximum(y_pred, 1e-7)
    masking_index = ((y_true - offset) * 2) -1
    
    mask = tf.cast(tf.less(tf.cast(tf.expand_dims(masking_index, axis=1), dtype=tf.int32), tf.range(n_neurons)), dtype=tf.float32)
    mask = tf.squeeze(mask, axis=1)

    even_mask = tf.tile(tf.expand_dims([1.0, 0.0], axis=0), [batch_size, int(max_classifier)-1-offset])

    xor_result = tf.cast(tf.math.not_equal(mask, even_mask), dtype=tf.float32)

    
    lambda_t_batch = tf.gather(lambda_t, tf.cast(y_true-1, dtype=tf.int32))
    cross_entropy = tf.reduce_sum((tf.cast(lambda_t_batch,dtype=tf.float32))*-1*xor_result*tf.math.log(y_pred_clip),axis=1)
    # cross_entropy = tf.reduce_sum(-1*xor_result*tf.math.log(y_pred_clip),axis=1)

    loss = tf.reduce_sum(cross_entropy)/(tf.cast(batch_size, dtype=tf.float32))
    
    # tf.print("\nn_neurons is:", (n_neurons), summarize=-1)
    # tf.print("\nbatch_size is:", (batch_size), summarize=-1)
    # tf.print("\ny_true is:", (y_true), summarize=-1)
    # tf.print("\noffset is:", (offset), summarize=-1)
    # tf.print("\nmasking_index is:", (masking_index), summarize=-1)  
    # tf.print("\nmask is:", (mask), summarize=-1)
    # tf.print("\neven_mask is:", (even_mask), summarize=-1)
    # tf.print("\nxor_result is:", (xor_result), summarize=-1)
    # tf.print("\nlambda_t is:", (lambda_t), summarize=-1)
    # tf.print("\nlambda_t batch is:", (lambda_t_batch), summarize=-1)
    # tf.print("\ncross_entropy is:", (cross_entropy), summarize=-1)
    # tf.print("\nloss is:", (loss), summarize=-1)
    
    return loss
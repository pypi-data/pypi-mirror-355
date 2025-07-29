import tensorflow as tf

#Note: You can change the thresold inside the tf.cast function.

def custom_mape50(y_true, y_pred):
    """
    This function implements the mean absolute percentage error. It uses the threshold of 0.5
    to consider a positive prediction.
    Parameters:
        y_true: tf tensor with the ground truth values in each batch 
        y_pred: tf tensor with the predicted values in each batch 
    Returns:
        mape: tf tensor with the value of the mape in each batch
    """
    offset = 0
        
    y_true_modified = tf.squeeze(y_true)
    
    y_pred_thresh = tf.cast(y_pred >= 0.5, dtype=tf.int32)
    
    y_pred_positives = y_pred_thresh[:, ::2]

    # Sum along the second axis (axis=1), i.e., sum along the columns
    y_pred_sum = tf.reduce_sum(y_pred_positives, axis=1)
    y_pred_sum = tf.cast(y_pred_sum + offset, dtype=tf.float32)
    abs_error = tf.abs(y_pred_sum-y_true_modified*1.0)
    abs_error_percentage = (abs_error/(y_true_modified*1.0))*100
    mape = tf.reduce_mean(abs_error_percentage)
    
    # tf.print("\ny_pred is:", (y_pred), summarize=-1)
    # tf.print("\ny_pred_thresh is:", (y_pred_thresh), summarize=-1)
    # tf.print("\ny_pred_positives is  is:", (y_pred_positives), summarize=-1)
    # tf.print("\ny_pred_sum + offset is:", (y_pred_sum), summarize=-1)
    # tf.print("\ny_true is:", (y_true_modified), summarize=-1)
    # tf.print("\nabs_error is:", (abs_error), summarize=-1)
    # tf.print("\nabs_error_percentage is:", (abs_error_percentage), summarize=-1)
    # tf.print("\nmape is:", (mape), summarize=-1)
    
    return mape

def custom_mae50(y_true, y_pred):
    """
    This function implements the mean absolute error. It uses the threshold of 0.5
    to consider a positive prediction.
    Parameters:
        y_true: tf tensor with the ground truth values in each batch 
        y_pred: tf tensor with the predicted values in each batch 
    Returns:
        mae: tf tensor with the value of the mae in each batch
    """
    offset = 0

    y_true_modified = tf.squeeze(y_true)

    y_pred_thresh = tf.cast(y_pred >= 0.5, dtype=tf.int32)
    
    y_pred_positives = y_pred_thresh[:, ::2]

    # Sum along the second axis (axis=1), i.e., sum along the columns
    y_pred_sum = tf.reduce_sum(y_pred_positives, axis=1)
    y_pred_sum = tf.cast(y_pred_sum + offset, dtype=tf.float32)
    abs_error = tf.abs(y_pred_sum-y_true_modified*1.0)
    mae = tf.reduce_mean(abs_error)
    #tf.print("\nmasking index is:", (masking_index), summarize=-1)
    #tf.print("\nxor_result is  is:", (xor_result), summarize=-1)
    #tf.print("\ny_true is:", (y_true), summarize=-1)
    #tf.print("\offset is:", (y_true - offset/1000), summarize=-1)
    
    return mae

def custom_accuracy5_50(y_true, y_pred):
    """
    This function implements the accuracy calculation. It uses the threshold of 0.5
    to consider a positive prediction and a 5% error tolerance to consider it in 
    between range.
    Parameters:
        y_true: tf tensor with the ground truth values in each batch 
        y_pred: tf tensor with the predicted values in each batch 
    Returns:
        mape: tf tensor with the value of the mape in each batch
    """
    offset = 0

    y_true_modified = tf.squeeze(y_true)
    
    y_pred_thresh = tf.cast(y_pred >= 0.5, dtype=tf.int32)
    
    y_pred_positives = y_pred_thresh[:, ::2]

    # Sum along the second axis (axis=1), i.e., sum along the columns
    y_pred_sum = tf.reduce_sum(y_pred_positives, axis=1)
    y_pred_sum = tf.cast(y_pred_sum + offset, dtype=tf.float32)
    abs_error = tf.abs(y_pred_sum-y_true_modified*1.0)
    abs_error_percentage = (abs_error/(y_true_modified*1.0))*100
    threshold_errors = tf.cast(abs_error_percentage <= 5.0, dtype=tf.float32)
    precentage_threshold_errors = tf.reduce_mean(threshold_errors)
    
    # tf.print("\ny_pred is:", (y_pred), summarize=-1)
    # tf.print("\ny_pred_thresh is:", (y_pred_thresh), summarize=-1)
    # tf.print("\ny_pred_positives is  is:", (y_pred_positives), summarize=-1)
    # tf.print("\ny_pred_sum + offset is:", (y_pred_sum), summarize=-1)
    # tf.print("\ny_true is:", (y_true_modified), summarize=-1)
    # tf.print("\nabs_error is:", (abs_error), summarize=-1)
    # tf.print("\nabs_error_percentage is:", (abs_error_percentage), summarize=-1)
    # tf.print("\nmape is:", (mape), summarize=-1)
    #tf.print("\nabs_error_percentage: ",abs_error_percentage, summarize=-1)
    #tf.print("\nNumber of thresholded_errors: ",threshold_errors, summarize=-1)
    #tf.print("\nprecentage_threshold_errors: ",precentage_threshold_errors, summarize=-1)
    
    return precentage_threshold_errors

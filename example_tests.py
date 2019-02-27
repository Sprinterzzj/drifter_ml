import joblib
import json
from sklearn import metrics
import numpy as np
import time
from sklearn import neighbors
from scipy import stats

# classification tests
def precision_lower_boundary_per_class(clf, test_data, target_name, column_names, lower_boundary):
    y = test_data[target_name]
    y_pred = clf.predict(test_data[column_names])
    
    for class_info in lower_boundary["per_class"]:
        klass = class_info["class"]
        y_pred_class = np.take(y_pred, y[y == klass].index, axis=0)
        y_class = y[y == klass]
        if metrics.precision_score(y_class, y_pred_class) < class_info["precision_score"]:
            return False
    return True

def recall_lower_boundary_per_class(clf, test_data, target_name, column_names, lower_boundary):
    y = test_data[target_name]
    y_pred = clf.predict(test_data[column_names])
    
    for class_info in lower_boundary["per_class"]:
        klass = class_info["class"]
        y_pred_class = np.take(y_pred, y[y == klass].index, axis=0)
        y_class = y[y == klass]
        if metrics.recall_score(y_class, y_pred_class) < class_info["recall_score"]:
            return False
    return True

def f1_lower_boundary_per_class(clf, test_data, target_name, column_names, lower_boundary):
    y = test_data[target_name]
    y_pred = clf.predict(test_data[column_names])
    
    for class_info in lower_boundary["per_class"]:
        klass = class_info["class"]
        y_pred_class = np.take(y_pred, y[y == klass].index, axis=0)
        y_class = y[y == klass]
        if metrics.f1_score(y_class, y_pred_class) < class_info["f1_score"]:
            return False
    return True

def get_parameters(clf_name, clf_metadata, data_name):
    clf = joblib.load(clf_name)
    metadata = json.load(open(clf_metadata, "r"))
    column_names = metadata["column_names"]
    target_name = metadata["target_name"]
    test_data = pd.read_csv(data_name)
    return clf, metadata, colum_names, target_name, test_data

def classifier_testing(clf_name, clf_metadata, data_name, precision_lower_boundary, recall_lower_boundary, f1_lower_boundary):
    clf, metadata, colum_names, target_name, test_data = get_parameters(clf_name, clf_metadata, data_name)
    precision_test = precision_lower_boundary_per_class(clf, test_data, target_name, column_names, precision_lower_boundary)
    recall_test = recall_lower_boundary_per_class(clf, test_data, target_name, column_names, recall_lower_boundary)
    f1_test = f1_lower_boundary_per_class(clf, test_data, target_name, column_names, f1_lower_boundary)
    if precision_test and recall_test and f1_test:
        return True
    else:
        return False
    
# regression tests
def mse_upper_boundary(reg, test_data, target_name, column_names, upper_boundary):
    y = test_data[target_name]
    y_pred = reg.predict(test_data[column_names])
    if metrics.mean_squared_error(y, y_pred) > upper_boundary:
        return False
    return True

def mae_upper_boundary(reg, test_data, target_name, column_names, upper_boundary):
    y = test_data[target_name]
    y_pred = reg.predict(test_data[column_names])
    if metrics.median_absolute_error(y, y_pred) > upper_boundary:
        return False
    return True

def regression_testing(reg_name, reg_metadata, data_name, mse_upper_boundary, mae_upper_boundary):
    reg, metadata, colum_names, target_name, test_data = get_parameters(reg_name, reg_metadata, data_name)
    mse_test = mse_upper_boundary(reg, test_data, target_name, column_names, mse_upper_boundary)
    mae_test = mae_upper_boundary(reg, test_data, target_name, column_names, mae_upper_boundary)
    if mse_test and mae_test:
        return True
    else:
        return False

def prediction_run_time_stress_test(model, test_data, column_names, performance_boundary):
    X = test_data[column_names]
    for performance_info in performance_boundary:
        n = int(performance_info["sample_size"])
        max_run_time = float(performance_info["max_run_time"])
        data = X.sample(n, replace=True)
        start_time = time.time()
        model.predict(data)
        model_run_time = time.time() - start_time
        if model_run_time > run_time:
            return False
    return True

# data tests
def is_complete(data, column):
    return data[column].isnull().sum() == 0

def has_completeness(data, column, threshold):
    return data[column].isnull().sum()/len(data) > threshold

def is_unique(data, column):
    return len(data[column].unique())/len(df) == 1

def has_uniqueness(data, column, threshold):
    return len(data[column].unique())/len(df) > threshold

def is_in_range(data, column, lower_bound, upper_bound, threshold):
    return data[(data[column] <= upper_bound) & (data[column] >= lower_bound)]/len(data) > threshold

def is_non_negative(data, column):
    return data[data[column] > 0]

def is_less_than(data, column_one, column_two):
    return data[data[column_one] < data[column_two]].all()

def clustering(data, columns, target):
    X = data[columns]
    y = data[target]
    k_measures = []
    for k in range(2, 12):
        knn = neighbors.KNeighborsRegressor(n_neighbors=k)
        knn.fit(X, y)
        y_pred = knn.predict(X)
        k_measures.append((k, metrics.mean_squared_error(y, y_pred)))
    sorted_k_measures = sorted(k_measures, key=lambda t:t[1])
    lowest_mse = sorted_k_measures[0]
    best_k = lowest_mse[0]
    return best_k
        
# memoryful tests
def similar_clustering(absolute_distance, new_data, historical_data, column_names, target_name):
    historical_k = clustering(historical_data, column_names, target_name)
    new_k = clustering(new_data, column_names, target_name)
    if abs(historical_k - new_k) > absolute_distance:
        return False
    else:
        return True

def similar_correlation(correlation_lower_bound, new_data, historical_data, column_names, pvalue_threshold=0.05):
    for column_name in column_names:
        correlation_info = stats.spearmanr(new_data[column_name], historical_data[column_name])
        if correlation_info.pvalue > pvalue_threshold:
            return False
        if correlation_info.correlation < correlation_lower_bound:
            return False
    return True

def similar_distribution(new_data, historical_data, column_names, pvalue_threshold=0.05):
    for column_name in column_names:
        distribution_info = stats.ks_2samp(new_data[column_name], historical_data[column_name])
        if correlation_info.pvalue < pvalue_threshold:
            return False
    return True

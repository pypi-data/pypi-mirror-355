"""
From: https://github.com/mlrequest/sklearn-json
"""
import numpy as np
import scipy as sp
from sklearn import svm, discriminant_analysis, dummy
from sklearn.linear_model import LogisticRegression, Perceptron
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.tree._tree import Tree
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, RandomForestRegressor, GradientBoostingRegressor, _gb_losses
from sklearn.naive_bayes import BernoulliNB, GaussianNB, MultinomialNB, ComplementNB
from sklearn.linear_model import LinearRegression, Lasso, Ridge
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.svm import SVR
from sklearn.preprocessing import LabelBinarizer
import json


########################################################################################
#
#                                   csr.py
#
########################################################################################

def serialize_csr_matrix(csr_matrix):
    serialized_csr_matrix = {
        'meta': 'csr',
        'data': csr_matrix.data.tolist(),
        'indices': csr_matrix.indices.tolist(),
        'indptr': csr_matrix.indptr.tolist(),
        '_shape': csr_matrix._shape,
    }
    return serialized_csr_matrix


def deserialize_csr_matrix(csr_dict, data_type=np.float64, indices_type=np.int32, indptr_type=np.int32):
    csr_matrix = sp.sparse.csr_matrix(tuple(csr_dict['_shape']))
    csr_matrix.data = np.array(csr_dict['data']).astype(data_type)
    csr_matrix.indices = np.array(csr_dict['indices']).astype(indices_type)
    csr_matrix.indptr = np.array(csr_dict['indptr']).astype(indptr_type)

    return csr_matrix


########################################################################################
#
#                                regression.py
#
########################################################################################

def serialize_linear_regressor(model):
    serialized_model = {
        'meta': 'linear-regression',
        'coef_': model.coef_.tolist(),
        'intercept_': model.intercept_.tolist(),
        'params': model.get_params()
    }

    return serialized_model


def deserialize_linear_regressor(model_dict):
    model = LinearRegression(**model_dict['params'])

    model.coef_ = np.array(model_dict['coef_'])
    model.intercept_ = np.array(model_dict['intercept_'])

    return model


def serialize_lasso_regressor(model):
    serialized_model = {
        'meta': 'lasso-regression',
        'coef_': model.coef_.tolist(),
        'params': model.get_params()
    }

    if isinstance(model.n_iter_, int):
        serialized_model['n_iter_'] = model.n_iter_
    else:
        serialized_model['n_iter_'] = model.n_iter_.tolist()

    if isinstance(model.n_iter_, float):
        serialized_model['intercept_'] = model.intercept_
    else:
        serialized_model['intercept_'] = model.intercept_.tolist()

    return serialized_model


def deserialize_lasso_regressor(model_dict):
    model = Lasso(**model_dict['params'])

    model.coef_ = np.array(model_dict['coef_'])

    if isinstance(model_dict['n_iter_'], list):
        model.n_iter_ = np.array(model_dict['n_iter_'])
    else:
        model.n_iter_ = int(model_dict['n_iter_'])

    if isinstance(model_dict['intercept_'], list):
        model.intercept_ = np.array(model_dict['intercept_'])
    else:
        model.intercept_ = float(model_dict['intercept_'])

    return model


def serialize_ridge_regressor(model):
    serialized_model = {
        'meta': 'ridge-regression',
        'coef_': model.coef_.tolist(),
        'params': model.get_params()
    }

    if model.n_iter_:
        serialized_model['n_iter_'] = model.n_iter_.tolist()

    if isinstance(model.n_iter_, float):
        serialized_model['intercept_'] = model.intercept_
    else:
        serialized_model['intercept_'] = model.intercept_.tolist()

    return serialized_model


def deserialize_ridge_regressor(model_dict):
    model = Ridge(model_dict['params'])

    model.coef_ = np.array(model_dict['coef_'])

    if 'n_iter_' in model_dict:
        model.n_iter_ = np.array(model_dict['n_iter_'])

    if isinstance(model_dict['intercept_'], list):
        model.intercept_ = np.array(model_dict['intercept_'])
    else:
        model.intercept_ = float(model_dict['intercept_'])

    return model


def serialize_svr(model):
    serialized_model = {
        'meta': 'svr',
        'class_weight_': model.class_weight_.tolist(),
        'support_': model.support_.tolist(),
        'n_support_': model.n_support_.tolist(),
        'intercept_': model.intercept_.tolist(),
        'probA_': model.probA_.tolist(),
        'probB_': model.probB_.tolist(),
        '_intercept_': model._intercept_.tolist(),
        'shape_fit_': model.shape_fit_,
        '_gamma': model._gamma,
        'params': model.get_params()
    }

    if isinstance(model.support_vectors_, sp.sparse.csr_matrix):
        serialized_model['support_vectors_'] = serialize_csr_matrix(model.support_vectors_)
    elif isinstance(model.support_vectors_, np.ndarray):
        serialized_model['support_vectors_'] = model.support_vectors_.tolist()

    if isinstance(model.dual_coef_, sp.sparse.csr_matrix):
        serialized_model['dual_coef_'] = serialize_csr_matrix(model.dual_coef_)
    elif isinstance(model.dual_coef_, np.ndarray):
        serialized_model['dual_coef_'] = model.dual_coef_.tolist()

    if isinstance(model._dual_coef_, sp.sparse.csr_matrix):
        serialized_model['_dual_coef_'] = serialize_csr_matrix(model._dual_coef_)
    elif isinstance(model._dual_coef_, np.ndarray):
        serialized_model['_dual_coef_'] = model._dual_coef_.tolist()

    return serialized_model


def deserialize_svr(model_dict):
    model = SVR(**model_dict['params'])
    model.shape_fit_ = model_dict['shape_fit_']
    model._gamma = model_dict['_gamma']

    model.class_weight_ = np.array(model_dict['class_weight_']).astype(np.float64)
    model.support_ = np.array(model_dict['support_']).astype(np.int32)
    model.n_support_ = np.array(model_dict['n_support_']).astype(np.int32)
    model.intercept_ = np.array(model_dict['intercept_']).astype(np.float64)
    model.probA_ = np.array(model_dict['probA_']).astype(np.float64)
    model.probB_ = np.array(model_dict['probB_']).astype(np.float64)
    model._intercept_ = np.array(model_dict['_intercept_']).astype(np.float64)

    if 'meta' in model_dict['support_vectors_'] and model_dict['support_vectors_']['meta'] == 'csr':
        model.support_vectors_ = deserialize_csr_matrix(model_dict['support_vectors_'])
        model._sparse = True
    else:
        model.support_vectors_ = np.array(model_dict['support_vectors_']).astype(np.float64)
        model._sparse = False

    if 'meta' in model_dict['dual_coef_'] and model_dict['dual_coef_']['meta'] == 'csr':
        model.dual_coef_ = deserialize_csr_matrix(model_dict['dual_coef_'])
    else:
        model.dual_coef_ = np.array(model_dict['dual_coef_']).astype(np.float64)

    if 'meta' in model_dict['_dual_coef_'] and model_dict['_dual_coef_']['meta'] == 'csr':
        model._dual_coef_ = deserialize_csr_matrix(model_dict['_dual_coef_'])
    else:
        model._dual_coef_ = np.array(model_dict['_dual_coef_']).astype(np.float64)

    return model


def serialize_tree(tree):
    serialized_tree = tree.__getstate__()
    # serialized_tree['nodes_dtype'] = serialized_tree['nodes'].dtype
    dtypes = serialized_tree['nodes'].dtype
    serialized_tree['nodes'] = serialized_tree['nodes'].tolist()
    serialized_tree['values'] = serialized_tree['values'].tolist()

    return serialized_tree, dtypes


def deserialize_tree(tree_dict, n_features, n_classes, n_outputs):
    tree_dict['nodes'] = [tuple(lst) for lst in tree_dict['nodes']]

    names = ['left_child', 'right_child', 'feature', 'threshold', 'impurity', 'n_node_samples', 'weighted_n_node_samples']
    tree_dict['nodes'] = np.array(tree_dict['nodes'], dtype=np.dtype({'names': names, 'formats': tree_dict['nodes_dtype']}))
    tree_dict['values'] = np.array(tree_dict['values'])

    tree = Tree(n_features, np.array([n_classes], dtype=np.intp), n_outputs)
    tree.__setstate__(tree_dict)

    return tree


def serialize_decision_tree_regressor(model):
    tree, dtypes = serialize_tree(model.tree_)
    serialized_model = {
        'meta': 'decision-tree-regression',
        'feature_importances_': model.feature_importances_.tolist(),
        'max_features_': model.max_features_,
        'n_features_': model.n_features_,
        'n_outputs_': model.n_outputs_,
        'tree_': tree
    }

    # serialized_model.

    tree_dtypes = []
    for i in range(0, len(dtypes)):
        tree_dtypes.append(dtypes[i].str)

    serialized_model['tree_']['nodes_dtype'] = tree_dtypes

    return serialized_model


def deserialize_decision_tree_regressor(model_dict):
    deserialized_decision_tree = DecisionTreeRegressor()

    deserialized_decision_tree.max_features_ = model_dict['max_features_']
    deserialized_decision_tree.n_features_ = model_dict['n_features_']
    deserialized_decision_tree.n_outputs_ = model_dict['n_outputs_']

    tree = deserialize_tree(model_dict['tree_'], model_dict['n_features_'], 1, model_dict['n_outputs_'])
    deserialized_decision_tree.tree_ = tree

    return deserialized_decision_tree


def serialize_dummy_regressor(model):
    model.constant = model.constant_.tolist()
    return model.__dict__


def serialize_gradient_boosting_regressor(model):

    serialized_model = {
        'meta': 'gb-regression',
        'max_features_': model.max_features_,
        'n_features_': model.n_features_,
        'train_score_': model.train_score_.tolist(),
        'params': model.get_params(),
        'estimators_shape': list(model.estimators_.shape),
        'estimators_': []
    }

    if  isinstance(model.init_, dummy.DummyRegressor):
        serialized_model['init_'] = serialize_dummy_regressor(model.init_)
        serialized_model['init_']['meta'] = 'dummy'
    elif isinstance(model.init_, str):
        serialized_model['init_'] = model.init_

    if isinstance(model.loss_, _gb_losses.LeastSquaresError):
        serialized_model['loss_'] = 'ls'
    elif isinstance(model.loss_, _gb_losses.LeastAbsoluteError):
        serialized_model['loss_'] = 'lad'
    elif isinstance(model.loss_, _gb_losses.HuberLossFunction):
        serialized_model['loss_'] = 'huber'
    elif isinstance(model.loss_, _gb_losses.QuantileLossFunction):
        serialized_model['loss_'] = 'quantile'

    if 'priors' in model.init_.__dict__:
        serialized_model['priors'] = model.init_.priors.tolist()

    for tree in model.estimators_.reshape((-1,)):
        serialized_model['estimators_'].append(serialize_decision_tree_regressor(tree))
    return serialized_model


def deserialize_gradient_boosting_regressor(model_dict):
    model = GradientBoostingRegressor(**model_dict['params'])
    trees = [deserialize_decision_tree_regressor(tree) for tree in model_dict['estimators_']]
    model.estimators_ = np.array(trees).reshape(model_dict['estimators_shape'])
    if 'init_' in model_dict and model_dict['init_']['meta'] == 'dummy':
        model.init_ = dummy.DummyRegressor()
        model.init_.__dict__ = model_dict['init_']
        model.init_.__dict__.pop('meta')


    model.train_score_ = np.array(model_dict['train_score_'])
    model.max_features_ = model_dict['max_features_']
    model.n_features_ = model_dict['n_features_']
    if model_dict['loss_'] == 'ls':
        model.loss_ = _gb_losses.LeastSquaresError(1)
    elif model_dict['loss_'] == 'lad':
        model.loss_ = _gb_losses.LeastAbsoluteError(1)
    elif model_dict['loss_'] == 'huber':
        model.loss_ = _gb_losses.HuberLossFunction(1)
    elif model_dict['loss_'] == 'quantile':
        model.loss_ = _gb_losses.QuantileLossFunction(1)

    if 'priors' in model_dict:
        model.init_.priors = np.array(model_dict['priors'])
    return model


def serialize_random_forest_regressor(model):

    serialized_model = {
        'meta': 'rf-regression',
        'max_depth': model.max_depth,
        'min_samples_split': model.min_samples_split,
        'min_samples_leaf': model.min_samples_leaf,
        'min_weight_fraction_leaf': model.min_weight_fraction_leaf,
        'max_features': model.max_features,
        'max_leaf_nodes': model.max_leaf_nodes,
        'min_impurity_decrease': model.min_impurity_decrease,
        'min_impurity_split': model.min_impurity_split,
        'n_features_': model.n_features_,
        'n_outputs_': model.n_outputs_,
        'estimators_': [serialize_decision_tree_regressor(decision_tree) for decision_tree in model.estimators_],
        'params': model.get_params()
    }

    if 'oob_score_' in model.__dict__:
        serialized_model['oob_score_'] = model.oob_score_
    if 'oob_decision_function_' in model.__dict__:
        serialized_model['oob_prediction_'] = model.oob_prediction_.tolist()

    return serialized_model


def deserialize_random_forest_regressor(model_dict):
    model = RandomForestRegressor(**model_dict['params'])
    estimators = [deserialize_decision_tree_regressor(decision_tree) for decision_tree in model_dict['estimators_']]
    model.estimators_ = np.array(estimators)

    model.n_features_ = model_dict['n_features_']
    model.n_outputs_ = model_dict['n_outputs_']
    model.max_depth = model_dict['max_depth']
    model.min_samples_split = model_dict['min_samples_split']
    model.min_samples_leaf = model_dict['min_samples_leaf']
    model.min_weight_fraction_leaf = model_dict['min_weight_fraction_leaf']
    model.max_features = model_dict['max_features']
    model.max_leaf_nodes = model_dict['max_leaf_nodes']
    model.min_impurity_decrease = model_dict['min_impurity_decrease']
    model.min_impurity_split = model_dict['min_impurity_split']

    if 'oob_score_' in model_dict:
        model.oob_score_ = model_dict['oob_score_']
    if 'oob_prediction_' in model_dict:
        model.oob_prediction_ =np.array(model_dict['oob_prediction_'])

    return model


def serialize_mlp_regressor(model):
    serialized_model = {
        'meta': 'mlp-regression',
        'coefs_': model.coefs_,
        'loss_': model.loss_,
        'intercepts_': model.intercepts_,
        'n_iter_': model.n_iter_,
        'n_layers_': model.n_layers_,
        'n_outputs_': model.n_outputs_,
        'out_activation_': model.out_activation_,
        'params': model.get_params()
    }

    return serialized_model


def deserialize_mlp_regressor(model_dict):
    model = MLPRegressor(**model_dict['params'])

    model.coefs_ = model_dict['coefs_']
    model.loss_ = model_dict['loss_']
    model.intercepts_ = model_dict['intercepts_']
    model.n_iter_ = model_dict['n_iter_']
    model.n_layers_ = model_dict['n_layers_']
    model.n_outputs_ = model_dict['n_outputs_']
    model.out_activation_ = model_dict['out_activation_']

    return model


########################################################################################
#
#                                classification.py
#
########################################################################################

def serialize_logistic_regression(model):
    serialized_model = {
        'meta': 'lr',
        'classes_': model.classes_.tolist(),
        'coef_': model.coef_.tolist(),
        'intercept_': model.intercept_.tolist(),
        'n_iter_': model.n_iter_.tolist(),
        'params': model.get_params()
    }

    return serialized_model


def deserialize_logistic_regression(model_dict):
    model = LogisticRegression(**model_dict['params'])

    model.classes_ = np.array(model_dict['classes_'])
    model.coef_ = np.array(model_dict['coef_'])
    model.intercept_ = np.array(model_dict['intercept_'])
    model.n_iter_ = np.array(model_dict['intercept_'])

    return model


def serialize_bernoulli_nb(model):
    serialized_model = {
        'meta': 'bernoulli-nb',
        'classes_': model.classes_.tolist(),
        'class_count_': model.class_count_.tolist(),
        'class_log_prior_': model.class_log_prior_.tolist(),
        'feature_count_': model.feature_count_.tolist(),
        'feature_log_prob_': model.feature_log_prob_.tolist(),
        'params': model.get_params()
    }

    return serialized_model


def deserialize_bernoulli_nb(model_dict):
    model = BernoulliNB(**model_dict['params'])

    model.classes_ = np.array(model_dict['classes_'])
    model.class_count_ = np.array(model_dict['class_count_'])
    model.class_log_prior_ = np.array(model_dict['class_log_prior_'])
    model.feature_count_= np.array(model_dict['feature_count_'])
    model.feature_log_prob_ = np.array(model_dict['feature_log_prob_'])

    return model


def serialize_gaussian_nb(model):
    serialized_model = {
        'meta': 'gaussian-nb',
        'classes_': model.classes_.tolist(),
        'class_count_': model.class_count_.tolist(),
        'class_prior_': model.class_prior_.tolist(),
        'theta_': model.theta_.tolist(),
        'sigma_': model.sigma_.tolist(),
        'epsilon_': model.epsilon_,
        'params': model.get_params()
    }

    return serialized_model


def deserialize_gaussian_nb(model_dict):
    model = GaussianNB(**model_dict['params'])

    model.classes_ = np.array(model_dict['classes_'])
    model.class_count_ = np.array(model_dict['class_count_'])
    model.class_prior_ = np.array(model_dict['class_prior_'])
    model.theta_ = np.array(model_dict['theta_'])
    model.sigma_ = np.array(model_dict['sigma_'])
    model.epsilon_ = model_dict['epsilon_']

    return model


def serialize_multinomial_nb(model):
    serialized_model = {
        'meta': 'multinomial-nb',
        'classes_': model.classes_.tolist(),
        'class_count_': model.class_count_.tolist(),
        'class_log_prior_': model.class_log_prior_.tolist(),
        'feature_count_': model.feature_count_.tolist(),
        'feature_log_prob_': model.feature_log_prob_.tolist(),
        'params': model.get_params()
    }

    return serialized_model


def deserialize_multinomial_nb(model_dict):
    model = MultinomialNB(**model_dict['params'])

    model.classes_ = np.array(model_dict['classes_'])
    model.class_count_ = np.array(model_dict['class_count_'])
    model.class_log_prior_ = np.array(model_dict['class_log_prior_'])
    model.feature_count_= np.array(model_dict['feature_count_'])
    model.feature_log_prob_ = np.array(model_dict['feature_log_prob_'])

    return model


def serialize_complement_nb(model):
    serialized_model = {
        'meta': 'complement-nb',
        'classes_': model.classes_.tolist(),
        'class_count_': model.class_count_.tolist(),
        'class_log_prior_': model.class_log_prior_.tolist(),
        'feature_count_': model.feature_count_.tolist(),
        'feature_log_prob_': model.feature_log_prob_.tolist(),
        'feature_all_': model.feature_all_.tolist(),
        'params': model.get_params()
    }

    return serialized_model


def deserialize_complement_nb(model_dict):
    model = ComplementNB(**model_dict['params'])

    model.classes_ = np.array(model_dict['classes_'])
    model.class_count_ = np.array(model_dict['class_count_'])
    model.class_log_prior_ = np.array(model_dict['class_log_prior_'])
    model.feature_count_= np.array(model_dict['feature_count_'])
    model.feature_log_prob_ = np.array(model_dict['feature_log_prob_'])
    model.feature_all_ = np.array(model_dict['feature_all_'])

    return model


def serialize_lda(model):
    serialized_model = {
        'meta': 'lda',
        'coef_': model.coef_.tolist(),
        'intercept_': model.intercept_.tolist(),
        'explained_variance_ratio_': model.explained_variance_ratio_.tolist(),
        'means_': model.means_.tolist(),
        'priors_': model.priors_.tolist(),
        'scalings_': model.scalings_.tolist(),
        'xbar_': model.xbar_.tolist(),
        'classes_': model.classes_.tolist(),
        'params': model.get_params()
    }
    if 'covariance_' in model.__dict__:
        serialized_model['covariance_'] = model.covariance_.tolist()

    return serialized_model


def deserialize_lda(model_dict):
    model = discriminant_analysis.LinearDiscriminantAnalysis(**model_dict['params'])

    model.coef_ = np.array(model_dict['coef_']).astype(np.float64)
    model.intercept_ = np.array(model_dict['intercept_']).astype(np.float64)
    model.explained_variance_ratio_ = np.array(model_dict['explained_variance_ratio_']).astype(np.float64)
    model.means_ = np.array(model_dict['means_']).astype(np.float64)
    model.priors_ = np.array(model_dict['priors_']).astype(np.float64)
    model.scalings_ = np.array(model_dict['scalings_']).astype(np.float64)
    model.xbar_ = np.array(model_dict['xbar_']).astype(np.float64)
    model.classes_ = np.array(model_dict['classes_']).astype(np.int64)

    return model


def serialize_qda(model):
    serialized_model = {
        'meta': 'qda',
        'means_': model.means_.tolist(),
        'priors_': model.priors_.tolist(),
        'scalings_': [array.tolist() for array in model.scalings_],
        'rotations_': [array.tolist() for array in model.rotations_],
        'classes_': model.classes_.tolist(),
        'params': model.get_params()
    }
    if 'covariance_' in model.__dict__:
        serialized_model['covariance_'] = model.covariance_.tolist()

    return serialized_model


def deserialize_qda(model_dict):
    model = discriminant_analysis.QuadraticDiscriminantAnalysis(**model_dict['params'])

    model.means_ = np.array(model_dict['means_']).astype(np.float64)
    model.priors_ = np.array(model_dict['priors_']).astype(np.float64)
    model.scalings_ = np.array(model_dict['scalings_']).astype(np.float64)
    model.rotations_ = np.array(model_dict['rotations_']).astype(np.float64)
    model.classes_ = np.array(model_dict['classes_']).astype(np.int64)

    return model


def serialize_svm(model):
    serialized_model = {
        'meta': 'svm',
        'class_weight_': model.class_weight_.tolist(),
        'classes_': model.classes_.tolist(),
        'support_': model.support_.tolist(),
        'n_support_': model.n_support_.tolist(),
        'intercept_': model.intercept_.tolist(),
        'probA_': model.probA_.tolist(),
        'probB_': model.probB_.tolist(),
        '_intercept_': model._intercept_.tolist(),
        'shape_fit_': model.shape_fit_,
        '_gamma': model._gamma,
        'params': model.get_params()
    }

    if isinstance(model.support_vectors_, sp.sparse.csr_matrix):
        serialized_model['support_vectors_'] = csr.serialize_csr_matrix(model.support_vectors_)
    elif isinstance(model.support_vectors_, np.ndarray):
        serialized_model['support_vectors_'] = model.support_vectors_.tolist()

    if isinstance(model.dual_coef_, sp.sparse.csr_matrix):
        serialized_model['dual_coef_'] = csr.serialize_csr_matrix(model.dual_coef_)
    elif isinstance(model.dual_coef_, np.ndarray):
        serialized_model['dual_coef_'] = model.dual_coef_.tolist()

    if isinstance(model._dual_coef_, sp.sparse.csr_matrix):
        serialized_model['_dual_coef_'] = csr.serialize_csr_matrix(model._dual_coef_)
    elif isinstance(model._dual_coef_, np.ndarray):
        serialized_model['_dual_coef_'] = model._dual_coef_.tolist()

    return serialized_model


def deserialize_svm(model_dict):
    model = svm.SVC(**model_dict['params'])
    model.shape_fit_ = model_dict['shape_fit_']
    model._gamma = model_dict['_gamma']

    model.class_weight_ = np.array(model_dict['class_weight_']).astype(np.float64)
    model.classes_ = np.array(model_dict['classes_'])
    model.support_ = np.array(model_dict['support_']).astype(np.int32)
    model.n_support_ = np.array(model_dict['n_support_']).astype(np.int32)
    model.intercept_ = np.array(model_dict['intercept_']).astype(np.float64)
    model.probA_ = np.array(model_dict['probA_']).astype(np.float64)
    model.probB_ = np.array(model_dict['probB_']).astype(np.float64)
    model._intercept_ = np.array(model_dict['_intercept_']).astype(np.float64)

    if 'meta' in model_dict['support_vectors_'] and model_dict['support_vectors_']['meta'] == 'csr':
        model.support_vectors_ = csr.deserialize_csr_matrix(model_dict['support_vectors_'])
        model._sparse = True
    else:
        model.support_vectors_ = np.array(model_dict['support_vectors_']).astype(np.float64)
        model._sparse = False

    if 'meta' in model_dict['dual_coef_'] and model_dict['dual_coef_']['meta'] == 'csr':
        model.dual_coef_ = csr.deserialize_csr_matrix(model_dict['dual_coef_'])
    else:
        model.dual_coef_ = np.array(model_dict['dual_coef_']).astype(np.float64)

    if 'meta' in model_dict['_dual_coef_'] and model_dict['_dual_coef_']['meta'] == 'csr':
        model._dual_coef_ = csr.deserialize_csr_matrix(model_dict['_dual_coef_'])
    else:
        model._dual_coef_ = np.array(model_dict['_dual_coef_']).astype(np.float64)

    return model


def serialize_dummy_classifier(model):
    model.classes_ = model.classes_.tolist()
    model.class_prior_ = model.class_prior_.tolist()
    return model.__dict__


def serialize_tree(tree):
    serialized_tree = tree.__getstate__()

    dtypes = serialized_tree['nodes'].dtype
    serialized_tree['nodes'] = serialized_tree['nodes'].tolist()
    serialized_tree['values'] = serialized_tree['values'].tolist()

    return serialized_tree, dtypes


def deserialize_tree(tree_dict, n_features, n_classes, n_outputs):
    tree_dict['nodes'] = [tuple(lst) for lst in tree_dict['nodes']]

    names = ['left_child', 'right_child', 'feature', 'threshold', 'impurity', 'n_node_samples', 'weighted_n_node_samples']
    tree_dict['nodes'] = np.array(tree_dict['nodes'], dtype=np.dtype({'names': names, 'formats': tree_dict['nodes_dtype']}))
    tree_dict['values'] = np.array(tree_dict['values'])

    tree = Tree(n_features, np.array([n_classes], dtype=np.intp), n_outputs)
    tree.__setstate__(tree_dict)

    return tree


def serialize_decision_tree(model):
    tree, dtypes = serialize_tree(model.tree_)
    serialized_model = {
        'meta': 'decision-tree',
        'feature_importances_': model.feature_importances_.tolist(),
        'max_features_': model.max_features_,
        'n_classes_': int(model.n_classes_),
        'n_features_': model.n_features_,
        'n_outputs_': model.n_outputs_,
        'tree_': tree,
        'classes_': model.classes_.tolist(),
        'params': model.get_params()
    }


    tree_dtypes = []
    for i in range(0, len(dtypes)):
        tree_dtypes.append(dtypes[i].str)

    serialized_model['tree_']['nodes_dtype'] = tree_dtypes

    return serialized_model


def deserialize_decision_tree(model_dict):
    deserialized_model = DecisionTreeClassifier(**model_dict['params'])

    deserialized_model.classes_ = np.array(model_dict['classes_'])
    deserialized_model.max_features_ = model_dict['max_features_']
    deserialized_model.n_classes_ = model_dict['n_classes_']
    deserialized_model.n_features_ = model_dict['n_features_']
    deserialized_model.n_outputs_ = model_dict['n_outputs_']

    tree = deserialize_tree(model_dict['tree_'], model_dict['n_features_'], model_dict['n_classes_'], model_dict['n_outputs_'])
    deserialized_model.tree_ = tree

    return deserialized_model


def serialize_gradient_boosting(model):
    serialized_model = {
        'meta': 'gb',
        'classes_': model.classes_.tolist(),
        'max_features_': model.max_features_,
        'n_classes_': model.n_classes_,
        'n_features_': model.n_features_,
        'train_score_': model.train_score_.tolist(),
        'params': model.get_params(),
        'estimators_shape': list(model.estimators_.shape),
        'estimators_': []
    }

    if  isinstance(model.init_, dummy.DummyClassifier):
        serialized_model['init_'] = serialize_dummy_classifier(model.init_)
        serialized_model['init_']['meta'] = 'dummy'
    elif isinstance(model.init_, str):
        serialized_model['init_'] = model.init_

    if isinstance(model.loss_, _gb_losses.BinomialDeviance):
        serialized_model['loss_'] = 'deviance'
    elif isinstance(model.loss_, _gb_losses.ExponentialLoss):
        serialized_model['loss_'] = 'exponential'
    elif isinstance(model.loss_, _gb_losses.MultinomialDeviance):
        serialized_model['loss_'] = 'multinomial'

    if 'priors' in model.init_.__dict__:
        serialized_model['priors'] = model.init_.priors.tolist()

    serialized_model['estimators_'] = [regression.serialize_decision_tree_regressor(regression_tree) for regression_tree in model.estimators_.reshape(-1, )]

    return serialized_model


def deserialize_gradient_boosting(model_dict):
    model = GradientBoostingClassifier(**model_dict['params'])
    estimators = [regression.deserialize_decision_tree_regressor(tree) for tree in model_dict['estimators_']]
    model.estimators_ = np.array(estimators).reshape(model_dict['estimators_shape'])
    if 'init_' in model_dict and model_dict['init_']['meta'] == 'dummy':
        model.init_ = dummy.DummyClassifier()
        model.init_.__dict__ = model_dict['init_']
        model.init_.__dict__.pop('meta')

    model.classes_ = np.array(model_dict['classes_'])
    model.train_score_ = np.array(model_dict['train_score_'])
    model.max_features_ = model_dict['max_features_']
    model.n_classes_ = model_dict['n_classes_']
    model.n_features_ = model_dict['n_features_']
    if model_dict['loss_'] == 'deviance':
        model.loss_ = _gb_losses.BinomialDeviance(model.n_classes_)
    elif model_dict['loss_'] == 'exponential':
        model.loss_ = _gb_losses.ExponentialLoss(model.n_classes_)
    elif model_dict['loss_'] == 'multinomial':
        model.loss_ = _gb_losses.MultinomialDeviance(model.n_classes_)

    if 'priors' in model_dict:
        model.init_.priors = np.array(model_dict['priors'])
    return model


def serialize_random_forest(model):
    serialized_model = {
        'meta': 'rf',
        'max_depth': model.max_depth,
        'min_samples_split': model.min_samples_split,
        'min_samples_leaf': model.min_samples_leaf,
        'min_weight_fraction_leaf': model.min_weight_fraction_leaf,
        'max_features': model.max_features,
        'max_leaf_nodes': model.max_leaf_nodes,
        'min_impurity_decrease': model.min_impurity_decrease,
        'min_impurity_split': model.min_impurity_split,
        'n_features_': model.n_features_,
        'n_outputs_': model.n_outputs_,
        'classes_': model.classes_.tolist(),
        'estimators_': [serialize_decision_tree(decision_tree) for decision_tree in model.estimators_],
        'params': model.get_params()
    }

    if 'oob_score_' in model.__dict__:
        serialized_model['oob_score_'] = model.oob_score_
    if 'oob_decision_function_' in model.__dict__:
        serialized_model['oob_decision_function_'] = model.oob_decision_function_.tolist()

    if isinstance(model.n_classes_, int):
        serialized_model['n_classes_'] = model.n_classes_
    else:
        serialized_model['n_classes_'] = model.n_classes_.tolist()

    return serialized_model


def deserialize_random_forest(model_dict):
    model = RandomForestClassifier(**model_dict['params'])
    estimators = [deserialize_decision_tree(decision_tree) for decision_tree in model_dict['estimators_']]
    model.estimators_ = np.array(estimators)

    model.classes_ = np.array(model_dict['classes_'])
    model.n_features_ = model_dict['n_features_']
    model.n_outputs_ = model_dict['n_outputs_']
    model.max_depth = model_dict['max_depth']
    model.min_samples_split = model_dict['min_samples_split']
    model.min_samples_leaf = model_dict['min_samples_leaf']
    model.min_weight_fraction_leaf = model_dict['min_weight_fraction_leaf']
    model.max_features = model_dict['max_features']
    model.max_leaf_nodes = model_dict['max_leaf_nodes']
    model.min_impurity_decrease = model_dict['min_impurity_decrease']
    model.min_impurity_split = model_dict['min_impurity_split']

    if 'oob_score_' in model_dict:
        model.oob_score_ = model_dict['oob_score_']
    if 'oob_decision_function_' in model_dict:
        model.oob_decision_function_ = model_dict['oob_decision_function_']

    if isinstance(model_dict['n_classes_'], list):
        model.n_classes_ = np.array(model_dict['n_classes_'])
    else:
        model.n_classes_ = model_dict['n_classes_']

    return model


def serialize_perceptron(model):
    serialized_model = {
        'meta': 'perceptron',
        'coef_': model.coef_.tolist(),
        'intercept_': model.intercept_.tolist(),
        'n_iter_': model.n_iter_,
        'classes_': model.classes_.tolist(),
        'params': model.get_params()
    }
    if 'covariance_' in model.__dict__:
        serialized_model['covariance_'] = model.covariance_.tolist()

    return serialized_model


def deserialize_perceptron(model_dict):
    model = Perceptron(**model_dict['params'])

    model.coef_ = np.array(model_dict['coef_']).astype(np.float64)
    model.intercept_ = np.array(model_dict['intercept_']).astype(np.float64)
    model.n_iter_ = np.array(model_dict['n_iter_']).astype(np.float64)
    model.classes_ = np.array(model_dict['classes_']).astype(np.int64)

    return model


def serialize_label_binarizer(label_binarizer):
    serialized_label_binarizer = {
        'neg_label': label_binarizer.neg_label,
        'pos_label': label_binarizer.pos_label,
        'sparse_output': label_binarizer.sparse_output,
        'y_type_': label_binarizer.y_type_,
        'sparse_input_': label_binarizer.sparse_input_,
        'classes_': label_binarizer.classes_.tolist()
    }

    return serialized_label_binarizer


def deserialize_label_binarizer(label_binarizer_dict):
    label_binarizer = LabelBinarizer()
    label_binarizer.neg_label = label_binarizer_dict['neg_label']
    label_binarizer.pos_label = label_binarizer_dict['pos_label']
    label_binarizer.sparse_output = label_binarizer_dict['sparse_output']
    label_binarizer.y_type_ = label_binarizer_dict['y_type_']
    label_binarizer.sparse_input_ = label_binarizer_dict['sparse_input_']
    label_binarizer.classes_ = np.array(label_binarizer_dict['classes_'])

    return label_binarizer


def serialize_mlp(model):
    serialized_model = {
        'meta': 'mlp',
        'coefs_': [array.tolist() for array in model.coefs_],
        'loss_': model.loss_,
        'intercepts_': [array.tolist() for array in model.intercepts_],
        'n_iter_': model.n_iter_,
        'n_layers_': model.n_layers_,
        'n_outputs_': model.n_outputs_,
        'out_activation_': model.out_activation_,
        '_label_binarizer': serialize_label_binarizer(model._label_binarizer),
        'params': model.get_params()
    }

    if isinstance(model.classes_, list):
        serialized_model['classes_'] = [array.tolist() for array in model.classes_]
    else:
        serialized_model['classes_'] = model.classes_.tolist()

    return serialized_model


def deserialize_mlp(model_dict):
    model = MLPClassifier(**model_dict['params'])

    model.coefs_ = np.array(model_dict['coefs_'], dtype=object)
    model.loss_ = model_dict['loss_']
    model.intercepts_ = np.array(model_dict['intercepts_'], dtype=object)
    model.n_iter_ = model_dict['n_iter_']
    model.n_layers_ = model_dict['n_layers_']
    model.n_outputs_ = model_dict['n_outputs_']
    model.out_activation_ = model_dict['out_activation_']
    model._label_binarizer = deserialize_label_binarizer(model_dict['_label_binarizer'])

    model.classes_ = np.array(model_dict['classes_'])

    for i, x in enumerate(model.coefs_):
	    model.coefs_[i] = np.array(x)

    return model


########################################################################################
#
#                                  __init__.py
#
########################################################################################

def serialize_model(model):
    if isinstance(model, LogisticRegression):
        return serialize_logistic_regression(model)
    elif isinstance(model, BernoulliNB):
        return serialize_bernoulli_nb(model)
    elif isinstance(model, GaussianNB):
        return serialize_gaussian_nb(model)
    elif isinstance(model, MultinomialNB):
        return serialize_multinomial_nb(model)
    elif isinstance(model, ComplementNB):
        return serialize_complement_nb(model)
    elif isinstance(model, discriminant_analysis.LinearDiscriminantAnalysis):
        return serialize_lda(model)
    elif isinstance(model, discriminant_analysis.QuadraticDiscriminantAnalysis):
        return serialize_qda(model)
    elif isinstance(model, svm.SVC):
        return serialize_svm(model)
    elif isinstance(model, Perceptron):
        return serialize_perceptron(model)
    elif isinstance(model, DecisionTreeClassifier):
        return serialize_decision_tree(model)
    elif isinstance(model, GradientBoostingClassifier):
        return serialize_gradient_boosting(model)
    elif isinstance(model, RandomForestClassifier):
        return serialize_random_forest(model)
    elif isinstance(model, MLPClassifier):
        return serialize_mlp(model)

    elif isinstance(model, LinearRegression):
        return serialize_linear_regressor(model)
    elif isinstance(model, Lasso):
        return serialize_lasso_regressor(model)
    elif isinstance(model, Ridge):
        return serialize_ridge_regressor(model)
    elif isinstance(model, SVR):
        return serialize_svr(model)
    elif isinstance(model, DecisionTreeRegressor):
        return serialize_decision_tree_regressor(model)
    elif isinstance(model, GradientBoostingRegressor):
        return serialize_gradient_boosting_regressor(model)
    elif isinstance(model, RandomForestRegressor):
        return serialize_random_forest_regressor(model)
    elif isinstance(model, MLPRegressor):
        return serialize_mlp_regressor(model)
    else:
        raise ModellNotSupported('This model type is not currently supported. Email support@mlrequest.com to request a feature or report a bug.')


def deserialize_model(model_dict):
    if model_dict['meta'] == 'lr':
        return deserialize_logistic_regression(model_dict)
    elif model_dict['meta'] == 'bernoulli-nb':
        return deserialize_bernoulli_nb(model_dict)
    elif model_dict['meta'] == 'gaussian-nb':
        return deserialize_gaussian_nb(model_dict)
    elif model_dict['meta'] == 'multinomial-nb':
        return deserialize_multinomial_nb(model_dict)
    elif model_dict['meta'] == 'complement-nb':
        return deserialize_complement_nb(model_dict)
    elif model_dict['meta'] == 'lda':
        return deserialize_lda(model_dict)
    elif model_dict['meta'] == 'qda':
        return deserialize_qda(model_dict)
    elif model_dict['meta'] == 'svm':
        return deserialize_svm(model_dict)
    elif model_dict['meta'] == 'perceptron':
        return deserialize_perceptron(model_dict)
    elif model_dict['meta'] == 'decision-tree':
        return deserialize_decision_tree(model_dict)
    elif model_dict['meta'] == 'gb':
        return deserialize_gradient_boosting(model_dict)
    elif model_dict['meta'] == 'rf':
        return deserialize_random_forest(model_dict)
    elif model_dict['meta'] == 'mlp':
        return deserialize_mlp(model_dict)

    elif model_dict['meta'] == 'linear-regression':
        return deserialize_linear_regressor(model_dict)
    elif model_dict['meta'] == 'lasso-regression':
        return deserialize_lasso_regressor(model_dict)
    elif model_dict['meta'] == 'ridge-regression':
        return deserialize_ridge_regressor(model_dict)
    elif model_dict['meta'] == 'svr':
        return deserialize_svr(model_dict)
    elif model_dict['meta'] == 'decision-tree-regression':
        return deserialize_decision_tree_regressor(model_dict)
    elif model_dict['meta'] == 'gb-regression':
        return deserialize_gradient_boosting_regressor(model_dict)
    elif model_dict['meta'] == 'rf-regression':
        return deserialize_random_forest_regressor(model_dict)
    elif model_dict['meta'] == 'mlp-regression':
        return deserialize_mlp_regressor(model_dict)
    else:
        raise ModellNotSupported('Model type not supported or corrupt JSON file. Email support@mlrequest.com to request a feature or report a bug.')


def to_dict(model):
    return serialize_model(model)


def from_dict(model_dict):
    return deserialize_model(model_dict)


def to_json(model, model_name):
    with open(model_name, 'w') as model_json:
        json.dump(serialize_model(model), model_json)


def from_json(model_name):
    with open(model_name, 'r') as model_json:
        model_dict = json.load(model_json)
        return deserialize_model(model_dict)

class ModellNotSupported(Exception):
    pass


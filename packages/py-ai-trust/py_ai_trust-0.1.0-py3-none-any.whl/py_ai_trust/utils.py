import numpy as np
import pandas as pd
import logging
import random # For set_random_seed
import torch # For device setup (even if scikit-learn heavy, good for future)
from typing import Union, Optional, Dict, Any, Callable
from sklearn.base import ClassifierMixin, RegressorMixin
from sklearn.metrics import accuracy_score, mean_squared_error, r2_score, f1_score # Common metrics

# Set up a logger for the entire py_ai_trust library
# This helps manage logging consistently across modules
logger = logging.getLogger(__name__)
if not logger.handlers: # Prevent adding multiple handlers if already configured
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def set_random_seed(seed: int = 42) -> None:
    """
    Sets the random seed for reproducibility across different libraries (numpy, random, torch).
    Ensures that experiments can be replicated.

    Args:
        seed (int): The seed value to use for random number generators.
    """
    logger.info(f"Setting random seed to {seed} for reproducibility.")
    random.seed(seed)
    np.random.seed(seed)
    # If PyTorch is installed and used:
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    torch.manual_seed(seed)


def setup_device(device_id: int = 0) -> torch.device:
    """
    Sets up the device (GPU or CPU) for PyTorch operations.
    Useful if some model components or computations are done in PyTorch.

    Args:
        device_id (int): The ID of the GPU to use if available. Defaults to 0.

    Returns:
        torch.device: The PyTorch device object.
    """
    if torch.cuda.is_available():
        num_gpus = torch.cuda.device_count()
        if device_id < num_gpus:
            device = torch.device(f"cuda:{device_id}")
            torch.cuda.set_device(device_id)
            logger.info(f"Using GPU: {torch.cuda.get_device_name(device_id)} (ID: {device_id})")
        else:
            logger.warning(f"GPU ID {device_id} not found. Available GPUs: {num_gpus}. Falling back to CPU.")
            device = torch.device("cpu")
    else:
        logger.info("No GPU found. Using CPU.")
        device = torch.device("cpu")
    return device


def calculate_performance_metric(y_true: np.ndarray, y_pred: np.ndarray, 
                                 model_type: Union[ClassifierMixin, RegressorMixin, str]) -> Dict[str, float]:
    """
    Calculates an appropriate performance metric based on the model type.

    Args:
        y_true (np.ndarray): True labels or regression targets.
        y_pred (np.ndarray): Predicted labels or regression outputs.
        model_type (Union[ClassifierMixin, RegressorMixin, str]): The trained scikit-learn model
                                                                   instance or a string ('classifier', 'regressor').

    Returns:
        Dict[str, float]: A dictionary containing the metric name and its score.
    """
    if isinstance(model_type, ClassifierMixin) or model_type == 'classifier':
        # For classification, return accuracy and F1-score (for binary/multiclass)
        # Assuming y_pred are hard labels (0 or 1) for classification
        try:
            acc = accuracy_score(y_true, y_pred)
            # For f1_score, determine average method dynamically
            if np.unique(y_true).shape[0] > 2: # Multiclass
                f1 = f1_score(y_true, y_pred, average='weighted', zero_division=0)
            else: # Binary
                f1 = f1_score(y_true, y_pred, average='binary', zero_division=0)
            return {"metric": "accuracy", "score": float(acc), "f1_score": float(f1)}
        except Exception as e:
            logger.warning(f"Error calculating classification metrics: {e}. Returning accuracy only.")
            return {"metric": "accuracy", "score": float(accuracy_score(y_true, y_pred))}

    elif isinstance(model_type, RegressorMixin) or model_type == 'regressor':
        # For regression, return Mean Squared Error (MSE) and R-squared
        try:
            mse = mean_squared_error(y_true, y_pred)
            r2 = r2_score(y_true, y_pred)
            return {"metric": "mse", "score": float(mse), "r2_score": float(r2)}
        except Exception as e:
            logger.warning(f"Error calculating regression metrics: {e}. Returning MSE only.")
            return {"metric": "mse", "score": float(mean_squared_error(y_true, y_pred))}
    else:
        logger.warning(f"Unknown model type for performance calculation: {type(model_type)}. Returning NaN.")
        return {"metric": "unknown", "score": np.nan}


def check_input_data_type(data: Union[np.ndarray, pd.DataFrame]) -> str:
    """
    Checks the type of input data and returns a descriptive string.

    Args:
        data (Union[np.ndarray, pd.DataFrame]): The input data.

    Returns:
        str: 'numpy_array', 'pandas_dataframe', or 'unsupported'.
    """
    if isinstance(data, np.ndarray):
        return 'numpy_array'
    elif isinstance(data, pd.DataFrame):
        return 'pandas_dataframe'
    else:
        logger.warning(f"Unsupported data type: {type(data)}. Expected numpy.ndarray or pandas.DataFrame.")
        return 'unsupported'

# --- Example Usage ---
if __name__ == "__main__":
    print("--- Testing py_ai_trust.utils ---")

    # Test 1: set_random_seed
    set_random_seed(123)
    print(f"Random number (numpy): {np.random.rand()}")
    print(f"Random number (random): {random.random()}")
    # For PyTorch, you'd test torch.randn, but it's set globally.

    # Test 2: setup_device
    device = setup_device()
    print(f"Detected device: {device}")
    dummy_tensor = torch.randn(2, 2).to(device)
    print(f"Dummy tensor created on device: {dummy_tensor.device}")

    # Test 3: calculate_performance_metric
    from sklearn.linear_model import LogisticRegression, LinearRegression
    
    # Classification example
    y_true_clf = np.array([0, 1, 0, 1, 0, 1, 0, 1])
    y_pred_clf = np.array([0, 0, 0, 1, 1, 1, 0, 1])
    
    clf_model = LogisticRegression() # Dummy model type for function
    clf_metrics = calculate_performance_metric(y_true_clf, y_pred_clf, clf_model)
    print(f"\nClassification Metrics (LogisticRegression): {clf_metrics}")

    # Regression example
    y_true_reg = np.array([1.0, 2.1, 3.0, 4.2])
    y_pred_reg = np.array([1.2, 2.0, 3.1, 4.0])

    reg_model = LinearRegression() # Dummy model type for function
    reg_metrics = calculate_performance_metric(y_true_reg, y_pred_reg, reg_model)
    print(f"Regression Metrics (LinearRegression): {reg_metrics}")

    # Test with string model type
    clf_metrics_str = calculate_performance_metric(y_true_clf, y_pred_clf, 'classifier')
    print(f"Classification Metrics (string 'classifier'): {clf_metrics_str}")

    # Test 4: check_input_data_type
    numpy_array = np.array([[1, 2], [3, 4]])
    pandas_df = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
    
    print(f"\nData type check for numpy_array: {check_input_data_type(numpy_array)}")
    print(f"Data type check for pandas_df: {check_input_data_type(pandas_df)}")
    print(f"Data type check for list: {check_input_data_type([1, 2, 3])}") # Should warn and return 'unsupported'

    print("\n--- py_ai_trust.utils testing complete ---")

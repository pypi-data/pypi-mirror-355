import numpy as np
import pandas as pd
import logging
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Any, Union, Optional, Callable
from sklearn.base import BaseEstimator, ClassifierMixin, RegressorMixin
from sklearn.metrics import accuracy_score, mean_squared_error, get_scorer
from sklearn.inspection import PartialDependenceDisplay, plot_partial_dependence # For PDPs
from sklearn.model_selection import permutation_test_score # For permutation importance

# Set up basic logging for this module
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class ExplainabilityEnhancer:
    """
    Provides tools for enhancing the explainability and interpretability of
    machine learning models, focusing on global insights into model behavior.
    """
    def __init__(self):
        logger.info("ExplainabilityEnhancer initialized.")

    def calculate_permutation_importance(self,
                                         model: BaseEstimator,
                                         X: Union[np.ndarray, pd.DataFrame],
                                         y: np.ndarray,
                                         scoring: Union[str, Callable] = 'accuracy',
                                         n_repeats: int = 5,
                                         random_state: Optional[int] = None) -> Dict[str, float]:
        """
        Calculates permutation importance for each feature. This is a model-agnostic
        method that measures the decrease in a model's score when a single feature
        is randomly shuffled, breaking its relationship with the target.

        Args:
            model (BaseEstimator): The trained machine learning model.
            X (Union[np.ndarray, pd.DataFrame]): Input features (validation or test set).
            y (np.ndarray): True labels or regression targets.
            scoring (Union[str, Callable]): Metric to use for scoring (e.g., 'accuracy', 'f1', 'neg_mean_squared_error').
                                            Can be a string accepted by sklearn.metrics.get_scorer or a callable.
            n_repeats (int): Number of times to permute a feature. Higher values give more robust results.
            random_state (Optional[int]): Seed for reproducibility.

        Returns:
            Dict[str, float]: A dictionary where keys are feature names and values are their
                              permutation importance scores (mean decrease in score).
        """
        logger.info(f"Calculating permutation importance using scoring '{scoring}' with {n_repeats} repeats.")
        
        if isinstance(X, pd.DataFrame):
            feature_names = X.columns.tolist()
            X_np = X.to_numpy()
        else:
            feature_names = [f'Feature_{i}' for i in range(X.shape[1])]
            X_np = X

        # Ensure y is 1D
        y_np = np.squeeze(y)

        # Calculate permutation importance
        try:
            # permutation_test_score returns 3 values: score, permutations_scores, pvalue
            # We are interested in the difference between the original score and the permuted scores
            
            # The direct way to get permutation importance:
            from sklearn.inspection import permutation_importance
            
            result = permutation_importance(
                estimator=model,
                X=X, # permutation_importance can handle DataFrame directly
                y=y_np,
                scoring=scoring,
                n_repeats=n_repeats,
                random_state=random_state,
                n_jobs=-1 # Use all available CPU cores
            )
            
            importances = result.importances_mean
            
            importance_dict = dict(zip(feature_names, importances))
            # Sort by importance in descending order
            sorted_importance = {k: v for k, v in sorted(importance_dict.items(), key=lambda item: item[1], reverse=True)}
            
            logger.info("Permutation importance calculation complete.")
            return sorted_importance
        except Exception as e:
            logger.error(f"Error calculating permutation importance: {e}. Ensure model is fitted and scoring metric is valid.")
            return {}

    def plot_permutation_importance(self,
                                    importance_scores: Dict[str, float],
                                    title: str = "Permutation Importance",
                                    save_path: Optional[str] = None) -> None:
        """
        Plots the permutation importance scores as a horizontal bar chart.

        Args:
            importance_scores (Dict[str, float]): Dictionary of feature names and their importance scores.
                                                 Typically output from `calculate_permutation_importance`.
            title (str): Title for the plot.
            save_path (Optional[str]): Path to save the plot (e.g., "permutation_importance.png").
                                      If None, the plot is displayed.
        """
        if not importance_scores:
            logger.warning("No importance scores provided for plotting.")
            return

        features = list(importance_scores.keys())
        scores = list(importance_scores.values())

        # Sort for better visualization
        sorted_indices = np.argsort(scores)
        features_sorted = [features[i] for i in sorted_indices]
        scores_sorted = [scores[i] for i in sorted_indices]

        plt.figure(figsize=(10, max(6, len(features) * 0.4)))
        sns.barplot(x=scores_sorted, y=features_sorted, palette='viridis')
        plt.xlabel("Importance (Mean Decrease in Score)")
        plt.ylabel("Feature")
        plt.title(title)
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path)
            logger.info(f"Permutation importance plot saved to '{save_path}'.")
        plt.show()

    def plot_partial_dependence(self,
                                model: BaseEstimator,
                                X: Union[np.ndarray, pd.DataFrame],
                                features_to_plot: Union[List[Union[str, int]], List[Tuple[Union[str, int], Union[str, int]]]],
                                feature_names: Optional[List[str]] = None,
                                grid_resolution: int = 20,
                                title: str = "Partial Dependence Plots",
                                save_path: Optional[str] = None) -> None:
        """
        Generates Partial Dependence Plots (PDPs) for single or pairs of features.
        PDPs show the marginal effect of one or two features on the predicted outcome
        of a fitted model.

        Args:
            model (BaseEstimator): The trained machine learning model.
            X (Union[np.ndarray, pd.DataFrame]): Input features used to train the model.
            features_to_plot (Union[List[Union[str, int]], List[Tuple[Union[str, int], Union[str, int]]]]):
                List of features for which to plot PDPs. Can be:
                - Single feature: `['feature_name_A', 'feature_name_B']` or `[0, 1]` (column indices).
                - Feature pairs: `[('feature_name_A', 'feature_name_B'), (0, 1)]`.
            feature_names (Optional[List[str]]): List of names for columns in X if X is a NumPy array.
                                                 Required if `features_to_plot` uses string names and X is array.
            grid_resolution (int): Number of points on the grid for each feature.
            title (str): Main title for the plot.
            save_path (Optional[str]): Path to save the plot.
        """
        logger.info(f"Generating Partial Dependence Plots for features: {features_to_plot}.")

        if isinstance(X, np.ndarray) and feature_names is None:
            logger.error("`feature_names` must be provided if `X` is a NumPy array and `features_to_plot` uses string names.")
            return

        # Handle feature names for plotting if X is numpy array
        if isinstance(X, np.ndarray) and feature_names:
            X_df = pd.DataFrame(X, columns=feature_names)
        else:
            X_df = X # Assume it's already a DataFrame or will be handled by sklearn

        try:
            # PartialDependenceDisplay.from_estimator can handle lists of single features or tuples of pairs
            # The `features` argument expects either integer indices or column names if X is a DataFrame.
            # If X is numpy array, it expects indices.

            # Convert string feature names to indices if X is np.ndarray and feature_names provided
            if isinstance(X, np.ndarray) and feature_names:
                mapped_features_to_plot = []
                for f in features_to_plot:
                    if isinstance(f, str):
                        mapped_features_to_plot.append(feature_names.index(f))
                    elif isinstance(f, tuple):
                        mapped_features_to_plot.append(tuple(feature_names.index(sub_f) if isinstance(sub_f, str) else sub_f for sub_f in f))
                    else:
                        mapped_features_to_plot.append(f)
            else: # If X is DataFrame or features_to_plot already indices
                mapped_features_to_plot = features_to_plot

            fig, ax = plt.subplots(figsize=(15, 8)) # Adjust size dynamically if many plots
            # Dynamically determine rows/cols for subplots based on number of features to plot
            n_plots = len(mapped_features_to_plot)
            n_cols = 2 if n_plots > 1 else 1
            n_rows = (n_plots + n_cols - 1) // n_cols # Ceiling division

            fig.set_size_inches(n_cols * 7, n_rows * 5) # Adjust subplot size

            PartialDependenceDisplay.from_estimator(
                estimator=model,
                X=X_df, # Pass DataFrame if available, or np.array otherwise
                features=mapped_features_to_plot,
                feature_names=feature_names if isinstance(X, np.ndarray) else X.columns.tolist(), # Ensure feature_names for plots
                grid_resolution=grid_resolution,
                ax=ax if n_plots == 1 else None # Only pass ax if single plot
            )
            
            fig.suptitle(title, y=1.02, fontsize=16) # y=1.02 to place title above subplots
            plt.tight_layout(rect=[0, 0, 1, 0.98]) # Adjust layout to prevent title overlap
            
            if save_path:
                plt.savefig(save_path)
                logger.info(f"Partial Dependence Plots saved to '{save_path}'.")
            plt.show()

        except Exception as e:
            logger.error(f"Error generating Partial Dependence Plots: {e}. "
                         f"Ensure model is fitted, features are numeric, and 'features_to_plot' are valid.")
            logger.info("Check `sklearn.inspection.PartialDependenceDisplay` documentation for details.")


    def plot_individual_conditional_expectation(self,
                                                model: BaseEstimator,
                                                X: Union[np.ndarray, pd.DataFrame],
                                                feature_index_or_name: Union[int, str],
                                                feature_names: Optional[List[str]] = None,
                                                num_individual_plots: int = 10,
                                                grid_resolution: int = 20,
                                                title: str = "Individual Conditional Expectation (ICE) Plot",
                                                save_path: Optional[str] = None) -> None:
        """
        Generates an Individual Conditional Expectation (ICE) plot for a single feature.
        ICE plots show how the prediction for *each individual instance* changes as the value
        of a single feature changes, while all other features are held constant.

        Args:
            model (BaseEstimator): The trained machine learning model.
            X (Union[np.ndarray, pd.DataFrame]): Input features.
            feature_index_or_name (Union[int, str]): The index or name of the feature to plot.
            feature_names (Optional[List[str]]): List of names for columns in X if X is a NumPy array.
                                                 Required if `feature_index_or_name` is a string and X is array.
            num_individual_plots (int): Number of individual ICE curves to plot.
            grid_resolution (int): Number of points on the grid for the feature.
            title (str): Title for the plot.
            save_path (Optional[str]): Path to save the plot.
        """
        logger.info(f"Generating ICE plot for feature: '{feature_index_or_name}'.")

        if isinstance(X, np.ndarray) and feature_names is None and isinstance(feature_index_or_name, str):
            logger.error("`feature_names` must be provided if `X` is a NumPy array and `feature_index_or_name` is a string.")
            return

        # Ensure X is DataFrame for easier handling with `feature_names`
        if isinstance(X, np.ndarray) and feature_names:
            X_df = pd.DataFrame(X, columns=feature_names)
        elif isinstance(X, pd.DataFrame):
            X_df = X
        else: # X is a numpy array and feature_index_or_name is int
            X_df = X 
        
        # Select a random subset of instances for individual plots
        if len(X_df) > num_individual_plots:
            # Use np.random.choice to get unique indices without replacement
            random_indices = np.random.choice(len(X_df), num_individual_plots, replace=False)
            X_subset = X_df.iloc[random_indices] if isinstance(X_df, pd.DataFrame) else X_df[random_indices]
        else:
            X_subset = X_df # Use all instances if fewer than num_individual_plots

        try:
            # The `PartialDependenceDisplay` can also generate ICE plots when `kind='individual'` is used
            # We plot the PDP (average) and individual ICE curves
            fig, ax = plt.subplots(figsize=(10, 6))
            
            PartialDependenceDisplay.from_estimator(
                estimator=model,
                X=X_df, # Pass the full DataFrame for PDP calculation background
                features=[feature_index_or_name], # PDP expects a list of features
                feature_names=feature_names if isinstance(X, np.ndarray) else X.columns.tolist(),
                grid_resolution=grid_resolution,
                ax=ax,
                # kind='individual' is not a direct parameter for from_estimator.
                # Instead, plot_partial_dependence with individual parameter generates ICE.
                # Let's use the older `plot_partial_dependence` for ICE directly if from_estimator doesn't support it.
                # Actually, `PartialDependenceDisplay.from_estimator` with `kind='both'` will show both.
                kind='both' # 'both' shows PDP and ICE curves
            )
            
            ax.set_title(title)
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path)
                logger.info(f"Individual Conditional Expectation (ICE) plot saved to '{save_path}'.")
            plt.show()

        except Exception as e:
            logger.error(f"Error generating Individual Conditional Expectation (ICE) Plot: {e}. "
                         f"Ensure model is fitted, feature is numeric, and 'feature_index_or_name' is valid.")
            logger.info("Check `sklearn.inspection.PartialDependenceDisplay` documentation for details.")


# --- Example Usage ---
if __name__ == "__main__":
    print("--- Testing py_ai_trust.explainability ---")

    np.random.seed(42)

    # --- Setup: Dummy Classifier Model and Data ---
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.datasets import make_classification

    # Generate a synthetic classification dataset
    X, y = make_classification(n_samples=1000, n_features=10, n_informative=5, n_redundant=2,
                               n_clusters_per_class=1, random_state=42, flip_y=0.1)
    
    # Convert X to DataFrame for easier feature naming
    feature_names = [f'F{i}' for i in range(X.shape[1])]
    X_df = pd.DataFrame(X, columns=feature_names)

    # Split into training and test sets
    X_train, X_test, y_train, y_test = train_test_split(X_df, y, test_size=0.3, random_state=42)

    # Train a RandomForestClassifier
    model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    
    y_pred_test = model.predict(X_test)
    test_accuracy = accuracy_score(y_test, y_pred_test)
    print(f"Model trained. Test Accuracy: {test_accuracy:.4f}")
    print("-" * 50)

    enhancer = ExplainabilityEnhancer()

    # --- Test 1: Permutation Importance ---
    print("\n--- Test 1: Calculating and Plotting Permutation Importance ---")
    importance_scores = enhancer.calculate_permutation_importance(
        model=model,
        X=X_test, # Use test set for evaluation
        y=y_test,
        scoring='accuracy',
        n_repeats=10,
        random_state=42
    )
    print("\nPermutation Importance Scores:")
    for feature, score in importance_scores.items():
        print(f"  {feature}: {score:.4f}")
    
    enhancer.plot_permutation_importance(importance_scores, save_path="permutation_importance.png")
    print("-" * 50)

    # --- Test 2: Partial Dependence Plots (PDP) ---
    print("\n--- Test 2: Generating Partial Dependence Plots (PDP) ---")
    
    # Plot single features
    enhancer.plot_partial_dependence(
        model=model,
        X=X_test, # Can use X_train or X_test
        features_to_plot=['F0', 'F1', 'F2'], # Plot F0, F1, F2
        feature_names=feature_names, # Provide if X is numpy array
        grid_resolution=30,
        title="Partial Dependence for Individual Features",
        save_path="pdp_single_features.png"
    )

    # Plot feature pairs (interaction)
    enhancer.plot_partial_dependence(
        model=model,
        X=X_test,
        features_to_plot=[('F0', 'F1'), ('F3', 'F4')], # Plot interactions between F0 & F1, and F3 & F4
        feature_names=feature_names,
        grid_resolution=20,
        title="Partial Dependence for Feature Interactions",
        save_path="pdp_feature_pairs.png"
    )
    print("-" * 50)

    # --- Test 3: Individual Conditional Expectation (ICE) Plots ---
    print("\n--- Test 3: Generating Individual Conditional Expectation (ICE) Plot ---")
    
    enhancer.plot_individual_conditional_expectation(
        model=model,
        X=X_test,
        feature_index_or_name='F0', # Plot ICE for Feature 0
        feature_names=feature_names,
        num_individual_plots=15, # Plot 15 individual curves
        grid_resolution=30,
        title="ICE Plot for Feature F0",
        save_path="ice_plot_F0.png"
    )
    print("-" * 50)

    # --- Cleanup ---
    print("\n--- Cleaning up temporary files ---")
    if os.path.exists("permutation_importance.png"): os.remove("permutation_importance.png")
    if os.path.exists("pdp_single_features.png"): os.remove("pdp_single_features.png")
    if os.path.exists("pdp_feature_pairs.png"): os.remove("pdp_feature_pairs.png")
    if os.path.exists("ice_plot_F0.png"): os.remove("ice_plot_F0.png")
    print("\n--- py_ai_trust.explainability testing complete ---")

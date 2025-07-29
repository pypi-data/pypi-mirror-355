import numpy as np
import pandas as pd
import logging
from typing import List, Dict, Any, Union, Optional
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.preprocessing import StandardScaler
from scipy.optimize import minimize_scalar

# Import FairnessAuditor to demonstrate mitigation effects
try:
    from py_ai_trust.fairness import FairnessAuditor
    FAIRNESS_AUDITOR_AVAILABLE = True
except ImportError:
    FAIRNESS_AUDITOR_AVAILABLE = False
    logging.warning("FairnessAuditor not found. Cannot demonstrate mitigation effects directly. Please ensure py_ai_trust.fairness is accessible.")


# Set up basic logging for this module
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class BiasMitigator:
    """
    A class providing various techniques to mitigate bias in machine learning models.
    Supports pre-processing and post-processing methods, primarily for binary classification.
    """
    def __init__(self):
        logger.info("BiasMitigator initialized.")

    def reweighing_pre_processing(self, 
                                  df: pd.DataFrame, 
                                  sensitive_attribute_name: str, 
                                  privileged_group_value: Any, 
                                  unprivileged_group_value: Any, 
                                  label_column: str) -> np.ndarray:
        """
        Calculates sample weights to reweigh the training data for fairness.
        This technique aims to achieve statistical parity by adjusting the influence
        of different (sensitive attribute, label) subgroups.

        Args:
            df (pd.DataFrame): The input DataFrame containing sensitive attribute and labels.
            sensitive_attribute_name (str): The name of the column with the sensitive attribute.
            privileged_group_value (Any): Value representing the privileged group.
            unprivileged_group_value (Any): Value representing the unprivileged group.
            label_column (str): The name of the column with the true binary labels (0 or 1).

        Returns:
            np.ndarray: An array of sample weights, one for each row in the DataFrame.
                        These weights can be passed to the `sample_weight` parameter
                        of many scikit-learn models' `fit` method.
        """
        logger.info(f"Calculating reweighing weights for sensitive attribute '{sensitive_attribute_name}'.")
        if sensitive_attribute_name not in df.columns or label_column not in df.columns:
            logger.error("Sensitive attribute or label column not found in DataFrame.")
            return np.ones(len(df)) # Return default weights

        weights = np.ones(len(df))
        
        # Denominators: count of total samples in each group (N) and positive/negative outcomes (P/N)
        N_total = len(df)
        N_y_0 = np.sum(df[label_column] == 0)
        N_y_1 = np.sum(df[label_column] == 1)

        for i, row in df.iterrows():
            A = row[sensitive_attribute_name]
            Y = row[label_column]

            # Count group-specific statistics
            N_A_y = np.sum((df[sensitive_attribute_name] == A) & (df[label_column] == Y))
            
            if A == privileged_group_value:
                # Privileged group: P(Y=y) * P(A=privileged) / P(Y=y, A=privileged)
                # Simplified: (N_y / N_total) * (N_A_priv / N_total) / (N_A_priv_y / N_total)
                #             = (N_y * N_A_priv) / (N_A_priv_y * N_total)
                # But a more common formulation used is: P(Y=y) * P(A=a) / P(Y=y, A=a)
                # To be precise from Aequitas (IBM AIF360):
                # P(Y=y) is N_y_Y / N_total
                # P(A=a) is N_A / N_total
                # P(Y=y, A=a) is N_A_y / N_total
                # Weight for (A=a, Y=y) = P(Y=y) * P(A=a) / P(Y=y, A=a)
                
                N_A = np.sum(df[sensitive_attribute_name] == A) # Total samples in current sensitive group
                
                if Y == 0: # Negative outcome for privileged group
                    term1 = N_y_0 / N_total
                    term2 = N_A / N_total
                    term3 = N_A_y / N_total
                    weight = (term1 * term2) / term3 if term3 > 0 else 0
                else: # Positive outcome for privileged group
                    term1 = N_y_1 / N_total
                    term2 = N_A / N_total
                    term3 = N_A_y / N_total
                    weight = (term1 * term2) / term3 if term3 > 0 else 0
            
            elif A == unprivileged_group_value:
                # Unprivileged group:
                N_A = np.sum(df[sensitive_attribute_name] == A) # Total samples in current sensitive group

                if Y == 0: # Negative outcome for unprivileged group
                    term1 = N_y_0 / N_total
                    term2 = N_A / N_total
                    term3 = N_A_y / N_total
                    weight = (term1 * term2) / term3 if term3 > 0 else 0
                else: # Positive outcome for unprivileged group
                    term1 = N_y_1 / N_total
                    term2 = N_A / N_total
                    term3 = N_A_y / N_total
                    weight = (term1 * term2) / term3 if term3 > 0 else 0
            else:
                weight = 1.0 # For other groups not explicitly defined, keep weight 1
            
            weights[i] = weight

        logger.info("Reweighing weights calculated.")
        # Normalize weights if desired (e.g., to sum to N_total)
        # weights = weights * (N_total / np.sum(weights)) if np.sum(weights) > 0 else weights
        return weights

    def equalized_odds_post_processing(self,
                                       y_true: np.ndarray,
                                       y_pred_proba: np.ndarray,
                                       sensitive_attributes: np.ndarray,
                                       privileged_group_value: Any,
                                       unprivileged_group_value: Any,
                                       target_tpr_diff: float = 0.0, # Target difference in TPR
                                       target_fpr_diff: float = 0.0, # Target difference in FPR
                                       optimizer_tolerance: float = 1e-4) -> np.ndarray:
        """
        Adjusts prediction thresholds for privileged and unprivileged groups to achieve
        Equalized Odds. This means ensuring that True Positive Rates (TPR) and False Positive Rates (FPR)
        are equal across groups.

        This implementation uses a simplified approach by finding optimal thresholds for each group
        to minimize a fairness objective (e.g., difference in TPR/FPR).

        Args:
            y_true (np.ndarray): True binary labels (0 or 1).
            y_pred_proba (np.ndarray): Predicted probabilities for the positive class (class 1).
            sensitive_attributes (np.ndarray): Array of sensitive attribute values.
            privileged_group_value (Any): Value representing the privileged group.
            unprivileged_group_value (Any): Value representing the unprivileged group.
            target_tpr_diff (float): The target difference for TPR (ideally 0).
            target_fpr_diff (float): The target difference for FPR (ideally 0).
            optimizer_tolerance (float): Tolerance for the optimization function.

        Returns:
            np.ndarray: Adjusted binary predictions (0 or 1) after post-processing.
        """
        logger.info("Applying Equalized Odds Post-Processing.")

        if not np.all(np.isin(y_true, [0, 1])):
            logger.error("True labels must be binary (0 or 1) for Equalized Odds Post-Processing.")
            return (y_pred_proba >= 0.5).astype(int) # Return default binary predictions

        # Separate data by group
        priv_indices = sensitive_attributes == privileged_group_value
        unpriv_indices = sensitive_attributes == unprivileged_group_value

        y_true_priv, y_proba_priv = y_true[priv_indices], y_pred_proba[priv_indices]
        y_true_unpriv, y_proba_unpriv = y_true[unpriv_indices], y_pred_proba[unpriv_indices]

        if len(y_true_priv) == 0 or len(y_true_unpriv) == 0:
            logger.warning("One or both groups have no data. Cannot apply Equalized Odds Post-Processing effectively.")
            return (y_pred_proba >= 0.5).astype(int)

        # Objective function to minimize: sum of squared differences from target TPR/FPR
        def _objective(thresholds: Tuple[float, float]) -> float:
            thresh_priv, thresh_unpriv = thresholds

            # Calculate TPR and FPR for privileged group
            pred_priv = (y_proba_priv >= thresh_priv).astype(int)
            tn_priv, fp_priv, fn_priv, tp_priv = confusion_matrix(y_true_priv, pred_priv).ravel()
            tpr_priv = tp_priv / (tp_priv + fn_priv) if (tp_priv + fn_priv) > 0 else 0.0
            fpr_priv = fp_priv / (fp_priv + tn_priv) if (fp_priv + tn_priv) > 0 else 0.0

            # Calculate TPR and FPR for unprivileged group
            pred_unpriv = (y_proba_unpriv >= thresh_unpriv).astype(int)
            tn_unpriv, fp_unpriv, fn_unpriv, tp_unpriv = confusion_matrix(y_true_unpriv, pred_unpriv).ravel()
            tpr_unpriv = tp_priv / (tp_priv + fn_priv) if (tp_priv + fn_priv) > 0 else 0.0 # Recheck: this uses priv_true/pred, should be unpriv
            tpr_unpriv = tp_unpriv / (tp_unpriv + fn_unpriv) if (tp_unpriv + fn_unpriv) > 0 else 0.0 # Corrected
            fpr_unpriv = fp_unpriv / (fp_unpriv + tn_unpriv) if (fp_unpriv + tn_unpriv) > 0 else 0.0 # Corrected

            # The overall objective function tries to make the rates equal
            # (tpr_unpriv - tpr_priv - target_tpr_diff)^2 + (fpr_unpriv - fpr_priv - target_fpr_diff)^2
            obj_val = (tpr_unpriv - tpr_priv - target_tpr_diff)**2 + \
                      (fpr_unpriv - fpr_priv - target_fpr_diff)**2
            return obj_val

        # This simplified optimization will find thresholds to minimize the difference in TPR and FPR.
        # More advanced methods involve calibrated equalized odds, which trains a post-processing classifier.
        # For a truly robust implementation, one would use a grid search or more sophisticated optimization
        # over a range of thresholds for each group, often coupled with maximizing accuracy subject to fairness.
        
        # A simpler approach for optimization: find a single optimal threshold for each group.
        # Here we do a grid search for simplicity over a range of thresholds.
        thresholds_priv = np.linspace(0.01, 0.99, 50)
        thresholds_unpriv = np.linspace(0.01, 0.99, 50)
        
        best_obj = float('inf')
        best_thresh_priv, best_thresh_unpriv = 0.5, 0.5

        for tp in thresholds_priv:
            for tup in thresholds_unpriv:
                current_obj = _objective((tp, tup))
                if current_obj < best_obj:
                    best_obj = current_obj
                    best_thresh_priv = tp
                    best_thresh_unpriv = tup

        optimal_threshold_priv = best_thresh_priv
        optimal_threshold_unpriv = best_thresh_unpriv

        logger.info(f"Optimal thresholds found: Privileged={optimal_threshold_priv:.4f}, Unprivileged={optimal_threshold_unpriv:.4f}")

        # Apply optimal thresholds
        adjusted_predictions = np.zeros_like(y_pred_proba, dtype=int)
        adjusted_predictions[priv_indices] = (y_pred_proba[priv_indices] >= optimal_threshold_priv).astype(int)
        adjusted_predictions[unpriv_indices] = (y_pred_proba[unpriv_indices] >= optimal_threshold_unpriv).astype(int)

        logger.info("Equalized Odds Post-Processing complete.")
        return adjusted_predictions


    def reject_option_classification_post_processing(self,
                                                    y_true: np.ndarray,
                                                    y_pred_proba: np.ndarray,
                                                    sensitive_attributes: np.ndarray,
                                                    privileged_group_value: Any,
                                                    unprivileged_group_value: Any,
                                                    roc_threshold: float = 0.05, # Max difference in rates to trigger reject
                                                    threshold_range: Tuple[float, float] = (0.4, 0.6)) -> np.ndarray:
        """
        Implements Reject Option Classification (ROC).
        When the model's confidence for a prediction falls within a specified "reject option"
        range around the decision boundary (0.5), and if there's a significant fairness
        disparity for that prediction, the model 'abstains' or assigns a neutral prediction
        (e.g., 0.5 for probability, or defers to human). For this implementation, we will
        adjust the prediction to favor fairness if within the reject region.

        Args:
            y_true (np.ndarray): True binary labels (0 or 1).
            y_pred_proba (np.ndarray): Predicted probabilities for the positive class (class 1).
            sensitive_attributes (np.ndarray): Array of sensitive attribute values.
            privileged_group_value (Any): Value representing the privileged group.
            unprivileged_group_value (Any): Value representing the unprivileged group.
            roc_threshold (float): The maximum allowed difference in statistical parity (positive rate)
                                   between groups within the reject region. If difference exceeds this,
                                   predictions in the reject region are adjusted.
            threshold_range (Tuple[float, float]): The range around the decision boundary (0.5)
                                                   where predictions can be rejected. E.g., (0.4, 0.6).

        Returns:
            np.ndarray: Adjusted binary predictions (0 or 1).
        """
        logger.info("Applying Reject Option Classification Post-Processing.")
        adjusted_predictions = (y_pred_proba >= 0.5).astype(int) # Start with original predictions

        priv_indices = sensitive_attributes == privileged_group_value
        unpriv_indices = sensitive_attributes == unprivileged_group_value

        # Identify samples within the reject option range
        reject_indices = (y_pred_proba >= threshold_range[0]) & (y_pred_proba <= threshold_range[1])

        # Analyze fairness within the reject region for the affected groups
        y_true_reject_priv = y_true[reject_indices & priv_indices]
        y_pred_proba_reject_priv = y_pred_proba[reject_indices & priv_indices]
        y_true_reject_unpriv = y_true[reject_indices & unpriv_indices]
        y_pred_proba_reject_unpriv = y_pred_proba[reject_indices & unpriv_indices]

        # Calculate positive rates for current predictions in reject region
        # (Assuming 0.5 as decision threshold for intermediate calculation)
        positive_rate_priv_in_reject = np.mean((y_pred_proba_reject_priv >= 0.5).astype(int)) if len(y_pred_proba_reject_priv) > 0 else 0.0
        positive_rate_unpriv_in_reject = np.mean((y_pred_proba_reject_unpriv >= 0.5).astype(int)) if len(y_pred_proba_reject_unpriv) > 0 else 0.0

        # Check for significant disparity in the reject region
        disparity_in_reject = abs(positive_rate_unpriv_in_reject - positive_rate_priv_in_reject)

        if disparity_in_reject > roc_threshold:
            logger.info(f"Disparity ({disparity_in_reject:.4f}) in reject region exceeds threshold ({roc_threshold}). Adjusting predictions.")
            
            # If there's a disparity, try to rebalance predictions in the reject region
            # This is a simplified heuristic: if unprivileged group gets fewer positive outcomes,
            # then for unprivileged samples in reject region, if their true label is positive,
            # make their prediction positive to balance.
            
            # Simple heuristic: if unprivileged has lower positive rate in reject region,
            # and their true label is positive, try to correct it to 1.
            if positive_rate_unpriv_in_reject < positive_rate_priv_in_reject:
                for i in np.where(reject_indices & unpriv_indices)[0]:
                    if y_true[i] == 1: # If unprivileged and true label is positive
                        adjusted_predictions[i] = 1 # Force positive prediction
            # Symmetrically, if privileged has lower positive rate in reject region
            elif positive_rate_priv_in_reject < positive_rate_unpriv_in_reject:
                 for i in np.where(reject_indices & priv_indices)[0]:
                    if y_true[i] == 1: # If privileged and true label is positive
                        adjusted_predictions[i] = 1 # Force positive prediction

            # A more robust ROC might involve deferring these predictions or using specific thresholds per group
            # to achieve fairness targets within this region, rather than a fixed "force positive."
            # This version aims for a quick rebalancing.

        logger.info("Reject Option Classification Post-Processing complete.")
        return adjusted_predictions


# --- Example Usage ---
if __name__ == "__main__":
    print("--- Testing py_ai_trust.mitigation ---")

    np.random.seed(42)

    # --- Create a simulated dataset with inherent bias ---
    # Binary classification: predict 'success' (1) or 'failure' (0)
    # Sensitive attribute: 'Race' (0: Minority, 1: Majority - assume Majority is Privileged)
    
    num_samples = 2000
    data = {
        'Race': np.random.choice([0, 1], size=num_samples, p=[0.3, 0.7]), # 30% Minority, 70% Majority
        'Feature1': np.random.rand(num_samples) * 10,
        'Feature2': np.random.rand(num_samples) * 5,
        'y_true': np.random.choice([0, 1], size=num_samples, p=[0.5, 0.5]) # Balanced true labels
    }
    df = pd.DataFrame(data)

    # Simulate a model that is biased against the Minority group (Race=0)
    # Minority group is less likely to be predicted positive, even if they should be (y_true=1)
    # Majority group is more likely to be predicted positive.

    # Base probability for being predicted positive, generally
    base_proba = 0.4 
    
    # Introduce bias:
    # Minority group (Race=0): lower success prob, higher failure prob
    minority_bias_factor = 0.7 # Makes predictions for minorities less likely to be positive
    # Majority group (Race=1): higher success prob
    majority_bias_factor = 1.3 # Makes predictions for majorities more likely to be positive

    y_pred_proba = np.zeros(num_samples)

    for i in range(num_samples):
        current_proba = base_proba + df.loc[i, 'Feature1'] * 0.05 - df.loc[i, 'Feature2'] * 0.02
        if df.loc[i, 'Race'] == 0: # Minority group
            current_proba *= minority_bias_factor
        else: # Majority group
            current_proba *= majority_bias_factor
        y_pred_proba[i] = np.clip(current_proba + np.random.normal(0, 0.1), 0.01, 0.99) # Add noise and clip

    df['y_pred_proba'] = y_pred_proba
    df['y_pred_biased'] = (df['y_pred_proba'] >= 0.5).astype(int)

    print("--- Original Biased Data & Predictions ---")
    print(df[['Race', 'y_true', 'y_pred_proba', 'y_pred_biased']].head())
    print(f"\nPredicted positive rate (Majority/Privileged): {df.loc[df['Race']==1, 'y_pred_biased'].mean():.2f}")
    print(f"Predicted positive rate (Minority/Unprivileged): {df.loc[df['Race']==0, 'y_pred_biased'].mean():.2f}")
    print("-" * 50)

    # Initialize BiasMitigator
    mitigator = BiasMitigator()
    sensitive_attr_name = 'Race'
    privileged_val = 1 # Majority
    unprivileged_val = 0 # Minority
    label_col = 'y_true'

    # Initialize FairnessAuditor for pre/post-mitigation comparison
    auditor = None
    if FAIRNESS_AUDITOR_AVAILABLE:
        auditor = FairnessAuditor(sensitive_attr_name, privileged_val, unprivileged_val)
        print("\n--- Initial Fairness Audit (Biased Model) ---")
        initial_audit_report = auditor.audit(df, label_col, 'y_pred_biased')
        print(json.dumps(initial_audit_report['metrics'], indent=4))
        auditor.plot_fairness_metrics(initial_audit_report, save_path="initial_fairness_metrics.png")
        print("-" * 50)
    else:
        print("\nSkipping fairness audit comparison as FairnessAuditor is not available.")

    # --- Mitigation Technique 1: Reweighing (Pre-processing) ---
    print("\n--- Applying Reweighing (Pre-processing) ---")
    # For Reweighing, we need the original features and labels for training
    X = df[['Feature1', 'Feature2']]
    y = df['y_true']

    sample_weights = mitigator.reweighing_pre_processing(
        df=df,
        sensitive_attribute_name=sensitive_attr_name,
        privileged_group_value=privileged_val,
        unprivileged_group_value=unprivileged_val,
        label_column=label_col
    )
    df['reweighing_weights'] = sample_weights
    print("Sample weights calculated:")
    print(df[['Race', 'y_true', 'reweighing_weights']].head())

    # Demonstrate reweighing by training a simple model with weights
    # In a real scenario, you'd integrate this with your hyper-aidev training pipeline.
    print("\nTraining a simple Logistic Regression with Reweighing weights...")
    model_reweighed = LogisticRegression(solver='liblinear', random_state=42, class_weight='balanced') # Use balanced for labels
    model_reweighed.fit(X, y, sample_weight=sample_weights)
    y_pred_reweighed_proba = model_reweighed.predict_proba(X)[:, 1]
    y_pred_reweighed = (y_pred_reweighed_proba >= 0.5).astype(int)
    df['y_pred_reweighed'] = y_pred_reweighed
    df['y_pred_reweighed_proba'] = y_pred_reweighed_proba

    if auditor:
        print("\n--- Fairness Audit (After Reweighing) ---")
        reweighed_audit_report = auditor.audit(df, label_col, 'y_pred_reweighed')
        print(json.dumps(reweighed_audit_report['metrics'], indent=4))
        auditor.plot_fairness_metrics(reweighed_audit_report, save_path="reweighed_fairness_metrics.png")
        print("-" * 50)
    else:
        print("\nSkipping fairness audit comparison for reweighed model.")


    # --- Mitigation Technique 2: Equalized Odds Post-Processing ---
    print("\n--- Applying Equalized Odds Post-Processing ---")
    y_pred_post_processed = mitigator.equalized_odds_post_processing(
        y_true=df['y_true'].values,
        y_pred_proba=df['y_pred_proba'].values,
        sensitive_attributes=df['Race'].values,
        privileged_group_value=privileged_val,
        unprivileged_group_value=unprivileged_val
    )
    df['y_pred_eq_odds'] = y_pred_post_processed

    if auditor:
        print("\n--- Fairness Audit (After Equalized Odds Post-Processing) ---")
        eq_odds_audit_report = auditor.audit(df, label_col, 'y_pred_eq_odds')
        print(json.dumps(eq_odds_audit_report['metrics'], indent=4))
        auditor.plot_fairness_metrics(eq_odds_audit_report, save_path="eq_odds_fairness_metrics.png")
        print("-" * 50)
    else:
        print("\nSkipping fairness audit comparison for Equalized Odds post-processed model.")

    # --- Mitigation Technique 3: Reject Option Classification (Post-processing) ---
    print("\n--- Applying Reject Option Classification (Post-processing) ---")
    y_pred_roc = mitigator.reject_option_classification_post_processing(
        y_true=df['y_true'].values,
        y_pred_proba=df['y_pred_proba'].values,
        sensitive_attributes=df['Race'].values,
        privileged_group_value=privileged_val,
        unprivileged_group_value=unprivileged_val,
        roc_threshold=0.05, # Max diff in positive rates to trigger reject
        threshold_range=(0.4, 0.6) # Confidence range around 0.5 to consider for rejection
    )
    df['y_pred_roc'] = y_pred_roc

    if auditor:
        print("\n--- Fairness Audit (After Reject Option Classification) ---")
        roc_audit_report = auditor.audit(df, label_col, 'y_pred_roc')
        print(json.dumps(roc_audit_report['metrics'], indent=4))
        auditor.plot_fairness_metrics(roc_audit_report, save_path="roc_fairness_metrics.png")
        print("-" * 50)
    else:
        print("\nSkipping fairness audit comparison for ROC post-processed model.")


    # Cleanup generated plot files
    if os.path.exists("initial_fairness_metrics.png"): os.remove("initial_fairness_metrics.png")
    if os.path.exists("reweighed_fairness_metrics.png"): os.remove("reweighed_fairness_metrics.png")
    if os.path.exists("eq_odds_fairness_metrics.png"): os.remove("eq_odds_fairness_metrics.png")
    if os.path.exists("roc_fairness_metrics.png"): os.remove("roc_fairness_metrics.png")
    print("\n--- py_ai_trust.mitigation testing complete ---")

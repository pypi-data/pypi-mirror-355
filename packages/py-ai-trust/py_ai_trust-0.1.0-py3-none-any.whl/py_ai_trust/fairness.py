import numpy as np
import pandas as pd
import logging
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Any, Union, Optional

# Set up basic logging for this module
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class FairnessAuditor:
    """
    A class to audit the fairness of a machine learning model's predictions.
    It calculates various fairness metrics, primarily for binary classification,
    across privileged and unprivileged groups defined by a sensitive attribute.
    """
    def __init__(self, sensitive_attribute_name: str, 
                 privileged_group_value: Any, 
                 unprivileged_group_value: Any):
        """
        Initializes the FairnessAuditor.

        Args:
            sensitive_attribute_name (str): The name of the column/feature representing the sensitive attribute.
            privileged_group_value (Any): The value in the sensitive attribute column that represents the privileged group.
            unprivileged_group_value (Any): The value in the sensitive attribute column that represents the unprivileged group.
        """
        self.sensitive_attribute_name = sensitive_attribute_name
        self.privileged_group_value = privileged_group_value
        self.unprivileged_group_value = unprivileged_group_value
        
        logger.info(f"FairnessAuditor initialized for sensitive attribute '{sensitive_attribute_name}'.")
        logger.info(f"  Privileged Group: '{privileged_group_value}'")
        logger.info(f"  Unprivileged Group: '{unprivileged_group_value}'")

    def _get_group_data(self, sensitive_attributes: np.ndarray, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, Dict[str, np.ndarray]]:
        """
        Internal helper to separate true labels and predictions by privileged and unprivileged groups.

        Args:
            sensitive_attributes (np.ndarray): Array of sensitive attribute values for each sample.
            y_true (np.ndarray): True labels for each sample (binary: 0 or 1).
            y_pred (np.ndarray): Predicted labels for each sample (binary: 0 or 1).

        Returns:
            Dict[str, Dict[str, np.ndarray]]: A dictionary containing 'privileged' and 'unprivileged'
                                              groups, each with 'y_true' and 'y_pred' arrays.
        """
        privileged_indices = sensitive_attributes == self.privileged_group_value
        unprivileged_indices = sensitive_attributes == self.unprivileged_group_value

        if not np.any(privileged_indices):
            logger.warning("No samples found for the privileged group. Fairness metrics might be undefined or inaccurate.")
        if not np.any(unprivileged_indices):
            logger.warning("No samples found for the unprivileged group. Fairness metrics might be undefined or inaccurate.")

        return {
            'privileged': {
                'y_true': y_true[privileged_indices],
                'y_pred': y_pred[privileged_indices]
            },
            'unprivileged': {
                'y_true': y_true[unprivileged_indices],
                'y_pred': y_pred[unprivileged_indices]
            }
        }

    def _calculate_base_rates(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """Calculates true positives, true negatives, false positives, false negatives."""
        if len(y_true) == 0:
            return {'TP': 0, 'TN': 0, 'FP': 0, 'FN': 0, 'total': 0, 'positive_rate': 0.0}

        TP = np.sum((y_pred == 1) & (y_true == 1))
        TN = np.sum((y_pred == 0) & (y_true == 0))
        FP = np.sum((y_pred == 1) & (y_true == 0))
        FN = np.sum((y_pred == 0) & (y_true == 1))
        
        total = len(y_true)
        positive_rate = np.sum(y_pred == 1) / total if total > 0 else 0.0 # P(Y_hat=1)

        # True Positive Rate (Recall) = TP / (TP + FN)
        TPR = TP / (TP + FN) if (TP + FN) > 0 else 0.0
        # False Positive Rate = FP / (FP + TN)
        FPR = FP / (FP + TN) if (FP + TN) > 0 else 0.0
        # True Negative Rate (Specificity) = TN / (TN + FP)
        TNR = TN / (TN + FP) if (TN + FP) > 0 else 0.0
        # False Negative Rate = FN / (FN + TP)
        FNR = FN / (FN + TP) if (FN + TP) > 0 else 0.0
        
        # Predictive Parity (Precision) = TP / (TP + FP)
        PPV = TP / (TP + FP) if (TP + FP) > 0 else 0.0

        return {
            'TP': int(TP), 'TN': int(TN), 'FP': int(FP), 'FN': int(FN),
            'total': int(total), 'positive_rate': float(positive_rate),
            'TPR': float(TPR), 'FPR': float(FPR), 'TNR': float(TNR), 'FNR': float(FNR),
            'PPV': float(PPV)
        }

    def _calculate_metrics(self, group_data: Dict[str, Dict[str, np.ndarray]]) -> Dict[str, float]:
        """
        Calculates various fairness metrics based on group data.
        Assumes binary classification (0/1 for y_true and y_pred).
        """
        metrics = {}

        priv_rates = self._calculate_base_rates(group_data['privileged']['y_true'], group_data['privileged']['y_pred'])
        unpriv_rates = self._calculate_base_rates(group_data['unprivileged']['y_true'], group_data['unprivileged']['y_pred'])

        # Check for sufficient group sizes before calculating ratios/differences
        if priv_rates['total'] == 0 or unpriv_rates['total'] == 0:
            logger.warning("One or both groups have no data. Cannot calculate fairness metrics.")
            return {
                "statistical_parity_difference": np.nan,
                "disparate_impact": np.nan,
                "equal_opportunity_difference": np.nan,
                "average_odds_difference": np.nan,
                "privileged_group_positive_rate": priv_rates['positive_rate'],
                "unprivileged_group_positive_rate": unpriv_rates['positive_rate'],
                "privileged_group_tpr": priv_rates['TPR'],
                "unprivileged_group_tpr": unpriv_rates['TPR'],
                "privileged_group_fpr": priv_rates['FPR'],
                "unprivileged_group_fpr": unpriv_rates['FPR'],
            }

        # 1. Statistical Parity Difference (SPD)
        # P(Y_hat=1 | unprivileged) - P(Y_hat=1 | privileged)
        # Ideally close to 0
        metrics['statistical_parity_difference'] = unpriv_rates['positive_rate'] - priv_rates['positive_rate']

        # 2. Disparate Impact (DI)
        # P(Y_hat=1 | unprivileged) / P(Y_hat=1 | privileged)
        # Ideally close to 1. Rule of thumb: between 0.8 and 1.25 (80% rule)
        metrics['disparate_impact'] = unpriv_rates['positive_rate'] / priv_rates['positive_rate'] if priv_rates['positive_rate'] > 0 else np.inf

        # 3. Equal Opportunity Difference (EOD)
        # TPR(unprivileged) - TPR(privileged)
        # Ideally close to 0. Measures if true positives are identified equally.
        metrics['equal_opportunity_difference'] = unpriv_rates['TPR'] - priv_rates['TPR']

        # 4. Average Odds Difference (AOD)
        # 0.5 * [(FPR(unprivileged) - FPR(privileged)) + (TPR(unprivileged) - TPR(privileged))]
        # Ideally close to 0. Measures parity in false positive rates and true positive rates.
        metrics['average_odds_difference'] = 0.5 * (
            (unpriv_rates['FPR'] - priv_rates['FPR']) +
            (unpriv_rates['TPR'] - priv_rates['TPR'])
        )
        
        # Include base rates for context
        metrics['privileged_group_positive_rate'] = priv_rates['positive_rate']
        metrics['unprivileged_group_positive_rate'] = unpriv_rates['positive_rate']
        metrics['privileged_group_tpr'] = priv_rates['TPR']
        metrics['unprivileged_group_tpr'] = unpriv_rates['TPR']
        metrics['privileged_group_fpr'] = priv_rates['FPR']
        metrics['unprivileged_group_fpr'] = priv_rates['FPR']

        return metrics

    def audit(self, 
              df: pd.DataFrame, 
              y_true_column: str, 
              y_pred_column: str) -> Dict[str, Any]:
        """
        Performs a fairness audit on the model's predictions.

        Args:
            df (pd.DataFrame): DataFrame containing sensitive attribute, true labels, and predictions.
            y_true_column (str): Name of the column with true labels (0 or 1).
            y_pred_column (str): Name of the column with predicted labels (0 or 1).

        Returns:
            Dict[str, Any]: A dictionary containing the fairness audit report.
        """
        logger.info(f"Starting fairness audit for columns '{y_true_column}', '{y_pred_column}' and sensitive attribute '{self.sensitive_attribute_name}'.")

        # Validate input columns
        for col in [self.sensitive_attribute_name, y_true_column, y_pred_column]:
            if col not in df.columns:
                logger.error(f"Required column '{col}' not found in the DataFrame.")
                return {"status": "Error", "message": f"Column '{col}' missing from DataFrame."}
        
        # Ensure data types are numeric for y_true and y_pred
        try:
            y_true_np = df[y_true_column].astype(int).values
            y_pred_np = df[y_pred_column].astype(int).values
            sensitive_attrs_np = df[self.sensitive_attribute_name].values
        except ValueError as e:
            logger.error(f"Error converting true/predicted labels to integers: {e}. Ensure they are binary (0/1).")
            return {"status": "Error", "message": "True/predicted labels must be convertible to integers (0/1)."}

        if not np.all(np.isin(y_true_np, [0, 1])) or not np.all(np.isin(y_pred_np, [0, 1])):
            logger.warning("True or predicted labels contain values other than 0 or 1. Metrics assume binary classification.")

        group_data = self._get_group_data(sensitive_attrs_np, y_true_np, y_pred_np)
        fairness_metrics = self._calculate_metrics(group_data)

        report = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "sensitive_attribute": self.sensitive_attribute_name,
            "privileged_group": self.privileged_group_value,
            "unprivileged_group": self.unprivileged_group_value,
            "group_sizes": {
                "privileged_total": group_data['privileged']['y_true'].shape[0],
                "unprivileged_total": group_data['unprivileged']['y_true'].shape[0]
            },
            "metrics": fairness_metrics,
            "recommendations": self._interpret_metrics(fairness_metrics)
        }
        
        logger.info("Fairness audit complete.")
        return report

    def _interpret_metrics(self, metrics: Dict[str, float]) -> List[str]:
        """Provides basic recommendations based on calculated fairness metrics."""
        recommendations = []
        
        # Define thresholds for "significant" difference (these are common rules of thumb)
        disparate_impact_lower_bound = 0.8
        disparate_impact_upper_bound = 1.25
        difference_threshold = 0.1 # For SPD, EOD, AOD: absolute difference greater than this

        if 'statistical_parity_difference' in metrics and not np.isnan(metrics['statistical_parity_difference']):
            spd = metrics['statistical_parity_difference']
            if abs(spd) > difference_threshold:
                recommendations.append(f"Statistical Parity Difference ({spd:.3f}) is high. This suggests a notable difference in the positive prediction rate between groups.")
                if spd > 0:
                    recommendations.append(f"  The unprivileged group ({self.unprivileged_group_value}) is predicted positive more often than the privileged group ({self.privileged_group_value}).")
                else:
                    recommendations.append(f"  The privileged group ({self.privileged_group_value}) is predicted positive more often than the unprivileged group ({self.unprivileged_group_value}).")
        
        if 'disparate_impact' in metrics and not np.isnan(metrics['disparate_impact']):
            di = metrics['disparate_impact']
            if not (disparate_impact_lower_bound <= di <= disparate_impact_upper_bound):
                recommendations.append(f"Disparate Impact ({di:.3f}) violates the 80% rule. This indicates potential discriminatory impact.")
                if di < disparate_impact_lower_bound:
                    recommendations.append(f"  The unprivileged group ({self.unprivileged_group_value}) is receiving favorable outcomes less than {disparate_impact_lower_bound*100}% of the rate of the privileged group.")
                else:
                    recommendations.append(f"  The unprivileged group ({self.unprivileged_group_value}) is receiving favorable outcomes more than {disparate_impact_upper_bound*100}% of the rate of the privileged group.")

        if 'equal_opportunity_difference' in metrics and not np.isnan(metrics['equal_opportunity_difference']):
            eod = metrics['equal_opportunity_difference']
            if abs(eod) > difference_threshold:
                recommendations.append(f"Equal Opportunity Difference ({eod:.3f}) is high. The model's True Positive Rate differs significantly between groups.")
                if eod > 0:
                    recommendations.append(f"  The unprivileged group ({self.unprivileged_group_value}) has a higher True Positive Rate (better recall for positive class) than the privileged group.")
                else:
                    recommendations.append(f"  The privileged group ({self.privileged_group_value}) has a higher True Positive Rate than the unprivileged group.")

        if 'average_odds_difference' in metrics and not np.isnan(metrics['average_odds_difference']):
            aod = metrics['average_odds_difference']
            if abs(aod) > difference_threshold:
                recommendations.append(f"Average Odds Difference ({aod:.3f}) is high. This indicates disparities in both False Positive Rate and True Positive Rate across groups.")
                if aod > 0:
                    recommendations.append(f"  There's a general trend of higher errors (FP/FN) for the unprivileged group relative to the privileged group.")
                else:
                    recommendations.append(f"  There's a general trend of higher errors (FP/FN) for the privileged group relative to the unprivileged group.")

        if not recommendations:
            recommendations.append("No significant fairness issues detected based on standard thresholds. Model appears fair by these metrics.")
        
        recommendations.append("Consider reviewing the context and impact of these differences on real-world outcomes.")
        recommendations.append("Explore bias mitigation techniques if significant issues are identified.")

        return recommendations


    def plot_fairness_metrics(self, audit_report: Dict[str, Any], save_path: Optional[str] = None) -> None:
        """
        Plots a bar chart of the key fairness metrics from an audit report.

        Args:
            audit_report (Dict[str, Any]): The report generated by the `audit` method.
            save_path (Optional[str]): Path to save the plot (e.g., "fairness_metrics.png").
                                      If None, the plot is displayed.
        """
        if audit_report.get("status") == "Error" or not audit_report.get("metrics"):
            logger.error("Invalid audit report provided. Cannot plot fairness metrics.")
            return

        metrics = audit_report['metrics']
        
        # Filter metrics to plot for clarity, focusing on differences
        plot_metrics = {
            "Statistical Parity Difference": metrics.get('statistical_parity_difference'),
            "Equal Opportunity Difference": metrics.get('equal_opportunity_difference'),
            "Average Odds Difference": metrics.get('average_odds_difference'),
            "Disparate Impact (Ratio)": metrics.get('disparate_impact'),
        }
        
        # Remove NaN values from plotting
        plot_metrics = {k: v for k, v in plot_metrics.items() if not np.isnan(v)}

        if not plot_metrics:
            logger.warning("No valid fairness metrics to plot from the audit report.")
            return

        metric_names = list(plot_metrics.keys())
        metric_values = list(plot_metrics.values())

        plt.figure(figsize=(10, 6))
        sns.barplot(x=metric_names, y=metric_values, palette='viridis')
        plt.ylabel("Metric Value")
        plt.title(f"Fairness Metrics for {audit_report['sensitive_attribute']} ({audit_report['privileged_group']} vs {audit_report['unprivileged_group']})")
        plt.xticks(rotation=30, ha='right')
        plt.axhline(0, color='gray', linestyle='--', linewidth=0.8) # Reference line for differences

        # Add interpretation for Disparate Impact around 1
        if "Disparate Impact (Ratio)" in metric_names:
            di_idx = metric_names.index("Disparate Impact (Ratio)")
            if metric_values[di_idx] is not None and not np.isinf(metric_values[di_idx]):
                plt.axhline(0.8, color='red', linestyle=':', linewidth=0.7, label='80% Rule (Lower Bound)')
                plt.axhline(1.25, color='red', linestyle=':', linewidth=0.7, label='80% Rule (Upper Bound)')
                plt.legend()
        
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path)
            logger.info(f"Fairness metrics plot saved to '{save_path}'.")
        plt.show()


# --- Example Usage ---
if __name__ == "__main__":
    print("--- Testing py_ai_trust.fairness ---")

    # Set a random seed for reproducibility in dummy data generation
    np.random.seed(42)

    # Create dummy data for a binary classification task
    # Sensitive attribute: 'Gender' (0 for female, 1 for male - assuming male is privileged for this example)
    # y_true: true labels (0 for loan rejected, 1 for loan approved)
    # y_pred: model predictions (0 for loan rejected, 1 for loan approved)
    
    num_samples = 1000
    data = {
        'Gender': np.random.choice([0, 1], size=num_samples, p=[0.5, 0.5]), # 0: Female (Unprivileged), 1: Male (Privileged)
        'y_true': np.random.choice([0, 1], size=num_samples, p=[0.6, 0.4]), # Overall 40% approval rate
        'y_pred': np.zeros(num_samples) # Initialize predictions
    }
    df = pd.DataFrame(data)

    # Simulate a biased model:
    # 1. Privileged group (Gender=1, Male) has a higher positive prediction rate
    #    E.g., 60% approval rate for privileged group
    male_indices = df['Gender'] == 1
    df.loc[male_indices, 'y_pred'] = np.random.choice([0, 1], size=np.sum(male_indices), p=[0.4, 0.6])

    # 2. Unprivileged group (Gender=0, Female) has a lower positive prediction rate
    #    E.g., 30% approval rate for unprivileged group
    female_indices = df['Gender'] == 0
    df.loc[female_indices, 'y_pred'] = np.random.choice([0, 1], size=np.sum(female_indices), p=[0.7, 0.3])

    print("Dummy DataFrame created (simulating bias):")
    print(df.head())
    print(f"\nOverall predicted positive rate: {df['y_pred'].mean():.2f}")
    print(f"Predicted positive rate for privileged (Male, 1): {df.loc[df['Gender']==1, 'y_pred'].mean():.2f}")
    print(f"Predicted positive rate for unprivileged (Female, 0): {df.loc[df['Gender']==0, 'y_pred'].mean():.2f}")
    print("-" * 50)

    # Initialize FairnessAuditor
    auditor = FairnessAuditor(
        sensitive_attribute_name='Gender',
        privileged_group_value=1,   # Male
        unprivileged_group_value=0  # Female
    )

    # Perform the fairness audit
    audit_report = auditor.audit(
        df=df,
        y_true_column='y_true',
        y_pred_column='y_pred'
    )

    print("\nFairness Audit Report:")
    print(json.dumps(audit_report, indent=4))
    print("-" * 50)

    # Plot the fairness metrics
    plot_save_path = "fairness_metrics_report.png"
    auditor.plot_fairness_metrics(audit_report, save_path=plot_save_path)
    print(f"\nFairness metrics plot saved to '{plot_save_path}'.")

    # --- Test Case 2: No bias (or less bias) ---
    print("\n--- Testing py_ai_trust.fairness (Less Biased Scenario) ---")
    df_fair = pd.DataFrame(data) # Start with original data structure
    # Simulate a less biased model (e.g., both groups have ~40% approval rate)
    df_fair['y_pred'] = np.random.choice([0, 1], size=num_samples, p=[0.6, 0.4])

    audit_report_fair = auditor.audit(
        df=df_fair,
        y_true_column='y_true',
        y_pred_column='y_pred'
    )
    print("\nFairness Audit Report (Less Biased Scenario):")
    print(json.dumps(audit_report_fair, indent=4))
    auditor.plot_fairness_metrics(audit_report_fair, save_path="fairness_metrics_report_fair.png")
    print(f"\nLess biased fairness metrics plot saved to 'fairness_metrics_report_fair.png'.")

    # Cleanup
    if os.path.exists(plot_save_path): os.remove(plot_save_path)
    if os.path.exists("fairness_metrics_report_fair.png"): os.remove("fairness_metrics_report_fair.png")
    print("\n--- py_ai_trust.fairness testing complete ---")

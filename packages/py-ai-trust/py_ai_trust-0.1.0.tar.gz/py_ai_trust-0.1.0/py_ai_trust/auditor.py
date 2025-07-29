import numpy as np
import pandas as pd
import logging
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Union, Optional, Callable
from sklearn.base import BaseEstimator, ClassifierMixin, RegressorMixin
from sklearn.model_selection import train_test_split # For internal data splitting if needed

# Import the specialized auditors and enhancers
try:
    from py_ai_trust.fairness import FairnessAuditor
    from py_ai_trust.robustness import RobustnessTester
    from py_ai_trust.privacy import PrivacyAuditor
    from py_ai_trust.explainability import ExplainabilityEnhancer
    ALL_DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    logging.error(f"Failed to import core py_ai_trust modules: {e}. Some audit features may be unavailable.")
    ALL_DEPENDENCIES_AVAILABLE = False


# Set up basic logging for this module
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class TrustAuditor:
    """
    An orchestrator class for conducting comprehensive trustworthiness audits of
    machine learning models. It integrates tools for fairness, robustness, privacy,
    and explainability from the py-ai-trust library.
    """
    def __init__(self, output_dir: str = "./trust_audit_reports"):
        """
        Initializes the TrustAuditor.

        Args:
            output_dir (str): Directory where audit reports and plots will be saved.
        """
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.fairness_auditor: Optional[FairnessAuditor] = None
        self.robustness_tester = RobustnessTester()
        self.privacy_auditor = PrivacyAuditor()
        self.explainability_enhancer = ExplainabilityEnhancer()

        self.audit_results: Dict[str, Any] = {}
        logger.info(f"TrustAuditor initialized. Reports will be saved to '{self.output_dir}'.")

    def conduct_full_audit(self,
                           model: BaseEstimator,
                           X: Union[np.ndarray, pd.DataFrame],
                           y_true: np.ndarray,
                           sensitive_attribute_name: Optional[str] = None,
                           privileged_group_value: Optional[Any] = None,
                           unprivileged_group_value: Optional[Any] = None,
                           test_size: float = 0.3,
                           random_state: int = 42,
                           run_fairness_audit: bool = True,
                           run_robustness_audit: bool = True,
                           run_privacy_audit: bool = True,
                           run_explainability_audit: bool = True,
                           save_plots: bool = True) -> Dict[str, Any]:
        """
        Conducts a full trustworthiness audit of the given model.

        Args:
            model (BaseEstimator): The trained machine learning model to audit.
            X (Union[np.ndarray, pd.DataFrame]): Input features for the model.
            y_true (np.ndarray): True labels or regression targets corresponding to X.
            sensitive_attribute_name (Optional[str]): Name of the sensitive column for fairness.
            privileged_group_value (Optional[Any]): Value of the privileged group.
            unprivileged_group_value (Optional[Any]): Value of the unprivileged group.
            test_size (float): Proportion of data to use as test set for evaluation.
            random_state (int): Random seed for reproducibility of splits and sampling.
            run_fairness_audit (bool): Whether to run the fairness audit.
            run_robustness_audit (bool): Whether to run the robustness audit.
            run_privacy_audit (bool): Whether to run the privacy audit.
            run_explainability_audit (bool): Whether to run the explainability audit.
            save_plots (bool): Whether to save generated plots to the output directory.

        Returns:
            Dict[str, Any]: A comprehensive audit report.
        """
        if not ALL_DEPENDENCIES_AVAILABLE:
            logger.error("Cannot run full audit: Core py_ai_trust modules are not available.")
            return {"status": "Error", "message": "Missing dependencies for full audit."}

        logger.info("Starting comprehensive AI trustworthiness audit...")
        self.audit_results = {
            "timestamp": datetime.now().isoformat(),
            "model_type": str(type(model).__name__),
            "audit_sections": {}
        }

        # --- Data Preparation for Audit ---
        # Ensure X is a DataFrame for consistent column handling
        if not isinstance(X, pd.DataFrame):
            X_df = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(X.shape[1])])
            logger.info("Converted X to DataFrame with generic feature names.")
        else:
            X_df = X.copy() # Work on a copy

        # Split data for robust testing (especially for privacy/robustness)
        # We need a separate test set to evaluate model performance under attack/noise
        # and also a "training" set for MIA, so we simulate train/test split from X, y_true
        X_train_sim, X_test_sim, y_train_sim, y_test_sim = train_test_split(
            X_df, y_true, test_size=test_size, random_state=random_state
        )
        
        # Ensure the model is fitted (cannot directly check from BaseEstimator)
        # Attempt to predict to see if it's fitted.
        try:
            model.predict(X_test_sim.iloc[:1] if isinstance(X_test_sim, pd.DataFrame) else X_test_sim[:1])
        except Exception as e:
            logger.warning(f"Model might not be fitted. Prediction failed: {e}. Ensure the model is trained before auditing.")
            # We'll proceed, but performance metrics might be unreliable

        # Get initial predictions
        y_pred_test_sim = model.predict(X_test_sim)
        y_pred_proba_test_sim = None
        if hasattr(model, 'predict_proba'):
            y_pred_proba_test_sim = model.predict_proba(X_test_sim)[:, 1] # Assuming binary for simplicity in many metrics

        # --- 1. Fairness Audit ---
        if run_fairness_audit and sensitive_attribute_name and privileged_group_value is not None and unprivileged_group_value is not None:
            logger.info("\n--- Running Fairness Audit ---")
            # Combine X_test_sim, y_test_sim, y_pred_test_sim, sensitive_attributes into a single DataFrame
            audit_df_fairness = X_test_sim.copy()
            audit_df_fairness['y_true'] = y_test_sim
            audit_df_fairness['y_pred'] = y_pred_test_sim

            self.fairness_auditor = FairnessAuditor(
                sensitive_attribute_name=sensitive_attribute_name,
                privileged_group_value=privileged_group_value,
                unprivileged_group_value=unprivileged_group_value
            )
            fairness_report = self.fairness_auditor.audit(
                df=audit_df_fairness,
                y_true_column='y_true',
                y_pred_column='y_pred'
            )
            self.audit_results['audit_sections']['fairness'] = fairness_report
            if save_plots and fairness_report['status'] == 'success':
                self.fairness_auditor.plot_fairness_metrics(fairness_report, os.path.join(self.output_dir, "fairness_metrics.png"))
        elif run_fairness_audit:
            logger.warning("Skipping fairness audit: Sensitive attribute or group values not provided.")

        # --- 2. Robustness Audit ---
        if run_robustness_audit:
            logger.info("\n--- Running Robustness Audit ---")
            robustness_results = {}

            # Robustness to noise
            noise_results = self.robustness_tester.evaluate_robustness_to_noise(
                model=model, X=X_test_sim, y_true=y_test_sim, noise_level=0.1, noise_type='gaussian', random_state=random_state
            )
            robustness_results['gaussian_noise'] = noise_results

            # Conceptual Adversarial Robustness
            if isinstance(model, ClassifierMixin): # Only for classifiers
                adversarial_results = self.robustness_tester.evaluate_adversarial_robustness(
                    model=model, X_original=X_test_sim, y_true=y_test_sim, epsilon=0.5, random_state=random_state
                )
                robustness_results['conceptual_adversarial'] = adversarial_results
            else:
                logger.info("Skipping adversarial robustness: Model is not a classifier.")

            # Data Corruption
            missing_val_corrupted_X = self.robustness_tester.apply_data_corruption(
                X=X_test_sim, corruption_level=0.05, corruption_type='missing_values', random_state=random_state
            )
            # Need to impute missing values before prediction. Using a simple mean imputer.
            from sklearn.impute import SimpleImputer
            imputer = SimpleImputer(strategy='mean')
            # Fit imputer on training data and transform corrupted test data
            imputer.fit(X_train_sim)
            missing_val_corrupted_X_imputed = imputer.transform(missing_val_corrupted_X)
            
            y_pred_missing_corrupted = model.predict(missing_val_corrupted_X_imputed)
            missing_accuracy = accuracy_score(y_test_sim, y_pred_missing_corrupted)
            robustness_results['missing_values_corruption'] = {"accuracy": missing_accuracy, "accuracy_drop": noise_results['original_performance']['score'] - missing_accuracy}

            self.audit_results['audit_sections']['robustness'] = robustness_results
        
        # --- 3. Privacy Audit ---
        if run_privacy_audit and isinstance(model, ClassifierMixin) and hasattr(model, 'predict_proba'):
            logger.info("\n--- Running Privacy Audit ---")
            privacy_results = {}
            # Membership Inference Attack (requires train and test data for comparison)
            mia_report = self.privacy_auditor.conduct_membership_inference_attack(
                model=model,
                X_train=X_train_sim, y_train=y_train_sim,
                X_test=X_test_sim, y_test=y_test_sim,
                confidence_threshold=0.9,
                random_state=random_state
            )
            privacy_results['membership_inference_attack'] = mia_report

            # Feature Leakage Detection (uses full data for correlation)
            df_for_leakage = X_df.copy()
            df_for_leakage['target_label'] = y_true # Add true labels for leakage detection
            leakage_report = self.privacy_auditor.detect_feature_leakage(
                df=df_for_leakage,
                target_column='target_label',
                correlation_threshold=0.8
            )
            privacy_results['feature_leakage_detection'] = leakage_report

            self.audit_results['audit_sections']['privacy'] = privacy_results
        elif run_privacy_audit:
            logger.warning("Skipping privacy audit: Model is not a classifier or does not support predict_proba.")

        # --- 4. Explainability Audit ---
        if run_explainability_audit:
            logger.info("\n--- Running Explainability Audit ---")
            explainability_results = {}

            # Permutation Importance
            permutation_importance_scores = self.explainability_enhancer.calculate_permutation_importance(
                model=model, X=X_test_sim, y=y_test_sim, scoring='accuracy', n_repeats=5, random_state=random_state
            )
            explainability_results['permutation_importance'] = permutation_importance_scores
            if save_plots:
                self.explainability_enhancer.plot_permutation_importance(permutation_importance_scores, os.path.join(self.output_dir, "permutation_importance.png"))
            
            # Partial Dependence Plots (for top 2-3 features or selected ones)
            # Find top 3 features by permutation importance for PDPs
            top_features = list(permutation_importance_scores.keys())[:3] if permutation_importance_scores else []
            if top_features:
                self.explainability_enhancer.plot_partial_dependence(
                    model=model,
                    X=X_test_sim,
                    features_to_plot=top_features,
                    feature_names=X_test_sim.columns.tolist() if isinstance(X_test_sim, pd.DataFrame) else None,
                    title="Partial Dependence Plots (Top Features)",
                    save_path=os.path.join(self.output_dir, "pdp_top_features.png")
                )
            
            # Individual Conditional Expectation (ICE) Plot for a single top feature
            if top_features:
                self.explainability_enhancer.plot_individual_conditional_expectation(
                    model=model,
                    X=X_test_sim,
                    feature_index_or_name=top_features[0],
                    feature_names=X_test_sim.columns.tolist() if isinstance(X_test_sim, pd.DataFrame) else None,
                    title=f"ICE Plot for {top_features[0]}",
                    save_path=os.path.join(self.output_dir, f"ice_plot_{top_features[0]}.png")
                )
            else:
                logger.warning("No features to plot for explainability (PDP/ICE).")

            self.audit_results['audit_sections']['explainability'] = explainability_results

        logger.info("Comprehensive AI trustworthiness audit complete.")
        return self.audit_results

    def generate_report_summary(self, audit_report: Dict[str, Any]) -> str:
        """
        Generates a human-readable summary of the comprehensive audit report.

        Args:
            audit_report (Dict[str, Any]): The full audit report from `conduct_full_audit`.

        Returns:
            str: A Markdown-formatted summary string.
        """
        if not audit_report or audit_report.get("status") == "Error":
            return "## AI Trustworthiness Audit Summary\n\nAudit could not be completed or report is empty."

        summary_md = f"# AI Trustworthiness Audit Report\n\n"
        summary_md += f"**Audit Date:** {audit_report['timestamp']}\n"
        summary_md += f"**Model Type:** {audit_report['model_type']}\n\n"
        summary_md += f"**Output Directory:** `{self.output_dir}` (for detailed logs and plots)\n\n"
        summary_md += "---\n\n"

        # Fairness Section
        if 'fairness' in audit_report['audit_sections']:
            fairness_data = audit_report['audit_sections']['fairness']
            summary_md += "## ⚖️ Fairness Audit\n\n"
            if fairness_data['status'] == 'Error':
                summary_md += f"**Status:** Error - {fairness_data['message']}\n\n"
            else:
                summary_md += f"**Sensitive Attribute:** `{fairness_data['sensitive_attribute']}`\n"
                summary_md += f"**Privileged Group:** `{fairness_data['privileged_group']}` (N={fairness_data['group_sizes']['privileged_total']})\n"
                summary_md += f"**Unprivileged Group:** `{fairness_data['unprivileged_group']}` (N={fairness_data['group_sizes']['unprivileged_total']})\n\n"
                summary_md += "**Key Metrics:**\n"
                for metric, value in fairness_data['metrics'].items():
                    if "group_positive_rate" not in metric and "group_tpr" not in metric and "group_fpr" not in metric: # Avoid showing raw rates again
                        summary_md += f"* {metric.replace('_', ' ').title()}: `{value:.4f}`\n"
                summary_md += "\n**Recommendations/Findings:**\n"
                for rec in fairness_data['recommendations']:
                    summary_md += f"* {rec}\n"
                summary_md += "\n(See `fairness_metrics.png` for plot.)\n\n"
        
        # Robustness Section
        if 'robustness' in audit_report['audit_sections']:
            robustness_data = audit_report['audit_sections']['robustness']
            summary_md += "## 💪 Robustness Audit\n\n"
            summary_md += "**Performance Under Perturbation:**\n"
            for test_name, results in robustness_data.items():
                original_score = results.get('original_performance', {}).get('score', 'N/A') if 'original_performance' in results else results.get('original_accuracy', 'N/A')
                perturbed_score = results.get('noisy_performance', {}).get('score', 'N/A') if 'noisy_performance' in results else results.get('adversarial_accuracy', 'N/A')
                drop = results.get('performance_drop', results.get('accuracy_drop', 'N/A'))
                metric_name = results.get('original_performance', {}).get('metric', 'Accuracy') if 'original_performance' in results else 'Accuracy' # Heuristic
                
                summary_md += f"* **{test_name.replace('_', ' ').title()}:**\n"
                summary_md += f"  - Original {metric_name}: `{original_score:.4f}`\n"
                summary_md += f"  - Perturbed {metric_name}: `{perturbed_score:.4f}`\n"
                summary_md += f"  - Performance Drop: `{drop:.4f}`\n"
                if drop > 0.1: # Example threshold for warning
                    summary_md += "  - _Finding:_ Model shows significant performance degradation under this perturbation. Investigation recommended.\n"
            summary_md += "\n"

        # Privacy Section
        if 'privacy' in audit_report['audit_sections']:
            privacy_data = audit_report['audit_sections']['privacy']
            summary_md += "## 🔒 Privacy Audit\n\n"
            if 'membership_inference_attack' in privacy_data:
                mia = privacy_data['membership_inference_attack']
                summary_md += "**Membership Inference Attack (MIA):**\n"
                summary_md += f"* Inference Accuracy: `{mia['inference_accuracy']:.4f}` (higher indicates more leakage)\n"
                summary_md += f"* Avg Train Confidence: `{mia['avg_train_confidence']:.4f}`\n"
                summary_md += f"* Avg Test Confidence: `{mia['avg_test_confidence']:.4f}`\n"
                summary_md += "* Findings:\n"
                for rec in mia['recommendations']:
                    summary_md += f"  * {rec}\n"
                summary_md += "\n"
            if 'feature_leakage_detection' in privacy_data:
                leakage = privacy_data['feature_leakage_detection']
                summary_md += "**Feature Leakage Detection:**\n"
                summary_md += f"* Summary: {leakage['summary']}\n"
                if leakage['potential_leakage_features']:
                    summary_md += "* Potential Leaking Features:\n"
                    for f in leakage['potential_leakage_features']:
                        summary_md += f"  * `{f['feature']}` (Correlation with target: `{f['target_correlation']:.4f}`): {f['recommendation']}\n"
                summary_md += "\n"

        # Explainability Section
        if 'explainability' in audit_report['audit_sections']:
            explain_data = audit_report['audit_sections']['explainability']
            summary_md += "## 💡 Explainability Audit\n\n"
            if 'permutation_importance' in explain_data and explain_data['permutation_importance']:
                summary_md += "**Top Permutation Importances:**\n"
                # Display top 5 features
                top_5_features = list(explain_data['permutation_importance'].items())[:5]
                for feature, score in top_5_features:
                    summary_md += f"* `{feature}`: `{score:.4f}`\n"
                summary_md += "\n(See `permutation_importance.png` for plot.)\n"
                summary_md += "(See `pdp_top_features.png` for Partial Dependence Plots of top features.)\n"
                summary_md += "(See `ice_plot_F0.png` (or similar) for Individual Conditional Expectation Plots.)\n"
            else:
                summary_md += "No permutation importance data or plots generated.\n"
            summary_md += "\n"

        summary_md += "---\n\n"
        summary_md += "This report provides a high-level overview. For detailed metrics, raw data, and all generated plots, please refer to the files in the output directory."

        logger.info("Audit report summary generated.")
        return summary_md

# --- Example Usage ---
if __name__ == "__main__":
    print("--- Testing py_ai_trust.auditor ---")

    np.random.seed(42)

    # --- Setup: Dummy Classifier Model and Data ---
    # We will simulate a scenario where 'Gender' might be a sensitive attribute
    # And there might be some bias.
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.datasets import make_classification
    
    num_samples = 1500
    n_features = 10
    n_informative = 5

    # Create synthetic data with a 'Gender' sensitive attribute
    # Feature 0 will be correlated with Gender and influence the target
    X_synthetic, y_synthetic = make_classification(n_samples=num_samples, n_features=n_features, n_informative=n_informative,
                                                    n_redundant=0, n_clusters_per_class=1, random_state=42, flip_y=0.05)
    
    # Introduce a 'Gender' feature (binary: 0 for Female, 1 for Male)
    # Let's say Female (0) is the unprivileged group.
    gender = np.random.choice([0, 1], size=num_samples, p=[0.5, 0.5]) # 50/50 split
    
    # Simulate correlation: make a specific feature (e.g., X_synthetic[:, 0]) correlate with gender
    # and also with the outcome, which might introduce bias.
    # For example, if gender 0 (female) often has lower values in X_synthetic[:,0]
    # and lower values in X_synthetic[:,0] lead to negative outcome.
    
    # To simulate bias:
    # Let X_synthetic[:, 0] be a proxy for 'credit score'.
    # Make 'credit score' generally lower for the unprivileged group (Gender 0).
    X_synthetic[gender == 0, 0] = np.random.uniform(0, 5, size=np.sum(gender == 0)) # Lower range for unprivileged
    X_synthetic[gender == 1, 0] = np.random.uniform(3, 10, size=np.sum(gender == 1)) # Higher range for privileged

    # Combine into a DataFrame to add 'Gender' column easily
    feature_names = [f'F{i}' for i in range(n_features)]
    X_df = pd.DataFrame(X_synthetic, columns=feature_names)
    X_df['Gender'] = gender
    
    # Split data for training the model and for auditing
    # The auditor will perform its own test_train_split on the passed X,y for its internal tests.
    X_train_model, X_test_model, y_train_model, y_test_model = train_test_split(
        X_df.drop('Gender', axis=1), y_synthetic, test_size=0.2, random_state=42
    )

    # Train a RandomForestClassifier on features only (not gender directly)
    model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X_train_model, y_train_model)
    
    y_pred_model = model.predict(X_test_model)
    test_accuracy = accuracy_score(y_test_model, y_pred_model)
    print(f"Model trained. Test Accuracy: {test_accuracy:.4f}")
    print("-" * 50)

    # --- Initialize and Run TrustAuditor ---
    auditor = TrustAuditor(output_dir="./py_ai_trust_audit_report")
    
    # Pass the full X_df (including sensitive attribute for fairness analysis) and y_synthetic
    # The auditor will internally split this into X_test_sim and y_test_sim
    full_audit_report = auditor.conduct_full_audit(
        model=model,
        X=X_df, # Pass the DataFrame including the sensitive attribute
        y_true=y_synthetic,
        sensitive_attribute_name='Gender',
        privileged_group_value=1, # Male
        unprivileged_group_value=0, # Female
        test_size=0.3, # Use 30% of input data for internal audit-specific tests
        random_state=42,
        run_fairness_audit=True,
        run_robustness_audit=True,
        run_privacy_audit=True,
        run_explainability_audit=True,
        save_plots=True
    )

    # Generate and print the summary report
    summary = auditor.generate_report_summary(full_audit_report)
    print("\n" + "="*70)
    print("COMPREHENSIVE AI TRUSTWORTHINESS AUDIT SUMMARY")
    print("="*70)
    print(summary)
    print("="*70 + "\n")

    # Save the full JSON report
    report_json_path = os.path.join(auditor.output_dir, "full_audit_report.json")
    with open(report_json_path, "w", encoding="utf-8") as f:
        json.dump(full_audit_report, f, indent=4)
    print(f"Full audit report (JSON) saved to '{report_json_path}'.")

    # --- Cleanup ---
    print("\n--- Cleaning up temporary files and directories ---")
    if os.path.exists("./py_ai_trust_audit_report"):
        import shutil
        shutil.rmtree("./py_ai_trust_audit_report")
        print("Removed './py_ai_trust_audit_report' directory.")
    print("\n--- py_ai_trust.auditor testing complete ---")

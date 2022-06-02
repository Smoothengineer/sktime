# -*- coding: utf-8 -*-
"""Evaluator for clustering experiments."""
import ast
from typing import Dict, List, Tuple

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    adjusted_mutual_info_score,
    adjusted_rand_score,
    mutual_info_score,
    normalized_mutual_info_score,
    rand_score,
)

from sktime.benchmarking.evaluation.base import BaseEstimatorEvaluator
from sktime.datasets import read_clusterer_result_from_uea_format

_evaluation_metrics_dict = {
    "RI": rand_score,  # Rand index
    "ARI": adjusted_rand_score,  # Adjusted rand index
    "MI": mutual_info_score,  # Mutual information
    "NMI": normalized_mutual_info_score,  # Normalized mutual information
    "AMI": adjusted_mutual_info_score,  # Adjusted mutual information
    # "FM": fowlkes_mallows_score,  # Fowlkes-Mallows
    # "SC": some_callable,  # Silhouette Coefficient
    # "CHI": calinski_harabasz_score,  # Calinski-Harabasz Index
    "ACC": accuracy_score,  # Accuracy
    # "PCM": confusion_matrix,  # Pair confusion matrix
}


class ClusterEvaluator(BaseEstimatorEvaluator):
    """Evaluator for clustering experiments.

    Parameters
    ----------
    results_path: str
        The path to the csv results generated by the estimators.
    evaluation_out_path: str
        The path to output the results of the evaluation
    experiment_name: str
        The name of the experiment (the directory that stores the results will be called
        this).
    metrics: List[str], defaults = None
        List of metrics to evaluate over.
    naming_parameter_key: str, defaults = None
        The key from the dict defining the parameters of the experiments (first line of
        csv file).
    draw_critical_difference_diagrams: bool, defaults = True
        Boolean that when true will also output critical difference diagrams. When
        False no diagrams will be outputted.
    critical_diff_params: dict, defaults = None
        Parameters for critical difference call. See create_critical_difference_diagram
        method for list of valid parameters.
    """

    def __init__(
        self,
        results_path: str,
        evaluation_out_path: str,
        experiment_name: str,
        metrics: List[str] = None,
        naming_parameter_key: str = None,
        draw_critical_difference_diagrams: bool = True,
        critical_diff_params: dict = None,
    ):

        if metrics is None:
            metrics = ["RI", "ARI", "MI", "NMI", "AMI", "ACC"]
        for metric in metrics:
            if metric not in _evaluation_metrics_dict:
                raise ValueError(
                    f"The metric: {metric} is invalid please check the "
                    f"list of available metrics to use."
                )
        self.metrics = metrics
        self.naming_parameter_key = naming_parameter_key
        super(ClusterEvaluator, self).__init__(
            results_path,
            evaluation_out_path,
            experiment_name,
            draw_critical_difference_diagrams=draw_critical_difference_diagrams,
            critical_diff_params=critical_diff_params,
        )

    def evaluate_csv_data(self, csv_path: str) -> Tuple:
        """Evaluate results from csv file.

        Parameters
        ----------
        csv_path: str
            Path to csv containing the results to analyse.

        Returns
        -------
        dataset: str
            Dataset for the experiment.
        estimator_name: str
            Estimator name.
        experiment_name: str
            Name for experiment (maybe the same as the estimator name).
        metric_scores: dict
            Dict where the key is the metric and the value is the score.
        """
        data = read_clusterer_result_from_uea_format(csv_path)
        first_line = data["first_line_comment"]
        parameters = ast.literal_eval(",".join((data["estimator_parameters"])))
        temp = pd.DataFrame(data["predictions"])
        predictions_df = pd.DataFrame(temp[[0, 1]])
        metrics_score = self._compute_metrics(predictions_df)
        estimator_name = self.get_estimator_name(first_line, parameters)
        return (first_line[0], first_line[1], estimator_name, metrics_score)

    def get_estimator_name(
        self, estimator_details: List[str], estimator_params: List[str]
    ) -> str:
        """Generate estimator name from parameters.

        Parameters
        ----------
        estimator_details: List[str]
            List of strings containing details about the estimator.
        estimator_params: List[str]
            List of strings containing details of the parameters the estimator used.

        Returns
        -------
        str
            Name of estimator to use.
        """
        estimator_name = estimator_details[1]
        if self.naming_parameter_key is not None:
            estimator_name = (
                f"{estimator_name}-{estimator_params[self.naming_parameter_key]}"
            )
        return estimator_name

    def _compute_metrics(self, predictions_df: pd.DataFrame) -> Dict:
        numpy_pred = predictions_df.to_numpy()
        true_class = [i[0] for i in numpy_pred[1:]]
        predicted_class = [i[1] for i in numpy_pred[1:]]
        metric_scores = {}
        for metric in self.metrics:
            metric_callable = _evaluation_metrics_dict[metric]
            metric_scores[metric] = metric_callable(true_class, predicted_class)

        return metric_scores


if __name__ == "__main__":
    evaluator = ClusterEvaluator(
        "C:\\Users\\chris\\Documents\\Projects\\sktime\\sktime\\benchmarking"
        "\\evaluation\\tests\\test_results",
        "C:\\Users\\chris\\Documents\\Projects\\sktime\\sktime\\benchmarking"
        "\\evaluation\\tests\\result_out",
        experiment_name="example_experiment",
        naming_parameter_key="metric",
        critical_diff_params={"alpha": 100000.0},
    )

    evaluator.run_evaluation(["kmeans", "kmedoids"])

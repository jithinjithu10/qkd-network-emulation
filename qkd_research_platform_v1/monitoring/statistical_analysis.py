# monitoring/statistical_analysis.py

import pandas as pd
import numpy as np
from scipy import stats


class StatisticalAnalyzer:

    def __init__(self, csv_file="experiment_results.csv"):
        self.df = pd.read_csv(csv_file)

    # =================================================
    # Confidence Interval
    # =================================================
    def confidence_interval(self, data, confidence=0.95):
        mean = np.mean(data)
        std_err = stats.sem(data)
        h = std_err * stats.t.ppf((1 + confidence) / 2., len(data)-1)
        return mean, h

    # =================================================
    # T-Test Between Two Modes
    # =================================================
    def compare_modes(self, metric, mode1, mode2):

        data1 = self.df[self.df["mode"] == mode1][metric]
        data2 = self.df[self.df["mode"] == mode2][metric]

        t_stat, p_value = stats.ttest_ind(data1, data2)

        return {
            "metric": metric,
            "mode1": mode1,
            "mode2": mode2,
            "t_statistic": t_stat,
            "p_value": p_value
        }

    # =================================================
    # Run Full Comparison
    # =================================================
    def full_analysis(self):

        metrics = [
            "avg_latency",
            "throughput_bytes_per_sec",
            "success_rate",
            "rekey_count"
        ]

        modes = self.df["mode"].unique()

        results = []

        for metric in metrics:
            for i in range(len(modes)):
                for j in range(i+1, len(modes)):

                    comparison = self.compare_modes(
                        metric,
                        modes[i],
                        modes[j]
                    )

                    results.append(comparison)

        return results


if __name__ == "__main__":

    analyzer = StatisticalAnalyzer()
    results = analyzer.full_analysis()

    for r in results:
        print(r)
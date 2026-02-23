# monitoring/qber_analysis.py

import json
import matplotlib.pyplot as plt


class QBERAnalyzer:

    def __init__(self, audit_file="audit.log"):
        self.audit_file = audit_file
        self.qbers = []

    # =================================================
    # Extract QBER from Audit Log
    # =================================================
    def extract_qber(self):

        with open(self.audit_file, "r") as file:
            for line in file:
                try:
                    entry = json.loads(line)
                    if entry.get("metadata") and "qber" in entry["metadata"]:
                        self.qbers.append(entry["metadata"]["qber"])
                except:
                    continue

    # =================================================
    # Plot Distribution
    # =================================================
    def plot_distribution(self):

        plt.figure()
        plt.hist(self.qbers, bins=20)
        plt.title("QBER Distribution")
        plt.xlabel("QBER")
        plt.ylabel("Frequency")
        plt.savefig("qber_distribution.png")
        plt.close()

    # =================================================
    # Plot Threshold Overlay
    # =================================================
    def plot_with_threshold(self, threshold=0.11):

        plt.figure()
        plt.hist(self.qbers, bins=20)
        plt.axvline(threshold)
        plt.title("QBER Distribution with Threshold")
        plt.xlabel("QBER")
        plt.ylabel("Frequency")
        plt.savefig("qber_threshold_overlay.png")
        plt.close()


if __name__ == "__main__":

    analyzer = QBERAnalyzer()
    analyzer.extract_qber()
    analyzer.plot_distribution()
    analyzer.plot_with_threshold()
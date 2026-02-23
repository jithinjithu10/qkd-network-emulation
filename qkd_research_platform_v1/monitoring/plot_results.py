# monitoring/plot_results.py

import pandas as pd
import matplotlib.pyplot as plt


class PlotResults:

    def __init__(self, csv_file="experiment_results.csv"):
        self.csv_file = csv_file
        self.df = pd.read_csv(csv_file)

    # =================================================
    # Latency Plot
    # =================================================
    def plot_latency(self):

        plt.figure()
        plt.bar(self.df["mode"], self.df["avg_latency"])
        plt.title("Average Latency by Policy Mode")
        plt.xlabel("Policy Mode")
        plt.ylabel("Latency (seconds)")
        plt.savefig("latency_plot.png")
        plt.close()

    # =================================================
    # Throughput Plot
    # =================================================
    def plot_throughput(self):

        plt.figure()
        plt.bar(self.df["mode"], self.df["throughput_bytes_per_sec"])
        plt.title("Throughput by Policy Mode")
        plt.xlabel("Policy Mode")
        plt.ylabel("Bytes per Second")
        plt.savefig("throughput_plot.png")
        plt.close()

    # =================================================
    # Success Rate Plot
    # =================================================
    def plot_success_rate(self):

        plt.figure()
        plt.bar(self.df["mode"], self.df["success_rate"])
        plt.title("Success Rate by Policy Mode")
        plt.xlabel("Policy Mode")
        plt.ylabel("Success Rate")
        plt.savefig("success_rate_plot.png")
        plt.close()

    # =================================================
    # Rekey Plot
    # =================================================
    def plot_rekey_count(self):

        plt.figure()
        plt.bar(self.df["mode"], self.df["rekey_count"])
        plt.title("Rekey Count by Policy Mode")
        plt.xlabel("Policy Mode")
        plt.ylabel("Rekey Count")
        plt.savefig("rekey_plot.png")
        plt.close()

    # =================================================
    # Generate All
    # =================================================
    def generate_all_plots(self):

        self.plot_latency()
        self.plot_throughput()
        self.plot_success_rate()
        self.plot_rekey_count()

        print("Plots generated successfully.")


if __name__ == "__main__":

    plotter = PlotResults()
    plotter.generate_all_plots()
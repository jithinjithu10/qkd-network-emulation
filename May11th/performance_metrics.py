# performance_metrics.py
# HYBRID QKD PERFORMANCE & RESEARCH ANALYTICS

import time

from statistics import mean

from audit import AuditLogger

from config import (
    QKD_PROTOCOL,
    SYSTEM_MODE
)


class PerformanceMetrics:

    """
    Performance Metrics Manager

    Responsibilities
    ----------------
    - latency analysis
    - synchronization timing
    - encryption performance
    - throughput calculation
    - QKD efficiency analysis
    - session analytics
    - distributed benchmarking

    Research Usage
    --------------
    Useful for:
    - thesis graphs
    - paper results
    - benchmarking
    - PPT analytics
    """

    def __init__(self):

        self.audit = AuditLogger()

        # =================================================
        # GLOBAL START TIME
        # =================================================

        self.start_time = (
            time.perf_counter()
        )

        # =================================================
        # LATENCY TRACKING
        # =================================================

        self.encryption_times = []

        self.decryption_times = []

        self.sync_times = []

        self.qkd_generation_times = []

        self.message_delivery_times = []

        self.session_establishment_times = []

        # =================================================
        # THROUGHPUT
        # =================================================

        self.total_messages = 0

        self.total_bytes = 0

        self.generated_keys = 0

        self.total_key_bits = 0

        self.total_consumed_bits = 0

        # =================================================
        # QKD METRICS
        # =================================================

        self.qber_values = []

        self.failed_sessions = 0

        self.successful_sessions = 0

        self.retry_counts = []

        self.sync_failures = 0

        self.replay_attempts = 0

        # =================================================
        # SESSION STORAGE
        # =================================================

        self.session_metrics = {}

    # =====================================================
    # RECORD ENCRYPTION
    # =====================================================

    def record_encryption(
        self,
        duration
    ):

        self.encryption_times.append(
            duration
        )

    # =====================================================
    # RECORD DECRYPTION
    # =====================================================

    def record_decryption(
        self,
        duration
    ):

        self.decryption_times.append(
            duration
        )

    # =====================================================
    # RECORD SYNCHRONIZATION
    # =====================================================

    def record_sync(
        self,
        duration
    ):

        self.sync_times.append(
            duration
        )

    # =====================================================
    # RECORD QKD GENERATION
    # =====================================================

    def record_qkd_generation(
        self,
        duration,
        key_bits=256
    ):

        self.qkd_generation_times.append(
            duration
        )

        self.generated_keys += 1

        self.total_key_bits += key_bits

    # =====================================================
    # RECORD DELIVERY
    # =====================================================

    def record_delivery(
        self,
        duration
    ):

        self.message_delivery_times.append(
            duration
        )

    # =====================================================
    # RECORD MESSAGE
    # =====================================================

    def record_message(
        self,
        size_bytes
    ):

        self.total_messages += 1

        self.total_bytes += size_bytes

    # =====================================================
    # RECORD QBER
    # =====================================================

    def record_qber(
        self,
        qber
    ):

        self.qber_values.append(
            qber
        )

    # =====================================================
    # RECORD RETRY
    # =====================================================

    def record_retry(
        self,
        retries
    ):

        self.retry_counts.append(
            retries
        )

    # =====================================================
    # RECORD SESSION ESTABLISHMENT
    # =====================================================

    def record_session_establishment(
        self,
        duration
    ):

        self.session_establishment_times.append(
            duration
        )

    # =====================================================
    # RECORD KEY CONSUMPTION
    # =====================================================

    def record_key_consumption(
        self,
        bits
    ):

        self.total_consumed_bits += bits

    # =====================================================
    # RECORD REPLAY ATTEMPT
    # =====================================================

    def record_replay_attempt(
        self
    ):

        self.replay_attempts += 1

    # =====================================================
    # RECORD SYNC FAILURE
    # =====================================================

    def record_sync_failure(
        self
    ):

        self.sync_failures += 1

    # =====================================================
    # SESSION SUCCESS
    # =====================================================

    def session_success(
        self
    ):

        self.successful_sessions += 1

    # =====================================================
    # SESSION FAILURE
    # =====================================================

    def session_failure(
        self
    ):

        self.failed_sessions += 1

    # =====================================================
    # START TIMER
    # =====================================================

    def timer(
        self
    ):

        return time.perf_counter()

    # =====================================================
    # STOP TIMER
    # =====================================================

    def elapsed(
        self,
        start_time
    ):

        return (
            time.perf_counter()
            - start_time
        )

    # =====================================================
    # STORE SESSION METRICS
    # =====================================================

    def store_session(

        self,

        session_id,

        metrics
    ):

        self.session_metrics[
            session_id
        ] = metrics

    # =====================================================
    # AVERAGE HELPER
    # =====================================================

    def avg(
        self,
        values
    ):

        if not values:
            return 0

        return mean(values)

    # =====================================================
    # MAX HELPER
    # =====================================================

    def max_value(
        self,
        values
    ):

        if not values:
            return 0

        return max(values)

    # =====================================================
    # MIN HELPER
    # =====================================================

    def min_value(
        self,
        values
    ):

        if not values:
            return 0

        return min(values)

    # =====================================================
    # TOTAL ELAPSED TIME
    # =====================================================

    def total_runtime(
        self
    ):

        return (
            time.perf_counter()
            - self.start_time
        )

    # =====================================================
    # TRUE THROUGHPUT
    # =====================================================

    def throughput(
        self
    ):

        """
        True network throughput
        in bytes/second.
        """

        runtime = self.total_runtime()

        if runtime <= 0:
            return 0

        return (
            self.total_bytes
            / runtime
        )

    # =====================================================
    # MESSAGE THROUGHPUT
    # =====================================================

    def messages_per_second(
        self
    ):

        runtime = self.total_runtime()

        if runtime <= 0:
            return 0

        return (
            self.total_messages
            / runtime
        )

    # =====================================================
    # SUCCESS RATE
    # =====================================================

    def success_rate(
        self
    ):

        total = (

            self.successful_sessions
            +
            self.failed_sessions
        )

        if total == 0:
            return 0

        return (

            self.successful_sessions
            /
            total
        ) * 100

    # =====================================================
    # QKD EFFICIENCY
    # =====================================================

    def qkd_efficiency(
        self
    ):

        """
        Useful key bits /
        generated BB84 bits.
        """

        if self.total_key_bits == 0:
            return 0

        return (

            self.total_consumed_bits
            /
            self.total_key_bits

        ) * 100

    # =====================================================
    # AVERAGE RETRIES
    # =====================================================

    def average_retries(
        self
    ):

        return self.avg(
            self.retry_counts
        )

    # =====================================================
    # RESEARCH REPORT
    # =====================================================

    def report(
        self
    ):

        return {

            # ---------------------------------------------
            # SYSTEM
            # ---------------------------------------------

            "protocol":
                QKD_PROTOCOL,

            "mode":
                SYSTEM_MODE,

            # ---------------------------------------------
            # MESSAGES
            # ---------------------------------------------

            "total_messages":
                self.total_messages,

            "total_bytes":
                self.total_bytes,

            "messages_per_second":
                self.messages_per_second(),

            # ---------------------------------------------
            # THROUGHPUT
            # ---------------------------------------------

            "throughput_bytes_per_sec":
                self.throughput(),

            # ---------------------------------------------
            # QKD
            # ---------------------------------------------

            "generated_keys":
                self.generated_keys,

            "generated_key_bits":
                self.total_key_bits,

            "consumed_key_bits":
                self.total_consumed_bits,

            "qkd_efficiency":
                self.qkd_efficiency(),

            "average_qber":
                self.avg(
                    self.qber_values
                ),

            "max_qber":
                self.max_value(
                    self.qber_values
                ),

            "min_qber":
                self.min_value(
                    self.qber_values
                ),

            # ---------------------------------------------
            # LATENCIES
            # ---------------------------------------------

            "avg_encryption_time":
                self.avg(
                    self.encryption_times
                ),

            "avg_decryption_time":
                self.avg(
                    self.decryption_times
                ),

            "avg_sync_time":
                self.avg(
                    self.sync_times
                ),

            "avg_qkd_generation":
                self.avg(
                    self.qkd_generation_times
                ),

            "avg_delivery_time":
                self.avg(
                    self.message_delivery_times
                ),

            "avg_session_establishment":
                self.avg(
                    self.session_establishment_times
                ),

            # ---------------------------------------------
            # MAX VALUES
            # ---------------------------------------------

            "max_sync_time":
                self.max_value(
                    self.sync_times
                ),

            "max_qkd_generation":
                self.max_value(
                    self.qkd_generation_times
                ),

            # ---------------------------------------------
            # MIN VALUES
            # ---------------------------------------------

            "min_sync_time":
                self.min_value(
                    self.sync_times
                ),

            "min_qkd_generation":
                self.min_value(
                    self.qkd_generation_times
                ),

            # ---------------------------------------------
            # RETRIES
            # ---------------------------------------------

            "average_retries":
                self.average_retries(),

            "sync_failures":
                self.sync_failures,

            # ---------------------------------------------
            # SECURITY
            # ---------------------------------------------

            "replay_attempts":
                self.replay_attempts,

            # ---------------------------------------------
            # SESSION STATS
            # ---------------------------------------------

            "successful_sessions":
                self.successful_sessions,

            "failed_sessions":
                self.failed_sessions,

            "success_rate":
                self.success_rate(),

            # ---------------------------------------------
            # RUNTIME
            # ---------------------------------------------

            "runtime_seconds":
                self.total_runtime()
        }

    # =====================================================
    # SUMMARY
    # =====================================================

    def summary(
        self
    ):

        report = self.report()

        return {

            "protocol":
                report["protocol"],

            "messages":
                report["total_messages"],

            "keys":
                report["generated_keys"],

            "avg_qber":
                report["average_qber"],

            "throughput":
                report[
                    "throughput_bytes_per_sec"
                ],

            "success_rate":
                report["success_rate"]
        }

    # =====================================================
    # EXPORT
    # =====================================================

    def export_all(
        self
    ):

        return {

            "report":
                self.report(),

            "sessions":
                self.session_metrics
        }

    # =====================================================
    # DEBUG
    # =====================================================

    def debug_dump(
        self
    ):

        return self.export_all()


# =========================================================
# STANDALONE TEST
# =========================================================

if __name__ == "__main__":

    pm = PerformanceMetrics()

    pm.record_message(1024)

    pm.record_qber(0.03)

    pm.record_encryption(0.002)

    pm.record_decryption(0.001)

    pm.record_sync(0.15)

    pm.record_qkd_generation(
        duration=0.8,
        key_bits=256
    )

    pm.record_key_consumption(
        128
    )

    pm.record_retry(2)

    pm.session_success()

    print("\nPERFORMANCE REPORT")

    print(pm.report())
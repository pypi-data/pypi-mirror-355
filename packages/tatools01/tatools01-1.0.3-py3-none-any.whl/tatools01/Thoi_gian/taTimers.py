import time


class MultiTimer:
    def __init__(self):
        self.times = {}  # Lưu trữ thời gian của mỗi đoạn code
        self.start_time = None

    def start(self):
        """Bắt đầu đo thời gian."""
        self.start_time = time.time()
    def stop(self):
        """Bắt đầu đo thời gian."""
        self.start_time = None

    def update(self, label):
        """Dừng đo thời gian và lưu kết quả cho một đoạn code với nhãn (label)."""
        if self.start_time is None:
            raise Exception("Timer has not been started yet!")
        elapsed_time = time.time() - self.start_time
        if label in self.times:
            self.times[label].append(elapsed_time)
        else:
            self.times[label] = [elapsed_time]
        self.start_time = time.time()

    def reset(self):
        """Đặt lại bộ đếm thời gian."""
        self.start_time = None
        self.times = {}

    def summary(self):
        """In ra kết quả đo thời gian cho tất cả các đoạn code."""
        if not self.times:
            print("No times recorded.")
        else:
            print("\n=== Time Summary ===")
            for label, times in self.times.items():
                total_time = sum(times)
                avg_time = total_time / len(times)
                print(f"Code: {label}")
                print(f"  Total time: {total_time:.6f} seconds")
                print(f"  Average time: {avg_time:.6f} seconds")
                print(f"  Runs: {len(times)}\n")

if __name__ == "__main__":
    # Ví dụ sử dụng class MultiTimer
    timer = MultiTimer()

    # Đo thời gian cho đoạn code 1
    timer.start()
    # Đoạn code mà bạn muốn đo (ví dụ 1)
    for _ in range(1000000):
        pass
    timer.update("Code 1")

    # Đo thời gian cho đoạn code 2
    timer.start()
    # Đoạn code mà bạn muốn đo (ví dụ 2)
    time.sleep(1)
    timer.update("Code 2")

    # Đo lại thời gian cho Code 1
    timer.start()
    for _ in range(500000):
        pass
    timer.update("Code 1")

    # In ra kết quả cuối cùng
    timer.summary()

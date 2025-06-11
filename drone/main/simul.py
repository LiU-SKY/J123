import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# ========== BLE 시뮬레이터 (비공개 위치) ========== #
class BLESimulator:
    def __init__(self, tag_position, A=-40, n=2.5, noise_std=2.0):
        self._tag_position = np.array(tag_position)
        self.A = A
        self.n = n
        self.noise_std = noise_std

    def get_rssi(self, position):
        d = np.linalg.norm(position - self._tag_position)
        if d < 0.1:
            d = 0.1
        rssi = self.A - 10 * self.n * np.log10(d)
        noise = np.random.normal(0, self.noise_std)
        return rssi + noise

# ========== 드론 트래커 (z축 포함) ========== #
class DroneTracker:
    def __init__(self, ble_simulator, start_position=(0, 0, 0)):
        self.ble = ble_simulator
        self.pos = np.array(start_position, dtype=float)
        self.history = [self.pos.copy()]
        self.rssi_trace = []

        # 26방향 (3x3x3 cube 중심 제외)
        self.directions = np.array([
            [dx, dy, dz]
            for dx in [-1, 0, 1]
            for dy in [-1, 0, 1]
            for dz in [-1, 0, 1]
            if not (dx == dy == dz == 0)
        ])

    def step(self, step_size=0.5):
        current_rssi = self.ble.get_rssi(self.pos)
        best_rssi = current_rssi
        best_move = np.array([0, 0, 0])

        for direction in self.directions:
            next_pos = self.pos + direction * step_size
            rssi = self.ble.get_rssi(next_pos)
            if rssi > best_rssi:
                best_rssi = rssi
                best_move = direction

        self.pos += best_move * step_size
        self.history.append(self.pos.copy())
        self.rssi_trace.append(best_rssi)
        return best_rssi

    def run(self, max_steps=150, rssi_threshold=-15):
        for i in range(max_steps):
            rssi = self.step()
            print(f"[{i:02d}] 📶 위치: {self.pos.round(2)}, RSSI: {rssi:.2f} dBm")
            if rssi >= rssi_threshold:
                print("🎯 목표 도달 (RSSI 임계값 도달)")
                break

# ========== 실행 및 시각화 ========== #
def simulate():
    TAG_POSITION = [4, -3, 3]  # 태그 위치 (외부에 노출되지 않음)
    ble = BLESimulator(TAG_POSITION)
    tracker = DroneTracker(ble, start_position=(0, 0, 0))
    tracker.run()

    # 시각화
    history = np.array(tracker.history)
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.plot(history[:, 0], history[:, 1], history[:, 2], marker='o', label="Drone Path")
    ax.scatter(*TAG_POSITION, color='red', label="(숨겨진) BLE Tag", s=100)
    ax.set_title("📡 3D BLE RSSI 기반 추적 시뮬레이션 (Z축 포함)")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.legend()
    plt.show()

if __name__ == "__main__":
    simulate()

# sim3d_run.py
# 3d 궤적 그려보는 시뮬레이션
"""
3D RSSI 추적 시뮬레이터 (standalone plotting)
- rssi_tracker의 fwd/yaw로 xy를 이동
- z는 시뮬레이터 보조 제어(타깃 고도 수렴)
- 실행 시 3D 궤적을 화면에 표시하거나 PNG로 저장

Usage:
  python sim3d_run.py --duration 60 --dropout 0.12
  python sim3d_run.py --save out.png --no-show
"""
import math, random, argparse
from typing import List, Tuple
from drone.main.rssi_tracker import RSSITracker, Config, ControlCmd

def rssi_from_distance_3d(dx, dy, dz, rssi0=-45.0, n=2.0, d0=1.0, noise_db=2.0):
    d = math.sqrt(dx*dx + dy*dy + dz*dz)
    d = max(0.2, d)
    rssi = rssi0 - 10*n*math.log10(d/d0) + random.gauss(0, noise_db)
    return rssi

def simulate_3d(duration_s=60.0, dt=0.2, dropout_p=0.1):
    cfg = Config(
        ema_alpha=0.25,
        der_alpha=0.35,
        scan_period=dt,
        found_threshold_db=-70.0,
        close_threshold_db=0.0,
        lost_timeout_s=2.5,
        yaw_sweep_rate=0.8,
        yaw_nudge_rate=0.3,
        approach_speed=0.8,
        min_speed=0.1,
        max_speed=1.6,
        der_gain=5.0,
    )
    tracker = RSSITracker(cfg)

    # 초기 상태
    x, y, z = -15.0, -10.0, 0.5
    yaw = math.radians(20)

    # 타깃 위치 (고정)
    tx, ty, tz = 10.0, 12.0, 2.0

    # 고도 제어(시뮬 전용)
    kz = 0.6
    z_max_speed = 0.8

    traj: List[Tuple[float,float,float]] = []
    times: List[float] = []
    rssis: List[float] = []
    states: List[str] = []

    t = 0.0
    while t <= duration_s:
        dx, dy, dz = tx - x, ty - y, tz - z

        # RSSI 생성 (드롭아웃 고려)
        if random.random() < dropout_p:
            rssi = None
        else:
            rssi = rssi_from_distance_3d(dx, dy, dz)

        cmd: ControlCmd = tracker.step(rssi, now=t)

        # 평면 운동
        yaw += cmd.yaw_rate * dt
        vx = cmd.forward * math.cos(yaw)
        vy = cmd.forward * math.sin(yaw)

        # 고도 운동
        z_err = tz - z
        vz = max(-z_max_speed, min(z_max_speed, kz * z_err))

        x += vx * dt
        y += vy * dt
        z += vz * dt

        traj.append((x, y, z))
        times.append(t)
        rssis.append(float('nan') if rssi is None else rssi)
        states.append(tracker.state.name)

        t += dt

    return {"traj": traj, "times": times, "rssis": rssis, "states": states, "target": (tx, ty, tz)}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=float, default=60.0, help="simulation length (s)")
    parser.add_argument("--dt", type=float, default=0.2, help="time step (s)")
    parser.add_argument("--dropout", type=float, default=0.12, help="packet dropout probability [0..1]")
    parser.add_argument("--save", type=str, default=None, help="save figure to this PNG path")
    parser.add_argument("--no-show", action="store_true", help="do not display the window")
    args = parser.parse_args()

    data = simulate_3d(duration_s=args.duration, dt=args.dt, dropout_p=args.dropout)

    # Plot
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

    import numpy as np
    traj = np.array(data["traj"])
    tx, ty, tz = data["target"]

    fig = plt.figure(figsize=(7,7))
    ax = fig.add_subplot(111, projection='3d')
    ax.plot(traj[:,0], traj[:,1], traj[:,2], linewidth=1.5)
    ax.scatter([tx], [ty], [tz], marker='x', s=60)
    ax.set_title("3D trajectory (drone path to target)")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_zlabel("z (m)")

    if args.save:
        plt.savefig(args.save, dpi=140, bbox_inches="tight")
        print(f"Saved figure to: {args.save}")

    if not args.no_show:
        plt.show()

    print(f"done {len(traj)}")

if __name__ == "__main__":
    main()

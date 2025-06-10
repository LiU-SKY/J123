from pymavlink import mavutil
import time

# Pixhawk와 연결
master = mavutil.mavlink_connection('/dev/ttyACM0', baud=57600)
master.wait_heartbeat()
print("✅ Pixhawk 연결됨")

# ARM (모터 작동 허용)
master.mav.command_long_send(
    master.target_system, master.target_component,
    mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
    0,
    1, 0, 0, 0, 0, 0, 0)
print("⚙️ ARM 명령 전송")

time.sleep(2)

# OFFBOARD 모드 전환
master.mav.command_long_send(
    master.target_system, master.target_component,
    mavutil.mavlink.MAV_CMD_DO_SET_MODE,
    0,
    1, 6, 0, 0, 0, 0, 0)
print("🚀 OFFBOARD 모드 전환 명령 전송")

# Setpoint 전송 루프 (z = -1은 NED 기준으로 1m 상승)
for _ in range(100):
    master.mav.set_position_target_local_ned_send(
        int(time.time() * 1e6),
        master.target_system, master.target_component,
        mavutil.mavlink.MAV_FRAME_LOCAL_NED,
        0b0000111111000111,
        0, 0, -1,   # x, y, z
        0, 0, 0,    # vx, vy, vz
        0, 0, 0,    # ax, ay, az
        0, 0)       # yaw, yaw_rate
    time.sleep(0.1)

print("📡 위치 명령 전송 완료")

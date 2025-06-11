#!/usr/bin/env python3

from pymavlink import mavutil
import time

# 1. 연결 설정
master = mavutil.mavlink_connection('/dev/ttyAMA0', baud=57600)

# 2. Heartbeat 수신 대기 (시작 확인)
master.wait_heartbeat()
print("💓 Heartbeat received")

# 3. 모드 설정 함수
def set_mode(mode_name):
    mode_id = master.mode_mapping()[mode_name]
    master.mav.set_mode_send(
        master.target_system,
        mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
        mode_id
    )
    print(f"✈️ Mode set to {mode_name}")
    time.sleep(1)

# 4. 모터 시동 (Arm)
def arm_drone():
    master.arducopter_arm()
    master.motors_armed_wait()
    print("✅ Drone Armed")

# 5. 스로틀 수동 제어 (수동 PWM)
def manual_throttle(throttle_pwm=1500):
    # mode: MANUAL (혹은 STABILIZE/ALT_HOLD 등 지원되는 모드 사용 가능)
    set_mode("STABILIZE")

    # RC_OVERRIDE: 채널 3이 스로틀 (1~8까지 순서대로: roll, pitch, throttle, yaw ...)
    master.mav.rc_channels_override_send(
        master.target_system,
        master.target_component,
        0, 0, throttle_pwm, 0, 0, 0, 0, 0
    )
    print(f"🚀 Throttle set to {throttle_pwm} μs")

# 6. 실행 예시
set_mode("STABILIZE")    # 혹은 "ALT_HOLD", "GUIDED" 등
arm_drone()

# 일정 시간 동안 스로틀 조작
for i in range(5):
    manual_throttle(1600)  # 상승
    time.sleep(1)
manual_throttle(1000)      # 하강

# 필요 시 모터 정지
master.arducopter_disarm()
print("🛑 Drone Disarmed")

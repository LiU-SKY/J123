#!/usr/bin/env python3

import time
from pymavlink import mavutil
#
# --- 설정 ---
CONNECTION_PORT = '/dev/ttyACM0'  # USB 포트 (시스템에 따라 ttyUSB0 등일 수 있음)
BAUD_RATE = 57600                # QGroundControl에서 설정한 BAUD와 일치해야 함

TAKEOFF_THROTTLE = 500
TAKEOFF_DURATION_SECONDS = 5
HOVER_DURATION_SECONDS = 7
LANDING_THROTTLE = 100
LANDING_DURATION_SECONDS = 10

PX4_ALTCTL_MODE_ID = 1  # ALTCTL
PX4_STABILIZED_MODE_ID = 0  # STABILIZED

# --- MAVLink 연결 ---
print(f"드론에 연결 중: {CONNECTION_PORT} @ {BAUD_RATE} baud...")
try:
    master = mavutil.mavlink_connection(CONNECTION_PORT, baud=BAUD_RATE)
except Exception as e:
    print(f"❌ 드론 연결 실패: {e}")
    exit()

print("📡 하트비트 수신 대기 중...")
master.wait_heartbeat()
print(f"✅ 하트비트 수신! 시스템 ID: {master.target_system}, 컴포넌트 ID: {master.target_component}")


# --- 함수 정의 ---

def wait_for_mode_change(master, target_mode_name, timeout_seconds=10):
    print(f"🕹️ 모드 '{target_mode_name}' 대기 중...")
    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        msg = master.recv_match(type='HEARTBEAT', blocking=True, timeout=1)
        if msg:
            if mavutil.mode_string_v10(msg) == target_mode_name:
                print(f"✅ 모드 '{target_mode_name}' 전환 완료.")
                return True
        time.sleep(0.1)
    print(f"⚠️ 모드 '{target_mode_name}' 전환 실패 (타임아웃).")
    return False


def set_px4_custom_mode(master, custom_mode_id):
    print(f"🔧 PX4 Custom Mode {custom_mode_id} 전환 시도 중...")
    master.mav.set_mode_send(
        master.target_system,
        mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
        custom_mode_id
    )
    time.sleep(0.1)


def arm_drone(master):
    print("🔒 드론 ARM 시도 중...")
    master.mav.command_long_send(
        master.target_system,
        master.target_component,
        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
        0, 1, 0, 0, 0, 0, 0, 0)

    start_time = time.time()
    while not master.motors_armed() and (time.time() - start_time < 10):
        master.recv_match(type='HEARTBEAT', blocking=True, timeout=1)
        print("-- ARM 대기 중...")
        time.sleep(0.5)

    if master.motors_armed():
        print("✅ ARM 완료.")
        return True
    else:
        print("❌ ARM 실패.")
        return False


def disarm_drone(master):
    print("🔓 드론 Disarm 시도 중...")
    master.mav.command_long_send(
        master.target_system,
        master.target_component,
        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
        0, 0, 0, 0, 0, 0, 0, 0)

    start_time = time.time()
    while master.motors_armed() and (time.time() - start_time < 10):
        master.recv_match(type='HEARTBEAT', blocking=True, timeout=1)
        print("-- Disarm 대기 중...")
        time.sleep(0.5)

    if not master.motors_armed():
        print("✅ Disarm 완료.")
        return True
    else:
        print("❌ Disarm 실패.")
        return False


def send_rc_override(master, throttle_value):
    master.mav.rc_channels_override_send(
        master.target_system,
        master.target_component,
        1500, 1500, int(1000 + throttle_value), 1500,
        0, 0, 0, 0
    )


def get_current_altitude(master, timeout=1.0):
    start_time = time.time()
    while time.time() - start_time < timeout:
        msg = master.recv_match(type='GLOBAL_POSITION_INT', blocking=False, timeout=0.1)
        if msg:
            return msg.relative_alt / 1000.0
        msg = master.recv_match(type='ALTITUDE', blocking=False, timeout=0.1)
        if msg:
            return msg.altitude_relative
        time.sleep(0.01)
    return None

# --- 메인 실행 ---

try:
    # 1. 모드 전환 (ALTCTL → 실패 시 STABILIZED로 fallback)
    set_px4_custom_mode(master, PX4_ALTCTL_MODE_ID)
    if not wait_for_mode_change(master, 'ALTCTL', timeout_seconds=10):
        print("⚠️ ALTCTL 전환 실패 → STABILIZED 시도")
        set_px4_custom_mode(master, PX4_STABILIZED_MODE_ID)
        if not wait_for_mode_change(master, 'STABILIZED', timeout_seconds=10):
            print("❌ 모드 전환 실패. 종료.")
            exit()

    # 2. ARM
    if not arm_drone(master):
        print("❌ ARM 실패. 종료.")
        exit()

    # 3. 이륙
    print(f"\n🚁 이륙 중... ({TAKEOFF_DURATION_SECONDS}초간)")
    start_time = time.time()
    while time.time() - start_time < TAKEOFF_DURATION_SECONDS:
        send_rc_override(master, TAKEOFF_THROTTLE)
        alt = get_current_altitude(master)
        if alt is not None:
            print(f"   현재 고도: {alt:.2f}m")
        time.sleep(0.1)

    # 4. 호버링
    print(f"\n⏸️ 호버링 중... ({HOVER_DURATION_SECONDS}초)")
    time.sleep(HOVER_DURATION_SECONDS)

    # 5. 착륙
    print(f"\n🛬 착륙 중... ({LANDING_DURATION_SECONDS}초간)")
    start_time = time.time()
    while time.time() - start_time < LANDING_DURATION_SECONDS:
        send_rc_override(master, LANDING_THROTTLE)
        alt = get_current_altitude(master)
        if alt is not None:
            print(f"   현재 고도: {alt:.2f}m")
        time.sleep(0.1)

    # 6. Disarm
    print("\n🧯 모터 정지 및 Disarm 대기 중...")
    disarm_drone(master)

except Exception as e:
    print(f"\n❗ 오류 발생: {e}")
    if master.motors_armed():
        print("⚠️ 비상 Disarm 시도...")
        disarm_drone(master)

finally:
    print("🔌 연결 종료.")
    master.close()
    print("🏁 프로그램 종료.")

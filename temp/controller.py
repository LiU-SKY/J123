#!/usr/bin/env python3

import time
from pymavlink import mavutil

# --- 설정 (Setting) ---
CONNECTION_PORT = '/dev/ttyACM0'
BAUD_RATE = 57600  # 픽스호크 USB 통신 속도 (QGroundControl에서 확인)

# 이륙 관련 설정
# ALTCTL 모드에서 직접 스로틀을 제어하여 이륙할 경우 필요한 값입니다.
# MAVLink 스로틀 값은 일반적으로 0 (최저)에서 1000 (최고) 사이입니다.
# 드론의 크기와 무게에 따라 적절한 값을 찾아야 합니다.
# 너무 낮으면 이륙 안 되고, 너무 높으면 빠르게 솟아오릅니다.
TAKEOFF_THROTTLE = 500  # 적절한 이륙 스로틀 값 (0-1000) - 드론마다 다름!
TAKEOFF_DURATION_SECONDS = 5  # 이륙을 위해 스로틀을 줄 시간 (초)
HOVER_DURATION_SECONDS = 7  # 호버링 시간 (초)
LANDING_THROTTLE = 100  # 착륙을 위해 스로틀을 줄 값 (0-1000)
LANDING_DURATION_SECONDS = 10  # 착륙을 위해 스로틀을 줄 시간 (초)

# PX4 Custom Flight Modes
# MAVLink.io/en/messages/common.html#MAV_MODE_PX4_CUSTOM_MODE
PX4_ALTCTL_MODE_ID = 1  # PX4 Altitude Control Mode (고도 제어)

# --- MAVLink 연결 (MAVLink Connection) ---
print(f"드론에 연결 중: {CONNECTION_PORT} @ {BAUD_RATE} baud...")
try:
    master = mavutil.mavlink_connection(CONNECTION_PORT, baud=BAUD_RATE)
except Exception as e:
    print(f"드론 연결 실패: {e}")
    print("다음 사항을 확인하세요:")
    print("1. 픽스호크가 USB로 라즈베리파이에 연결되어 있고 전원이 켜져 있는지.")
    print("2. 'sudo usermod -a -G dialout $USER' 명령으로 사용자에게 시리얼 포트 권한이 부여되었는지 (재부팅 필수).")
    print("3. CONNECTION_PORT와 BAUD_RATE 설정이 올바른지.")
    exit()

# 첫 번째 하트비트를 기다려 연결 확인 및 시스템 ID 획득
print("하트비트 대기 중...")
master.wait_heartbeat()
print(f"하트비트 수신! 시스템 ID: {master.target_system}, 컴포넌트 ID: {master.target_component}")


# --- 헬퍼 함수 (Helper Functions) ---

def wait_for_mode_change(master, target_mode_name, timeout_seconds=10):
    """지정된 비행 모드로 전환될 때까지 대기합니다."""
    print(f"모드 '{target_mode_name}' 대기 중...")
    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        msg = master.recv_match(type='HEARTBEAT', blocking=True, timeout=1)
        if msg:
            # HEARTBEAT 메시지에서 비행 모드 문자열을 추출합니다.
            current_mode = mavutil.mode_string_v10(msg)  # <--- 수정된 부분
            if current_mode == target_mode_name:
                print(f"-- 모드 '{target_mode_name}'로 전환되었습니다.")
                return True
        time.sleep(0.1)
    print(f"오류: 모드 '{target_mode_name}' 전환 타임아웃.")
    return False


def set_px4_custom_mode(master, custom_mode_id):
    """PX4의 커스텀 비행 모드를 설정합니다."""
    print(f"PX4 Custom Mode {custom_mode_id}로 전환 시도 중...")
    master.mav.set_mode_send(
        master.target_system,
        mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
        custom_mode_id
    )
    time.sleep(0.1)


def arm_drone(master):
    """드론을 ARM 시킵니다."""
    print("ARMing 중...")
    master.mav.command_long_send(
        master.target_system,
        master.target_component,
        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
        0, 1, 0, 0, 0, 0, 0, 0)

    start_time = time.time()
    while not master.motors_armed() and (time.time() - start_time < 10):
        master.recv_match(type='HEARTBEAT', blocking=True, timeout=1)
        print("-- ARM 대기 중...")

    if master.motors_armed():
        print("드론이 ARM 되었습니다.")
        return True
    else:
        print("ARMing 실패 또는 타임아웃.")
        return False


def disarm_drone(master):
    """드론을 Disarm 시킵니다."""
    print("Disarming 중...")
    master.mav.command_long_send(
        master.target_system,
        master.target_component,
        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
        0, 0, 0, 0, 0, 0, 0, 0)

    start_time = time.time()
    while master.motors_armed() and (time.time() - start_time < 10):
        master.recv_match(type='HEARTBEAT', blocking=True, timeout=1)
        print("-- Disarm 대기 중...")

    if not master.motors_armed():
        print("드론이 Disarm 되었습니다.")
        return True
    else:
        print("Disarming 실패 또는 타임아웃.")
        return False


def send_rc_override(master, throttle_value):
    """
    MAVLink RC_CHANNELS_OVERRIDE 메시지를 보내 스로틀 값을 직접 제어합니다.
    GPS가 없을 때 Altitude Control 모드에서 이륙/착륙에 사용될 수 있습니다.
    """
    # MAVLink RC_CHANNELS_OVERRIDE 메시지 전송
    # 각 채널의 값 범위는 일반적으로 1000(최소) ~ 2000(최대)입니다.
    # 스로틀 (channel 3) 값만 변경하고 나머지는 중립(1500)으로 유지합니다.

    master.mav.rc_channels_override_send(
        master.target_system,
        master.target_component,
        1500,  # channel 1 (roll)
        1500,  # channel 2 (pitch)
        int(1000 + throttle_value),  # channel 3 (throttle) - 0-1000 스케일을 1000-2000으로 매핑
        1500,  # channel 4 (yaw)
        0, 0, 0, 0  # channel 5-8 (unused)
    )
    # print(f"RC Override 스로틀 값 전송: {int(1000 + throttle_value)}") # 디버깅용


def get_current_altitude(master, timeout=5):
    """현재 드론의 상대 고도를 가져옵니다 (기압계 기반)."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        # GLOBAL_POSITION_INT 메시지 수신 (relative_alt는 기압계 기반)
        msg = master.recv_match(type='GLOBAL_POSITION_INT', blocking=False, timeout=0.1)
        if msg:
            relative_alt_m = msg.relative_alt / 1000.0
            return relative_alt_m
        # ALTITUDE 메시지 수신 (altitude_relative도 기압계 기반)
        msg = master.recv_match(type='ALTITUDE', blocking=False, timeout=0.1)
        if msg:
            relative_alt_m = msg.altitude_relative
            return relative_alt_m
        time.sleep(0.01)
    return None


# --- 메인 실행 로직 (Main Execution Logic) ---
try:
    # 1. 비행 모드 설정: Altitude Control (ALTCTL) 모드
    set_px4_custom_mode(master, PX4_ALTCTL_MODE_ID)
    if not wait_for_mode_change(master, 'ALTCTL', timeout_seconds=15):
        print("경고: Altitude Control 모드로 전환하지 못했습니다. 수동으로 모드를 설정해주세요.")
        # 안전을 위해 여기서 프로그램을 종료하는 것이 좋습니다.
        # exit()

    # 2. 드론 ARM
    if not arm_drone(master):
        print("드론 ARM 실패. 프로그램을 종료합니다.")
        exit()

    print(f"\n--- 이륙 시작 ({TAKEOFF_DURATION_SECONDS}초간 스로틀 적용) ---")
    start_time = time.time()
    while time.time() - start_time < TAKEOFF_DURATION_SECONDS:
        send_rc_override(master, TAKEOFF_THROTTLE)  # 스로틀 전송
        current_alt = get_current_altitude(master)
        if current_alt is not None:
            print(f"   현재 고도: {current_alt:.2f}m")
        time.sleep(0.1)  # 100ms마다 스로틀 명령 전송

    print(f"\n--- 호버링 시작 ({HOVER_DURATION_SECONDS}초간) ---")
    # RC_CHANNELS_OVERRIDE 메시지를 계속 보내지 않으면
    # PX4의 ALTCTL 모드에서 드론이 자동으로 고도를 유지하려고 시도합니다.
    print(f"{HOVER_DURATION_SECONDS}초 동안 대기...")
    time.sleep(HOVER_DURATION_SECONDS)  # 호버링 시간 대기

    print(f"\n--- 착륙 시작 ({LANDING_DURATION_SECONDS}초간 스로틀 감소) ---")
    start_time = time.time()
    while time.time() - start_time < LANDING_DURATION_SECONDS:
        # 착륙을 위해 스로틀을 점차 줄이거나, 낮은 값으로 유지
        send_rc_override(master, LANDING_THROTTLE)  # 착륙 스로틀 값 전송
        current_alt = get_current_altitude(master)

        # 현재 모드도 함께 확인하여 착륙 진행 상태 판단
        heartbeat_msg_land = master.recv_match(type='HEARTBEAT', blocking=False, timeout=0.1)
        current_flight_mode_land = ""
        if heartbeat_msg_land:
            current_flight_mode_land = mavutil.mode_string_v10(heartbeat_msg_land)  # <--- 수정된 부분

        if current_alt is not None:
            print(f"   현재 고도: {current_alt:.2f}m, 모드: {current_flight_mode_land}")

            # 고도가 0.5m 미만이고, 드론이 착륙 모드에 있거나 ARM 해제 상태라면 착륙 완료로 간주
            # PX4는 착륙 후 자동으로 Disarm 되는 경우가 많습니다.
            if current_alt < 0.5 and not master.motors_armed():
                print("-- 착륙 완료 및 Disarm 확인.")
                break
            elif current_alt < 0.5 and current_flight_mode_land == 'ALTCTL':  # 여전히 ALTCTL 모드이고 고도가 낮으면
                print("-- 지면에 근접했습니다. 모터 정지를 대기합니다.")
                # PX4는 ALTCTL에서 착륙 시 스로틀이 매우 낮으면 자동으로 모터 정지 (disarm) 시퀀스에 들어갈 수 있습니다.
                time.sleep(1)  # 모터 정지를 기다릴 시간
                if not master.motors_armed():
                    print("-- 착륙 완료 (모터 정지 확인).")
                    break

        time.sleep(0.1)  # 메시지 수신 주기

    print("착륙 절차 완료.")
    # 착륙 후 드론이 자동으로 Disarm 될 때까지 기다립니다.
    start_time = time.time()
    while master.motors_armed() and (time.time() - start_time < 10):
        master.recv_match(type='HEARTBEAT', blocking=True, timeout=1)
        print("-- 모터 정지 대기 중...")
        time.sleep(0.5)

    # 픽스호크가 자동으로 Disarm되지 않았다면 수동으로 Disarm 시도
    if master.motors_armed():
        disarm_drone(master)

except Exception as e:
    print(f"\n치명적인 오류 발생: {e}")
    if master.motors_armed():
        print("오류 발생으로 인한 비상 Disarm 시도...")
        try:
            disarm_drone(master)  # 안전을 위해 Disarm 시도
        except Exception as err:
            print(f"비상 처리 중 오류 발생: {err}")
finally:
    print("드론 연결 종료.")
    master.close()
    print("프로그램 종료.")
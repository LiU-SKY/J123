#!/usr/bin/env python3

import time
from pymavlink import mavutil

# --- 설정 (Setting) ---
# 드론 연결 시리얼 포트 (USB를 통해 연결됨)
CONNECTION_PORT = '/dev/ttyACM0'
# 픽스호크의 USB 통신 속도 (일반적으로 57600 또는 115200, 921600 등. 펌웨어 설정에 따라 다름)
# QGroundControl에서 'Parameters' -> 'SER_USB_BAUD' 또는 관련 항목을 확인하세요.
# 만약 연결이 안되면 이 값을 바꿔보세요.
BAUD_RATE = 57600  # 픽스호크 USB 통신 기본 속도 중 하나. 921600도 시도해볼 수 있습니다.

TARGET_ALTITUDE_METERS = 3  # 이륙 목표 고도 (미터)
HOVER_DURATION_SECONDS = 7  # 호버링 시간 (초)

# PX4 Custom Flight Modes (Mavlink.io/en/messages/common.html#MAV_MODE_PX4_CUSTOM_MODE)
# OFFBOARD 모드는 외부 명령을 지속적으로 보내야 유지됩니다.
# 간단한 이륙/착륙에는 Position 모드가 더 안정적일 수 있습니다.
PX4_POS_MODE_ID = 2  # PX4 Position Control Mode
PX4_ALTCTL_MODE_ID = 1  # PX4 Altitude Control Mode (고도만 제어, 수평은 조종)

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
            current_mode = master.flight_mode()  # pymavlink의 현재 비행 모드 문자열 가져오기
            if current_mode == target_mode_name:
                print(f"-- 모드 '{target_mode_name}'로 전환되었습니다.")
                return True
        time.sleep(0.1)
    print(f"오류: 모드 '{target_mode_name}' 전환 타임아웃.")
    return False


def set_px4_custom_mode(master, custom_mode_id):
    """PX4의 커스텀 비행 모드를 설정합니다."""
    # MAV_MODE_FLAG_CUSTOM_MODE_ENABLED를 1로 설정하여 custom_mode 필드가 유효하도록 함
    print(f"PX4 Custom Mode {custom_mode_id}로 전환 시도 중...")
    master.mav.set_mode_send(
        master.target_system,
        mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
        custom_mode_id
    )
    time.sleep(0.1)  # 명령 전송 후 잠시 대기


def arm_drone(master):
    """드론을 ARM 시킵니다."""
    print("ARMing 중...")
    master.mav.command_long_send(
        master.target_system,
        master.target_component,
        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
        0, 1, 0, 0, 0, 0, 0, 0)  # param1 = 1 (ARM)

    start_time = time.time()
    while not master.motors_armed() and (time.time() - start_time < 10):  # 10초 타임아웃
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
        0, 0, 0, 0, 0, 0, 0, 0)  # param1 = 0 (DISARM)

    start_time = time.time()
    while master.motors_armed() and (time.time() - start_time < 10):  # 10초 타임아웃
        master.recv_match(type='HEARTBEAT', blocking=True, timeout=1)
        print("-- Disarm 대기 중...")

    if not master.motors_armed():
        print("드론이 Disarm 되었습니다.")
        return True
    else:
        print("Disarming 실패 또는 타임아웃.")
        return False


def takeoff_drone(master, altitude_meters):
    """드론을 이륙시킵니다."""
    print(f"이륙 명령 전송 중... 목표 고도: {altitude_meters}m")
    master.mav.command_long_send(
        master.target_system,
        master.target_component,
        mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
        0,  # confirmation (0 for normal, 1 for confirmation expected)
        0, 0, 0, 0,  # param2-param5 (unused for takeoff)
        0, 0,  # param6 (lat), param7 (lon) - unused for takeoff from current pos
        altitude_meters  # param8 (altitude in meters)
    )

    # 이륙 명령 후 실제 고도 상승을 기다려야 합니다.
    # 여기서는 간단히 일정 시간 대기합니다.
    # 실제 구현에서는 GLOBAL_POSITION_INT 또는 ALTITUDE 메시지를 받아 고도를 확인해야 합니다.
    print(f"이륙 후 {HOVER_DURATION_SECONDS}초 동안 호버링 대기...")
    time.sleep(HOVER_DURATION_SECONDS)


def land_drone(master):
    """드론을 착륙시킵니다."""
    print("착륙 명령 전송 중...")
    master.mav.command_long_send(
        master.target_system,
        master.target_component,
        mavutil.mavlink.MAV_CMD_NAV_LAND,
        0,  # confirmation
        0, 0, 0, 0,  # param2-param5 (unused)
        0, 0, 0)  # param6, param7, param8 (lat, lon, alt) - 0이면 현재 위치에 착륙

    # 착륙 명령 후 실제 착륙 완료를 기다려야 합니다.
    # 여기서는 간단히 일정 시간 대기합니다.
    print("착륙 완료 대기 중...")
    # 비행 중임을 나타내는 HEARTBEAT 메시지의 'in_air' 상태를 확인하는 것이 더 정확합니다.
    start_time = time.time()
    while time.time() - start_time < 20:  # 최대 20초 대기
        msg = master.recv_match(type='HEARTBEAT', blocking=True, timeout=1)
        if msg:
            if not master.flight_mode() == 'LAND':  # 착륙 모드임을 확인
                # PX4에서는 착륙 완료 시 모터가 자동으로 꺼집니다.
                pass
        # 드론이 땅에 닿았는지 확인하는 로직 (예: 고도 0m 근접 확인)
        # 텔레메트리 스트림에서 고도 정보 받는 부분 추가 필요
        time.sleep(0.5)

    print("착륙 절차 완료.")


# --- 메인 실행 로직 (Main Execution Logic) ---
try:
    # 1. 시동 전 시스템 상태 확인 (필요한 경우)
    # PX4는 일반적으로 안전 스위치가 눌려 있거나, GPS 락이 없거나, 센서 오류가 있으면 ARM이 안됩니다.
    # QGroundControl을 통해 초기 안전 조건을 확인하고 해제해야 합니다.

    # 2. 비행 모드 설정: Position 모드 또는 Altitude 모드 (PX4에서 자율 비행의 기본)
    # 이륙 명령은 Position 또는 Altitude 모드에서 가장 잘 작동합니다.
    set_px4_custom_mode(master, PX4_POS_MODE_ID)  # 또는 PX4_ALTCTL_MODE_ID
    # 모드 전환 확인 (QGC에서 'POSCTL' 또는 'ALTCTL'로 표시될 수 있습니다.)
    if not wait_for_mode_change(master, 'POSCTL', timeout_seconds=15) and \
            not wait_for_mode_change(master, 'ALTCTL', timeout_seconds=15):
        print("경고: 원하는 비행 모드로 전환하지 못했습니다. 수동으로 모드를 설정해주세요.")
        # 이 경우, 다음 단계로 진행하지 않거나 수동 개입을 요구할 수 있습니다.
        # 안전을 위해 여기서 프로그램을 종료할 수 있습니다.
        # exit() # 비행 모드 전환 실패 시 종료

    # 3. 드론 ARM
    if not arm_drone(master):
        print("드론 ARM 실패. 프로그램을 종료합니다.")
        exit()

    # 4. 이륙 명령
    takeoff_drone(master, TARGET_ALTITUDE_METERS)

    print(f"{HOVER_DURATION_SECONDS}초 호버링 완료.")

    # 5. 착륙 명령
    land_drone(master)

    # 6. 드론 Disarm (착륙 후 자동으로 Disarm되지 않았다면)
    # PX4는 착륙 후 자동으로 Disarm되는 경우가 많습니다.
    # 따라서 이 단계는 선택 사항이거나, 실제 Disarm 상태를 확인 후 수행할 수 있습니다.
    if master.motors_armed():  # 아직 ARM 상태라면 Disarm 시도
        disarm_drone(master)

except Exception as e:
    print(f"\n치명적인 오류 발생: {e}")
    # 비상 착륙 또는 Disarm 로직 추가
    if master.motors_armed():
        print("오류 발생으로 인한 비상 착륙 또는 Disarm 시도...")
        try:
            land_drone(master)  # 안전을 위해 착륙 명령 다시 시도
            disarm_drone(master)
        except Exception as err:
            print(f"비상 처리 중 오류 발생: {err}")
finally:
    print("드론 연결 종료.")
    master.close()
    print("프로그램 종료.")
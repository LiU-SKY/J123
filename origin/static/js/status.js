async function fetchDroneStatus() {
    try {
        const res = await fetch('/drones/status');
        if (!res.ok) throw new Error('드론 상태 로드 실패');
        const data = await res.json();  // [{drone_id, status}, ...]

        const list = document.getElementById('drone-status-list');
        list.innerHTML = '';  // 기존 목록 초기화

        data.forEach(drone => {
            const span = document.createElement('span');
            span.innerHTML = `
                ${drone.drone_id}
                <span class="status-dot ${drone.status === 'online' ? 'status-online' : 'status-offline'}"></span>
            `;
            list.appendChild(span);
        });
    } catch (err) {
        console.error('드론 상태 가져오기 오류:', err);
    }
}

// 3초마다 상태 갱신
setInterval(fetchDroneStatus, 3000);
fetchDroneStatus();  // 최초 1회 실행

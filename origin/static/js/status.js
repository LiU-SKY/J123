async function fetchDroneStatus() {
    try {
        const res = await fetch('/drones/status');
        if (!res.ok) throw new Error('드론 상태 로드 실패');

        const data = await res.json(); // 서버로부터 [{drone_id, status, last_seen}, ...] 받음
        const container = document.getElementById('drone-status-list');
        container.innerHTML = '';

        data.forEach(drone => {
            const span = document.createElement('span');
            span.innerHTML = `
                ${drone.drone_id}
                <span class="status-dot ${drone.status === 'online' ? 'status-online' : 'status-offline'}"></span>
            `;
            container.appendChild(span);
        });
    } catch (err) {
        console.error('드론 상태 오류:', err);
    }
}

setInterval(fetchDroneStatus, 3000);
fetchDroneStatus(); // 최초 1회

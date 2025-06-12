async function fetchDroneStatus() {
    try {
        const res = await fetch('/drones/status');
        if (!res.ok) throw new Error('드론 상태 로드 실패');

        const data = await res.json(); // [{ drone_id, status, last_seen }, ...]

        const list = document.getElementById('drone-status-list');
        list.innerHTML = '';

        data.forEach(drone => {
            // ✅ status 안전하게 검사
            const rawStatus = drone.status || "";
            const statusClass = rawStatus.trim().toLowerCase() === 'online' ? 'status-online' : 'status-offline';

            const span = document.createElement('span');
            span.innerHTML = `
                ${drone.drone_id}
                <span class="status-dot ${statusClass}"></span>
            `;
            list.appendChild(span);
        });
    } catch (err) {
        console.error('드론 상태 표시 중 오류 발생:', err);
    }
}

setInterval(fetchDroneStatus, 3000);
fetchDroneStatus();  // 최초 1회

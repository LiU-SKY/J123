async function fetchData() {
    const response = await fetch('/position');
    const data = await response.json();
    const list = document.getElementById('data-list');
    list.innerHTML = '';
    data.forEach(item => {
        const li = document.createElement('li');
        li.textContent = item;
        list.appendChild(li);
    });
}

// 처음 로딩 시 실행
fetchData();

// 3초마다 자동 생신
setInterval(fetchData, 3000);


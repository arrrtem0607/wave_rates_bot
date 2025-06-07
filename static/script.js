const form = document.getElementById('range-form');
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fromDate = document.getElementById('from_date').value;
    const toDate = document.getElementById('to_date').value;

    const params = new URLSearchParams();
    if (fromDate) params.append('from_date', fromDate);
    if (toDate) params.append('to_date', toDate);

    const resp = await fetch(`/rates?${params.toString()}`);
    if (!resp.ok) {
        alert('Не удалось загрузить данные');
        return;
    }
    const data = await resp.json();
    const tbody = document.getElementById('rates-table-body');
    tbody.innerHTML = '';
    data.forEach(r => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${r.date}</td>
            <td>${r.ust_rub.toFixed(2)}</td>
            <td>${r.cny_rub.toFixed(2)}</td>
            <td>${r.ust_rub_plus1.toFixed(2)}</td>
            <td>${r.cny_rub_plus2p.toFixed(2)}</td>`;
        tbody.appendChild(row);
    });
});

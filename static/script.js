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
        alert('Failed to load data');
        return;
    }
    const data = await resp.json();
    const tbody = document.getElementById('rates-table-body');
    tbody.innerHTML = '';
    data.forEach(r => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${r.date}</td>
            <td>${r.ust_rub}</td>
            <td>${r.cny_rub}</td>
            <td>${r.ust_rub_plus1}</td>
            <td>${r.cny_rub_plus2p}</td>`;
        tbody.appendChild(row);
    });
});

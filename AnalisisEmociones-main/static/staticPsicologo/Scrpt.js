const ctx = document.getElementById('resultsChart').getContext('2d');
const resultsChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio'],
        datasets: [{
            label: 'Resultados',
            data: [0.5, 0.8, 0.6, 0.9, 0.7, 1.0, 0.4],
            borderColor: 'rgba(255, 99, 132, 1)',
            backgroundColor: 'rgba(255, 99, 132, 0.2)',
            borderWidth: 1
        }]
    },
    options: {
        scales: {
            y: {
                beginAtZero: true
            }
        }
    }
});

function toggleTheme() {
    document.body.classList.toggle('dark-mode');
    
    // Cambia también las clases en los elementos específicos si es necesario
    document.querySelector('.sidebar').classList.toggle('dark-mode');
    document.querySelector('.main-content').classList.toggle('dark-mode');
    const table = document.querySelector('table');
    if (table) {
        table.classList.toggle('dark-mode');
    }
}
const labels = document.querySelectorAll('.form-control label')

labels.forEach(label => {
    label.innerHTML = label.innerText
        .split('')
        .map((letter, index) => `<span style="transition-delay:${ index * 25 }ms">${ letter }</span>`)
        .join('')
})


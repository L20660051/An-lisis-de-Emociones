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



// Datos ficticios de ansiedad en la escala de Hamilton
const datosAnsiedad = {
    labels: ['Leve', 'Moderada', 'Severa', 'Extrema'],
    datasets: [{
        label: 'Casos de Ansiedad',
        data: [12, 19, 7, 3], // Cantidades ficticias de casos
        backgroundColor: [
            'rgba(75, 192, 192, 0.2)',
            'rgba(54, 162, 235, 0.2)',
            'rgba(255, 206, 86, 0.2)',
            'rgba(255, 99, 132, 0.2)'
        ],
        borderColor: [
            'rgba(75, 192, 192, 1)',
            'rgba(54, 162, 235, 1)',
            'rgba(255, 206, 86, 1)',
            'rgba(255, 99, 132, 1)'
        ],
        borderWidth: 1
    }]
};

// Configuración de la gráfica
const config = {
    type: 'bar', // Tipo de gráfica (barras)
    data: datosAnsiedad,
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: {
                beginAtZero: true
            }
        }
    }
};

// Renderizar la gráfica en el canvas
const ctx = document.getElementById('ansiedadChart').getContext('2d');
new Chart(ctx, config);

//Testing

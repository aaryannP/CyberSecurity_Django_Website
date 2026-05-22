document.addEventListener('DOMContentLoaded', function() {
    
    // 1. Count-up Animation Logic
    const counters = document.querySelectorAll('.count-up');
    const speed = 200;

    counters.forEach(counter => {
        const animate = () => {
            const value = +counter.getAttribute('data-target');
            const data = +counter.innerText;
            const time = value / speed;

            if (data < value) {
                counter.innerText = Math.ceil(data + time);
                setTimeout(animate, 20);
            } else {
                counter.innerText = value;
            }
        }
        animate();
    });

    // 2. Chart.js Initialization
    const chartDataScript = document.getElementById('chart-data');
    if(chartDataScript) {
        const data = JSON.parse(chartDataScript.textContent);
        
        // Activity Chart (Bar)
        const ctxActivity = document.getElementById('activityChart').getContext('2d');
        new Chart(ctxActivity, {
            type: 'bar',
            data: {
                labels: data.actions.labels,
                datasets: [{
                    label: 'Event Count',
                    data: data.actions.data,
                    backgroundColor: [
                        'rgba(46, 204, 113, 0.6)', // Login - Green
                        'rgba(231, 76, 60, 0.6)',  // Failed - Red
                        'rgba(52, 152, 219, 0.6)'  // Logout - Blue
                    ],
                    borderColor: [
                        'rgba(46, 204, 113, 1)',
                        'rgba(231, 76, 60, 1)',
                        'rgba(52, 152, 219, 1)'
                    ],
                    borderWidth: 1,
                    borderRadius: 5
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: { 
                        beginAtZero: true,
                        ticks: { stepSize: 1, color: 'rgba(255, 255, 255, 0.7)' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                    },
                    x: {
                        ticks: { color: 'rgba(255, 255, 255, 0.7)' },
                        grid: { display: false }
                    }
                }
            }
        });

        // Risk Chart (Doughnut)
        const ctxRisk = document.getElementById('riskChart').getContext('2d');
        new Chart(ctxRisk, {
            type: 'doughnut',
            data: {
                labels: data.risk.labels,
                datasets: [{
                    data: data.risk.data,
                    backgroundColor: [
                        'rgba(46, 204, 113, 0.6)', // Safe
                        'rgba(231, 76, 60, 0.6)'   // Suspicious
                    ],
                    borderColor: [
                        'rgba(46, 204, 113, 1)',
                        'rgba(231, 76, 60, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { 
                        position: 'bottom',
                        labels: { color: 'rgba(255, 255, 255, 0.9)' }
                    }
                }
            }
        });
    }

});

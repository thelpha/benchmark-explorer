function updateActiveTab(selectedId) {
    const tabs = document.querySelectorAll('.tabs a');
    tabs.forEach(tab => tab.classList.remove('active'));
    document.getElementById(selectedId).classList.add('active');
}

function renderGraph(canvas_id, graph_data, show_title, title, show_legend, datasetName, metricName, task,type) {

    const data = graph_data
    const datasets = [];
    let lastMaxTimestamp = null;
    let lastMinTimestamp = null;

    Object.entries(data).forEach(([datasetName, datasetData]) => {
        Object.entries(datasetData).forEach(([metricName, metricArray]) => {
            const values = [];
            const localPaperURLs = [];
            const localPaperTitles = [];
            const localPaperModels = [];

            let currentMax = -Infinity;
            let currentMin = Infinity;
            let maxChangeCount = 0;
            let minChangeCount = 0;
            const maxLineData = [];
            const minLineData = [];

            metricArray.forEach(({ date, value, paper_url, paper_title, model_name }) => {
                values.push(value);
                localPaperURLs.push(paper_url);
                localPaperTitles.push(paper_title);
                localPaperModels.push(model_name)

                if (value > currentMax) {
                    currentMax = value;
                    if (date > lastMaxTimestamp){
                        maxChangeCount++;
                    }
                    lastMaxTimestamp = date;
                    
                }
            
                if (value < currentMin) {
                    currentMin = value;
                    if (date > lastMinTimestamp){
                        minChangeCount++;
                    }
                    lastMinTimestamp = date;
                    
                }
                maxLineData.push(currentMax);
                minLineData.push(currentMin);
            });

            datasets.push({
                label: `${datasetName} - ${metricName}`,
                data: values,
                paperURLs: localPaperURLs,
                paperTitles: localPaperTitles,
                paperModels: localPaperModels,
                tension: 0.4,
                borderColor: `rgba(${Math.random() * 255}, ${Math.random() * 255}, ${Math.random() * 255}, 1)`,
                borderWidth: 0,
                fill: false,
                pointRadius: 4,
                pointHoverBorderWidth: 2 // hover border width
            });

            if (type == 'max') {
                datasets.push({
                    label: `${datasetName} - ${metricName} (Max Line)`,
                    data: maxLineData,
                    tension: 0.1,
                    borderColor: 'LightSeaGreen',
                    borderWidth: 1.5,
                    fill: false,
                    pointRadius: 0,
                });
            } else {
                datasets.push({
                    label: `${datasetName} - ${metricName} (Min Line)`,
                    data: minLineData,
                    tension: 0.1,
                    borderColor: 'magenta',
                    borderWidth: 1.5,
                    fill: false,
                    pointRadius: 0,
                });
            }
        });
    });

    const labels = data[Object.keys(data)[0]][Object.keys(data[Object.keys(data)[0]])[0]].map(item => moment(item.date));

    const ctx = document.getElementById(canvas_id).getContext('2d');
    const chart = new Chart(ctx, {
        type: 'line',
        data: { labels, datasets },
        options: {
            scales: { x: { type: 'time', time: { unit: 'year', displayFormats: { day: 'YYYY' } }, grid: { display: false } }, y: { beginAtZero: true } },
            animation: { duration: 1000, easing: 'easeInOutQuad' },
            plugins: {
                title: { display: show_title, text: title },
                legend: { display: show_legend, position: 'right' },
                tooltip: {
                    callbacks: {
                        title: function (tooltipItem) {
                            const datasetIndex = tooltipItem[0].datasetIndex;
                            const index = tooltipItem[0].dataIndex;
                            const paperDate = moment(tooltipItem[0].parsed.x).format('YYYY-MM-DD');
                            return `Date: ${paperDate}\nTitle: ${chart.data.datasets[datasetIndex].paperTitles[index]}\nModel: ${chart.data.datasets[datasetIndex].paperModels[index]}`;
                        },
                        footer: function (tooltipItem) {
                            const datasetIndex = tooltipItem[0].datasetIndex;
                            const index = tooltipItem[0].dataIndex;
                            return `URL: ${chart.data.datasets[datasetIndex].paperURLs[index]}`;
                        },
                    },
                },
            },
            onClick: function (evt) {
                var element = chart.getElementsAtEventForMode(evt, 'nearest', { intersect: true }, true);
                if (element.length) {
                    var index = element[0].index;
                    var datasetIndex = element[0].datasetIndex;
                    var paperURL = chart.data.datasets[datasetIndex].paperURLs[index];
                    window.open(paperURL, '_blank');
                }
            }
        },
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const container = document.querySelector('.chart-container');

    document.getElementById('sortRecent').addEventListener('click', function() {
        const divs = Array.from(container.querySelectorAll('.chart-wrapper'));
        divs.sort((a, b) => new Date(b.getAttribute('data-last_date')) - new Date(a.getAttribute('data-last_date')));
        divs.forEach((div, index) => {
            div.style.order = index;
        });
        updateActiveTab('sortRecent');

    });

    document.getElementById('sortInteresting').addEventListener('click', function() {
        const divs = Array.from(container.querySelectorAll('.chart-wrapper'));
        divs.sort((a, b) => {
            const lastChangeA = parseFloat(a.getAttribute('data-last_change'));
            const lastChangeB = parseFloat(b.getAttribute('data-last_change'));
            const lastDateA = new Date(a.getAttribute('data-last_date'));
            const lastDateB = new Date(b.getAttribute('data-last_date'));
            const today = new Date();
            const daysOldA = (today - lastDateA) / (1000 * 3600 * 24);
            const daysOldB = (today - lastDateB) / (1000 * 3600 * 24);
            const ratioA = lastChangeA / daysOldA;
            const ratioB = lastChangeB / daysOldB;
            return ratioB - ratioA;
        });
        divs.forEach((div, index) => {
            div.style.order = index;
        });
        updateActiveTab('sortInteresting');

    });
});
let mainChartInstance, detailedChartInstance;
let hourlyDataGlobal = [], dailySummariesGlobal = [], globalHeatwaveInfo = {};

function formatTimestamp(ts) {
  const d = new Date(ts * 1000);
  return `${d.getMonth()+1}/${d.getDate()} ${d.getHours()}:00`;
}

document.getElementById("forecast-form")
  .addEventListener("submit", e => {
    e.preventDefault();

    // strip degree symbol
    const lat = document.getElementById("latitude").value.replace(/[^0-9.\-+]/g, "");
    const lon = document.getElementById("longitude").value.replace(/[^0-9.\-+]/g, "");

    fetch(`${API_BASE}/forecast`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ latitude: lat, longitude: lon })
    })
    .then(res => res.json())
    .then(data => {
      if (data.error) {
        return document.getElementById("summaryTableContainer").innerText = data.error;
      }
      // store for detailed drill-down
      hourlyDataGlobal = data.forecast.hourly || [];
      dailySummariesGlobal = data.summaries.daily || [];
      globalHeatwaveInfo = data.summaries.heatwave || {};

      // MAIN HOURLY CHART
      if (mainChartInstance) mainChartInstance.destroy();
      const labels = hourlyDataGlobal.map(h => formatTimestamp(h.dt));
      const temps  = hourlyDataGlobal.map(h => h.temp);
      const hw     = hourlyDataGlobal.map(h =>
        (globalHeatwaveInfo.is_heatwave &&
         h.dt >= globalHeatwaveInfo.start_date &&
         h.dt <= globalHeatwaveInfo.end_date) ? 1 : 0
      );
      const ctx = document.getElementById("mainChart").getContext("2d");
      mainChartInstance = new Chart(ctx, {
        type: "line",
        data: { labels, datasets: [
          { label: "Temp (°C)", data: temps, borderColor: "orange", fill: false, yAxisID: "y1" },
          { label: "Heatwave", data: hw, borderColor: "red", stepped: true, fill: false, yAxisID: "y2" }
        ]},
        options: {
          scales: {
            y1: { type:"linear", position:"left", title:{display:true,text:"°C"} },
            y2: { type:"linear", position:"right", min:0, max:1, ticks:{display:false} }
          },
          plugins: { title:{display:true,text:"Hourly Temp & Heatwave"} }
        }
      });

      // DAILY SUMMARY TABLE
      let html = `<table border="1" style="width:100%;border-collapse:collapse;">
                    <thead><tr>
                      <th>Date</th><th>Min</th><th>Max</th><th>Cond</th><th>HW</th>
                    </tr></thead><tbody>`;
      dailySummariesGlobal.forEach(day => {
        html += `<tr data-date="${new Date(day.date*1000).toISOString().slice(0,10)}">
                   <td>${new Date(day.date*1000).toLocaleDateString()}</td>
                   <td>${day.min_temp}</td>
                   <td>${day.max_temp}</td>
                   <td>${day.weather}</td>
                   <td>${day.heatwave}</td>
                 </tr>`;
      });
      document.getElementById("summaryTableContainer").innerHTML = html + `</tbody></table>`;

      // CLICK ROW → DETAILED CHART
      document.querySelectorAll("#summaryTableContainer tr[data-date]")
        .forEach(r => r.onclick = () => showDetailedChart(r.dataset.date));

      // HEATWAVE INFO
      const infoDiv = document.getElementById("heatwaveInfo");
      infoDiv.innerText = globalHeatwaveInfo.is_heatwave
        ? globalHeatwaveInfo.message
        : globalHeatwaveInfo.message || "No heatwave.";

    })
    .catch(err => {
      console.error(err);
      document.getElementById("summaryTableContainer").innerText = "Fetch error: " + err;
    });
});

function showDetailedChart(date) {
  const dayData = hourlyDataGlobal.filter(h =>
    new Date(h.dt*1000).toISOString().slice(0,10) === date
  );
  if (!dayData.length) return alert("No hourly data for " + date);

  if (detailedChartInstance) detailedChartInstance.destroy();
  const labels = dayData.map(h => new Date(h.dt*1000).getHours()+":00");
  const temps  = dayData.map(h => h.temp);
  const hw     = dayData.map(h =>
    (globalHeatwaveInfo.is_heatwave &&
     h.dt >= globalHeatwaveInfo.start_date &&
     h.dt <= globalHeatwaveInfo.end_date) ? 1 : 0
  );
  document.getElementById("detailedChartContainer").style.display = "block";
  document.getElementById("detailedChartTitle").innerText = "Hourly for " + date;
  const ctx2 = document.getElementById("detailedChart").getContext("2d");
  detailedChartInstance = new Chart(ctx2, {
    type: "line",
    data: { labels, datasets: [
      { label:"Temp (°C)", data:temps, borderColor:"orange", fill:false, yAxisID:"y1" },
      { label:"Heatwave", data:hw, borderColor:"red", stepped:true, fill:false, yAxisID:"y2" }
    ]},
    options: {
      scales: {
        y1:{ position:"left", title:{display:true,text:"°C"} },
        y2:{ display:false, min:0, max:1 }
      },
      plugins:{ title:{display:true,text:"Details "+date} }
    }
  });
}

document.getElementById("closeDetailedChart").onclick = () => {
  document.getElementById("detailedChartContainer").style.display = "none";
};

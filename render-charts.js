for (const node of Array.from(document.querySelectorAll('script.chart'))) {
  const div = document.createElement('div')
  node.after(div)

  const rawData = JSON.parse(node.textContent)
  const data = [
    {
      type: 'bar',
      x: rawData.map(d => d[0]),
      y: rawData.map(d => d[1])
    }
  ]
  Plotly.newPlot(div, data)
}

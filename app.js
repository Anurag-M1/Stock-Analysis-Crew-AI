const form = document.getElementById("analyze-form");
const tickerInput = document.getElementById("ticker");
const statusEl = document.getElementById("status");
const reportEl = document.getElementById("report");
const button = document.getElementById("analyze-btn");

async function runAnalysis(ticker) {
  const url = `/api/analyze?ticker=${encodeURIComponent(ticker)}`;
  const response = await fetch(url);
  const data = await response.json();

  if (!response.ok || !data.ok) {
    throw new Error(data.error || `Request failed (${response.status})`);
  }
  return data.report || "No report returned.";
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const ticker = tickerInput.value.trim().toUpperCase();
  if (!ticker) return;

  button.disabled = true;
  statusEl.textContent = `Running analysis for ${ticker}...`;
  reportEl.textContent = "Please wait...";

  try {
    const report = await runAnalysis(ticker);
    statusEl.textContent = `Completed for ${ticker}.`;
    reportEl.textContent = report;
  } catch (error) {
    statusEl.textContent = "Request failed.";
    reportEl.textContent = `Error: ${error.message}`;
  } finally {
    button.disabled = false;
  }
});

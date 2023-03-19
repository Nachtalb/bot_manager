const apiUrl = "http://" + window.location.host; // Replace with your FastAPI server address

async function fetchData(url, { method = "GET", query = {} } = {}) {
  // Add query parameters to the URL
  const searchParams = new URLSearchParams(query);
  const urlWithQuery = new URL(url);
  urlWithQuery.search = searchParams.toString();

  // Fetch data from the URL with query parameters
  try {
    const response = await fetch(urlWithQuery, { method: method });
    const data = await response.json();
    return data;
  } catch (error) {
    console.error(error);
    displayLogEntry({
      text: "Error fetching data",
      status: "error",
      timestamp: Math.floor(Date.now() / 1000),
    });
  }
}

function displayLogEntry({ text, status, timestamp } = {}) {
  const logHistory = document.getElementById("log-history-entries");
  var isScrolledToBottom =
    logHistory.scrollHeight - logHistory.clientHeight <=
    logHistory.scrollTop + 1;
  // Create a new log entry element
  const logEntry = document.createElement("div");
  logEntry.classList.add("log-entry");

  // Add a class based on the status
  if (status === "success") {
    logEntry.classList.add("log-success");
  } else if (status === "error") {
    logEntry.classList.add("log-error");
  } else if (status === "info") {
    logEntry.classList.add("log-info");
  }

  // Convert the timestamp to a readable datetime
  const date = new Date(timestamp * 1000);
  const datetime = date.toISOString();

  // Set the log entry content
  logEntry.textContent = `[${datetime}] ${status.toUpperCase()}: ${text}`;

  logHistory.appendChild(logEntry);
  if (isScrolledToBottom) {
    logHistory.scrollTop = logHistory.scrollHeight;
  }
}

function currentTimestamp() {
  return Math.floor(Date.now() / 1000);
}

async function fetchAndDisplayLogEntries(since) {
  // Fetch log entries since the current timestamp
  const logsUrl = apiUrl + "/logs";

  const options = since ? { query: { since: since } } : {};
  const logs = (await fetchData(logsUrl, options)).logs;

  // Display the fetched log entries using the displayLogEntry function
  logs.forEach((logEntry) => {
    displayLogEntry(logEntry);
  });
}

// Modify the loadApplicationsList function
async function loadApplicationsList() {
  const applications = await fetchData(`${apiUrl}/list`);
  const tbody = document.getElementById("applications-tbody");

  // Clear the existing table content
  tbody.innerHTML = "";

  // Fill the table with the list of applications
  for (const app of applications.applications) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="align-middle col-id">${app.id}</td>
      <td class="align-middle col-telegram"><a href="${
        app.bot.link
      }" target="_blank">@${app.bot.username}</a></td>
      <td class="align-middle col-telegram-token">${app.telegram_token}</td>
      <td class="align-middle col-running">${app.running ? "✅" : "❌"}</td>
      <td class="align-middle col-actions d-flex justify-content-between">
          <button ${
            app.running ? "disabled" : ""
          } class="btn btn-success action-start-app" onclick="startApp('${
      app.id
    }')"><i class="bi bi-play"></i> Start</button>
          <button class="btn btn-primary action-restart-app" onclick="restartApp('${
            app.id
          }')"><i class="bi bi-arrow-clockwise"></i> Restart</button>
          <button class="btn btn-info action-reload-app" onclick="reloadApp('${
            app.id
          }')"><i class="bi bi-arrow-repeat"></i> Reload</button>
          <button ${
            !app.running ? "disabled" : ""
          } class="btn btn-warning action-stop-app" onclick="stopApp('${
      app.id
    }')"><i class="bi bi-stop"></i> Stop</button>
      </td>
    `;
    tbody.appendChild(tr);
  }
}

async function startApp(appId) {
  let ts = currentTimestamp();
  await fetchData(`${apiUrl}/start_app/${appId}`, {
    method: "POST",
  });
  fetchAndDisplayLogEntries(ts);
  loadApplicationsList();
}

async function restartApp(appId) {
  let ts = currentTimestamp();
  await fetchData(`${apiUrl}/restart_app/${appId}`, {
    method: "POST",
  });
  fetchAndDisplayLogEntries(ts);
  loadApplicationsList();
}

async function reloadApp(appId) {
  let ts = currentTimestamp();
  await fetchData(`${apiUrl}/reload_app/${appId}`, {
    method: "POST",
  });
  fetchAndDisplayLogEntries(ts);
  loadApplicationsList();
}

async function stopApp(appId) {
  let ts = currentTimestamp();
  await fetchData(`${apiUrl}/stop_app/${appId}`, {
    method: "POST",
  });
  fetchAndDisplayLogEntries(ts);
  loadApplicationsList();
}

async function shutdown() {
  await fetchData(`${apiUrl}/shutdown`);
}

async function reloadConfig() {
  let ts = currentTimestamp();
  await fetchData(`${apiUrl}/reload_config`);
  fetchAndDisplayLogEntries(ts);
  loadApplicationsList();
}

async function startAll() {
  let ts = currentTimestamp();
  await fetchData(`${apiUrl}/start_all`);
  fetchAndDisplayLogEntries(ts);
  loadApplicationsList();
}

async function stopAll() {
  let ts = currentTimestamp();
  await fetchData(`${apiUrl}/stop_all`);
  fetchAndDisplayLogEntries(ts);
  loadApplicationsList();
}

// Call the loadApplicationsList function when the page loads
loadApplicationsList();
fetchAndDisplayLogEntries();
setInterval(loadApplicationsList, 5000);

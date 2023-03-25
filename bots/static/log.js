const logHistory = document.getElementById("log-history-entries");

// Auto scroll log history
const serverLogsShown = document.getElementById("serverLogsShown");
serverLogsShown.addEventListener("change", () => {
  logHistory.scrollTop = logHistory.scrollHeight;
});

// Add log to log history
export function displayLogEntry(namespace, event, status, message) {
  var isScrolledToBottom = logHistory.scrollHeight - logHistory.clientHeight <= logHistory.scrollTop + 1;

  // Create a new log entry element
  const logEntry = document.createElement("div");
  logEntry.classList.add("log-entry");

  // Add a class based on the status
  if (status === "success") {
    logEntry.classList.add("log-success");
  } else if (status === "error") {
    logEntry.classList.add("log-error");
  } else if (status === "warning") {
    logEntry.classList.add("log-warning");
  } else if (status === "info") {
    logEntry.classList.add("log-info");
  }

  // Set the log entry content
  logEntry.textContent = `[${namespace}/${event}] Status: ${status.toUpperCase()}, Message: ${message}`;
  logEntry.classList.add("log-ns-" + namespace.substring(1));

  logHistory.appendChild(logEntry);
  if (isScrolledToBottom) {
    logHistory.scrollTop = logHistory.scrollHeight;
  }
}

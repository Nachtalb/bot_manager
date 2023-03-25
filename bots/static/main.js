class AppManager {
  constructor() {
    this.apps = [];
  }

  updateApps(newApps) {
    this.apps = newApps;
    this.fillTable();
  }

  updateAppById(id, updatedApp) {
    const appIndex = this.apps.findIndex((app) => app.id === id);

    if (appIndex !== -1) {
      this.apps[appIndex] = updatedApp;
      this.fillTable(updatedApp);
    } else {
      console.error(`App with id '${id}' not found`);
    }
  }

  getAppById(id) {
    return this.apps.find((app) => app.id === id);
  }

  async fillTable(updatedApp) {
    const tbody = document.getElementById("applications-tbody");

    if (!updatedApp) {
      // Clear the existing table content
      tbody.innerHTML = "";
    }

    // Fill the table with the list of applications or update a single row
    for (const app of this.apps) {
      if (updatedApp && app.id !== updatedApp.id) {
        continue;
      }

      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td class="align-middle col-id">${app.id}</td>
        <td class="align-middle col-telegram">
          <a href="${app.bot.link}" target="_blank">@${app.bot.username}</a>
        </td>
        <td class="align-middle col-telegram-token">${app.telegram_token}</td>
        <td class="align-middle col-running">${app.running ? "✅" : "❌"}</td>
        <td class="align-middle col-actions d-flex justify-content-between">
            <button
              ${app.running ? "disabled" : ""}
              class="btn btn-success action-start-app"
              onclick="apiSocket.emit('app_start', {appId: '${app.id}'})">
              <i class="bi bi-play"></i> Start
            </button>
            <button class="btn btn-primary action-restart-app" onclick="apiSocket.emit('app_restart', {appId: '${
              app.id
            }'})">
              <i class="bi bi-arrow-clockwise"></i> Restart
            </button>
            <button class="btn btn-info action-reload-app" onclick="apiSocket.emit('app_reload', {appId: '${app.id}'})">
              <i class="bi bi-arrow-repeat"></i> Reload
            </button>
            <button
              ${!app.running ? "disabled" : ""}
              class="btn btn-warning action-stop-app"
              onclick="apiSocket.emit('app_stop', {appId: '${app.id}'})">
              <i class="bi bi-stop"></i> Stop
            </button>
            <button
              class="btn btn-secondary action-stop-app"
              data-bs-toggle="modal"
              data-bs-target="#editAppConfigModal"
              data-bs-app-id="${app.id}">
                <i class="bi bi-pencil-square"></i> Edit Config
            </button>
        </td>
      `;

      tr.setAttribute("data-app-id", app.id);

      if (updatedApp) {
        const existingRow = tbody.querySelector(`tr[data-app-id="${app.id}"]`);
        if (existingRow) {
          tbody.replaceChild(tr, existingRow);
        } else {
          tbody.appendChild(tr);
        }
      } else {
        tbody.appendChild(tr);
      }
    }
  }
}

// Usage example:
const appManager = new AppManager();
const serverSocket = io(`ws://${window.location.host}/server`, {path: "/ws/socket.io"});
const apiSocket = io(`ws://${window.location.host}/api`, {path: "/ws/socket.io"});
const logHistory = document.getElementById("log-history-entries");

function displayLogEntry(namespace, event, status, message) {
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

apiSocket.onAny((eventName, response) => {
  if (response.message !== null && response.message !== undefined) {
    displayLogEntry("/api", eventName, response.status, response.message);
  }

  if (response.status === "success") {
    if (response.data.app_update !== undefined) {
      appManager.updateAppById(response.data.app_update.id, response.data.app_update);
    } else if (response.data.apps_update !== undefined) {
      appManager.updateApps(response.data.apps_update)
    }

  }
});

serverSocket.onAny((eventName, response) => {
  if (response.message !== null && response.message !== undefined) {
    displayLogEntry("/server", eventName, response.status, response.message);
  }
});

const editAppConfig = document.getElementById("editAppConfigModal");
const editAppConfigAppId = editAppConfig.querySelector("#editAppConfigAppId");
const editAppConfigType = editAppConfig.querySelector("#editAppConfigType");
const editAppConfigFieldsTable = editAppConfig.querySelector("#editAppConfigFields tbody");
const editAppConfigConfig = editAppConfig.querySelector("#editAppConfigConfigInput");
const editAppConfigSave = editAppConfig.querySelector("#editAppConfigSave");

const editAppConfigModal = new bootstrap.Modal(editAppConfig);

function postErrorInEditConfigModal(message, type) {
  editAppConfig.querySelector("#editAppConfigErrors").innerHTML = [
    `<div class="alert alert-${type} alert-dismissible" role="alert">`,
    `   <div>${message}</div>`,
    '   <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>',
    "</div>",
  ].join("");
}

apiSocket.on("app_edit", (response) => {
  if (response.status !== "success") {
    return postErrorInEditConfigModal(response.message, response.status === "error" ? "danger" : "warning");
  }
  editAppConfigModal.hide();
});

editAppConfigSave.addEventListener("click", async () => {
  try {
    apiSocket.emit("app_edit", {appId: editAppConfigAppId.value, config: JSON.parse(editAppConfigConfig.value)});
  } catch (error) {
    return postErrorInEditConfigModal(`Invalid JSON: ${error}`, "danger");
  }
});

editAppConfig.addEventListener("show.bs.modal", async (event) => {
  editAppConfig.querySelector("#editAppConfigErrors").innerHTML = "";

  // Button that triggered the modal
  const button = event.relatedTarget;

  // Extract info from data-bs-* attributes
  const appId = button.getAttribute("data-bs-app-id");

  const app = appManager.getAppById(appId);

  // Update the modal's content.
  const modalTitle = editAppConfig.querySelector(".modal-title");
  modalTitle.textContent = `Edit config for @${app.bot.username}`;

  editAppConfigAppId.value = app.id;
  editAppConfigType.value = app.type;

  if (Object.keys(app.fields).length === 0) {
    // No config
    editAppConfig.classList.add("no-config");
  } else {
    editAppConfig.classList.remove("no-config");

    editAppConfigFieldsTable.innerHTML = "";
    for (const key in app.fields) {
      if (app.fields.hasOwnProperty(key)) {
        const item = app.fields[key];
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${key}</td>
          <td>${item.type}</td>
          <td>${item.default}</td>
          <td>${item.required ? "✅" : "❌"}</td>
        `;
        editAppConfigFieldsTable.appendChild(tr);
      }
    }

    editAppConfigConfig.value = JSON.stringify(app.config, null, 4);
  }
});

const serverLogsShown = document.getElementById("serverLogsShown");
serverLogsShown.addEventListener("change", () => {
  logHistory.scrollTop = logHistory.scrollHeight;
});

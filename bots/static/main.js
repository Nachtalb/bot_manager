import AppManager from "./appManager.js";
import { displayLogEntry } from "./log.js";

// Usage example:
const appManager = new AppManager();

const serverSocket = io(`ws://${window.location.host}/server`, { path: "/ws/socket.io" });
window.serverSocket = serverSocket;
const apiSocket = io(`ws://${window.location.host}/api`, { path: "/ws/socket.io" });
window.apiSocket = apiSocket;

// On any API endpoint message
apiSocket.onAny((eventName, response) => {
  if (response.message !== null && response.message !== undefined) {
    displayLogEntry("/api", eventName, response.status, response.message);
  }

  if (response.status === "success") {
    if (response.data.app_update !== undefined) {
      appManager.updateAppById(response.data.app_update.id, response.data.app_update);
    } else if (response.data.apps_update !== undefined) {
      appManager.updateApps(response.data.apps_update);
    }
  }
});

// On any Server endpoint message
serverSocket.onAny((eventName, response) => {
  if (response.message !== null && response.message !== undefined) {
    displayLogEntry("/server", eventName, response.status, response.message);
  }
});

// Post error to modal
export function postErrorIn(element, message, type) {
  element.innerHTML = [
    `<div class="alert alert-${type} alert-dismissible" role="alert">`,
    `   <div>${message}</div>`,
    '   <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>',
    "</div>",
  ].join("");
}

// Show schema modal
const schemaModel = document.getElementById("schemaModel");
const schemaModelErrors = schemaModel.querySelector("#schemaModelErrors");
const schemaModelAppId = schemaModel.querySelector("#schemaModelAppId");
const schemaModelAppType = schemaModel.querySelector("#schemaModelAppType");
const schemaModelSchemaInput = schemaModel.querySelector("#schemaModelSchemaInput");
const schemaModelBack = schemaModel.querySelectorAll(".edit-app-config-toggle");

schemaModel.addEventListener("show.bs.modal", async (event) => {
  schemaModelSchemaInput.value = "Loading...";

  schemaModelErrors.innerHTML = "";

  const appId = event.relatedTarget.getAttribute("data-bs-app-id");
  const app = appManager.getAppById(appId);

  schemaModel.querySelector(".modal-title").textContent = `Config Schema for @${app.bot.username}`;

  schemaModelAppId.value = app.id;
  schemaModelAppType.value = app.type;

  apiSocket.emit("app_schema", { appId: app.id });

  schemaModelBack.forEach((element) => {
    element.setAttribute("data-bs-app-id", app.id);
  });
});

apiSocket.on("app_schema", (response) => {
  if (response.status !== "success") {
    return postErrorIn(schemaModelErrors, response.message, response.status === "error" ? "danger" : "warning");
  }
  schemaModelSchemaInput.value = JSON.stringify(response.data.schema, null, 2);
});

// Show edit app config modal
const editAppConfig = document.getElementById("editAppConfigModal");
const editAppConfigErrors = editAppConfig.querySelector("#editAppConfigErrors");
const editAppConfigAppId = editAppConfig.querySelector("#editAppConfigAppId");
const editAppConfigType = editAppConfig.querySelector("#editAppConfigType");
const editAppConfigFieldsTable = editAppConfig.querySelector("#editAppConfigFields tbody");
const editAppConfigConfig = editAppConfig.querySelector("#editAppConfigConfigInput");
const editAppConfigShowSchema = editAppConfig.querySelector("#editAppConfigShowSchema");
const editAppConfigSave = editAppConfig.querySelector("#editAppConfigSave");

const editAppConfigModal = new bootstrap.Modal(editAppConfig);

editAppConfig.addEventListener("show.bs.modal", async (event) => {
  editAppConfigErrors.innerHTML = "";

  const appId = event.relatedTarget.getAttribute("data-bs-app-id");
  const app = appManager.getAppById(appId);

  editAppConfig.querySelector(".modal-title").textContent = `Edit config for @${app.bot.username}`;

  editAppConfigAppId.value = app.id;
  editAppConfigType.value = app.type;
  editAppConfigShowSchema.setAttribute("data-bs-app-id", app.id);

  if (Object.keys(app.fields).length === 0) {
    editAppConfig.classList.add("no-config");
  } else {
    editAppConfig.classList.remove("no-config");

    editAppConfigFieldsTable.innerHTML = "";
    for (const key in app.fields) {
      if (app.fields.hasOwnProperty(key)) {
        const item = app.fields[key];
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${item.required ? "✅" : "❌"}</td>
          <td>${key}</td>
          <td>${item.type}</td>
          <td>${item.help || "Not provided"}</td>
          <td class="text-break"><code>${item.default}</code></td>
          <td class="text-break"><code>${item.current}</code></td>
        `;
        editAppConfigFieldsTable.appendChild(tr);
      }
    }

    editAppConfigConfig.value = JSON.stringify(app.config, null, 4);
  }
});

apiSocket.on("app_edit", (response) => {
  if (response.status !== "success") {
    return postErrorIn(editAppConfigErrors, response.message, response.status === "error" ? "danger" : "warning");
  }
  editAppConfigModal.hide();
});

editAppConfigSave.addEventListener("click", async () => {
  try {
    apiSocket.emit("app_edit", { appId: editAppConfigAppId.value, config: JSON.parse(editAppConfigConfig.value) });
  } catch (error) {
    return postErrorIn(editAppConfigErrors, `Invalid JSON: ${error}`, "danger");
  }
});

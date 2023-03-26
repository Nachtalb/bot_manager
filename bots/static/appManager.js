export default class AppManager {
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
        <td class="align-middle col-started">${app.running ? "✅" : "❌"}</td>
        <td class="align-middle col-actions">
          <div class="d-flex g-3">
            <button
              ${app.running ? "disabled" : ""}
              class="btn me-2 text-nowrap btn-success action-start-app"
              onclick="apiSocket.emit('app_start', {appId: '${app.id}'})">
              <i class="bi bi-play"></i> Start
            </button>
            <button
              class="btn me-2 text-nowrap btn-info action-reload-app"
              onclick="apiSocket.emit('app_reload', {appId: '${app.id}'})">
              <i class="bi bi-arrow-repeat"></i> Reload
            </button>
            <button
              ${!app.running ? "disabled" : ""}
              class="btn me-2 text-nowrap btn-warning action-pause-app"
              onclick="apiSocket.emit('app_pause', {appId: '${app.id}'})">
              <i class="bi bi-pause"></i> Pause
            </button>
            <button
              class="btn text-nowrap btn-secondary action-pause-app"
              data-bs-toggle="modal"
              data-bs-target="#editAppConfigModal"
              data-bs-app-id="${app.id}">
                <i class="bi bi-pencil-square"></i> Edit Config
            </button>
          </div>
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

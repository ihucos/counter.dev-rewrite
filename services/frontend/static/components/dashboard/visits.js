customElements.define(
    tagName(),
    class extends HTMLElement {
        draw(logs) {
            // The backend sends parsed log entries:
            // [{date, time, country, referrer, device, platform, ...}, ...]
            var parsedLogs = logs || [];
            this.innerHTML = `
        <div class="metrics-four-item">
          <div class="metrics-headline">
            <img src="/img/visit.svg" width="24" height="24" alt="Visits">
            <h3 class="ml16">Visits</h3>
          </div>
          <div class="metrics-three-data bg-white radius-lg shadow-sm">
            <div class="metrics-three-data-headline shadow-sm caption gray">
              <span class="visits-date">Date</span>
              <span class="visits-time">Time</span>
              <span class="visits-ip"></span>
              <span class="visits-device"></span>
              <span class="visits-platform"></span>
              <span class="visits-referrer">Referrer</span>
            </div>
            <div class="metrics-three-data-content caption" data-simplebar data-simplebar-auto-hide="false">
              ${parsedLogs
                  .map(
                      (logEntry) => `
                <div class="hour-item">
                  <span class="visits-date">${escapeHtml(logEntry.date)}</span>
                  <span class="visits-time caption-strong">${escapeHtml(logEntry.time)}</span>
                  <img class="visits-ip" title="${escapeHtml(logEntry.country)}" src="/img/famfamfam_flags/gif/${escapeHtml(logEntry.country || "xx")}.gif" width="16" height="11" alt="${escapeHtml(logEntry.country)}">
                  <img class="visits-device" title="${escapeHtml(logEntry.device)}" src="/img/visits/devices/${escapeHtml((logEntry.device || "unknown").toLowerCase())}.svg"></img>
                  <img class="visits-platform" title="${escapeHtml(logEntry.platform)}" src="/img/visits/platforms/${escapeHtml((logEntry.platform || "unknown").toLowerCase())}.svg"></img>
                  <span class="visits-referrer">${this.referrerHtml(logEntry.referrer)}</span>
                </div>`,
                  )
                  .join("")}

            </div>
            <div class="metrics-three-data-footer bg-white"></div>
          </div>
        </div>`;
        }

        referrerHtml(referrer) {
            if (!referrer) {
                return "-";
            }
            try {
                var url = new URL(referrer);
            } catch (err) {
                return "?";
            }
            return `<a target="_blank" class="visits-referrer black" href="${escapeHtml(referrer)}">${escapeHtml(url.host)}</a>`;
        }
    },
);
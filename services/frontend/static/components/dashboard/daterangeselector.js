customElements.define(
    tagName(),
    class extends HTMLElement {
        draw(oldestArchiveDate, isDemo) {
            this.style.display = "none";
            this.innerHTML = `
                  <div class="modal-header">
                    <img
                      src="/img/calendar.svg"
                      width="24"
                      height="24"
                      alt="Edit account"
                    />
                    <h3 class="ml16">Custom date range...</h3>
                    <a href="#" class="btn-close" rel="modal:close"></a>
                  </div>
                  <div class="modal-content" style="text-align: center;">
                    <form action="" method="GET">
                      <div>
                          <input type="text" name="from" style="display: none"/>
                          <input type="text" name="to" style="display: none" />
                      </div>

                      <div>
                        <div class="caption gray" style="text-align: left">
                            <b>Note</b>: currently it is not possible to select today or yesterdays date. This will change in the future.
                        </div>

                        <div class="account-btn-group flex mt24 mb32">
                          <a href="#" class="btn-secondary full mr16" rel="modal:close">
                            Cancel
                          </a>
                          <button type="submit" class="btn-primary full">Ok</button>
                        </div>
                      </div>

                    </form>
                  </div>`;

            this.querySelector("form").setAttribute("action", "");
            this.fromInputEl = this.querySelector('input[name="from"]');
            this.toInputEl = this.querySelector('input[name="to"]');

            this.picker = new easepick.create({
                element: this.querySelector('input[name="from"]'),
                css: ["https://cdn.jsdelivr.net/npm/@easepick/bundle@1.2.0/dist/index.css", "https://cdn.jsdelivr.net/npm/@easepick/lock_plugin@1.2.0/dist/index.css", "/css/daterangepicker.css"],
                plugins: ["RangePlugin", "AmpPlugin", "LockPlugin"],
                RangePlugin: {
                    elementEnd: this.querySelector('input[name="to"]'),
                    tooltip: true,
                },
                AmpPlugin: {},
                LockPlugin: {
                    minDate: oldestArchiveDate,
                    maxDate: moment().subtract(2, "days").format("YYYY-MM-DD"),
                },
                inline: true,
                //calendars: 2,
                //grid: 2
            });

            this.picker.on("select", () => {
                this.querySelector('form button[type="submit"]').removeAttribute("disabled");
            });

            // Announce the picked range; dashboard.js fetches /query for it and
// redraws, the selector renames its range option.
            this.querySelector("form").onsubmit = (evt) => {
                evt.preventDefault();
                let detail = {
                    from: moment(this.fromInputEl.value),
                    to: moment(this.toInputEl.value),
                };
                document.dispatchEvent(new CustomEvent("selector-daterange-fetched", { detail: detail }));
                this.closeSuccess = true;
                closeModal();
            };

            document.addEventListener("selector-daterange-fetch", (evt) => {
                this.popup();
            });

            this.addEventListener("modal-after-close", () => {
                if (!this.closeSuccess) {
                    // select anything that is not the invalid "daterangesel" val
                    var rangeSelect = document.getElementById("range-select");
                    rangeSelect.value = "all";
                    rangeSelect.dispatchEvent(new Event("change"));
                }
                this.closeSuccess = false;
            });
        }

        popup() {
            // reset states
            this.querySelector('form button[type="submit"]').setAttribute("disabled", "disabled");
            this.picker.clear();

            openModal(this);
        }
    },
);

customElements.define(
    tagName(),
    class extends HTMLElement {
        // The id embedded in the tracking code is the account username: the
        // tracker buckets visits under the given data-id, sync.py maps it
        // back to the account and the dashboard reads the visit logs under
        // log:<site>:<username>.
        getTrackingCode(id, utcoffset) {
            if (String(id).includes('"') || String(utcoffset).includes('"')) {
                console.log("Sanity input validation test failed");
                return "error, contact support";
            }
            return `<script src="https://cdn.counter.dev/script.js" data-id="${id}" data-utcoffset="${utcoffset}"></script>`;
        }

        draw(id, utcoffset) {
            this.style.display = "block";
            var randId = "tracking-" + Math.floor(Math.random() * 1000000 + 1);
            this.innerHTML = `
                  <div class="tracking-code mb8">
                    <input
                      type="text"
                      id="${randId}"
                      class="full"
                      value='${this.getTrackingCode(id, utcoffset)}'
                      readonly
                    />
                    <button
                      class="btn-primary btn-copy ml16"
                      data-clipboard-target="#${randId}"
                    >
                      Copy
                    </button>
                  </div>
                  <span class="caption gray"
                    >Inside the
                    <span class="caption-strong">&lt;head&gt;</span> section</span
                  >`;
            new ClipboardJS(this.querySelector(".btn-copy"));
        }
    },
);

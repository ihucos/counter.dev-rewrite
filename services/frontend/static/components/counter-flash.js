customElements.define(
    tagName(),
    class extends HTMLElement {
        KEY = "close-invest";
        connectedCallback() {
            if (false) {
                this.innerHTML += `
                   <!-- Notification -->
                   <section class="notification">
                     <div class="content">
                       <span>Invest in Counter. <a href="/invest.html">Learn more.</a></span>
                       <div class="btn-close"></div>
                     </div>
                   </section>`;

                this.querySelector(".btn-close").onclick = () => {
                    this.remove();
                    localStorage.setItem(this.KEY, "yes");
                };
            }
        }
    },
);

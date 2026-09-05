// Not signed in (the /me endpoint answered 401) means the setup page is
// only reachable for logged-out visitors.
async function boot() {
    const me = await apiGetJSON("/me");
    if (me === null) {
        window.location.href = "index.html";
        return;
    }
    // The sites list is the source of truth for which sites an account has.
    const sites = await apiGetJSON("/sites");
    if (sites === null) {
        window.location.href = "index.html";
        return;
    }
    if (sites.length > 0) {
        window.location.href = "dashboard.html";
        return;
    }
    customElements.whenDefined("counter-trackingcode").then(() => {
        let el = document.querySelector("counter-trackingcode");
        // The tracking code keys on the username (see dashboard.js).
        el.draw(me.user.id, me.user.prefs.utcoffset || getUTCOffset());
    });
}
boot();

// Not signed in (the /account endpoint answered 401) means the setup page is
// only reachable for logged-out visitors.
async function boot() {
    const me = await apiGetJSON("/account");
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
        el.draw(me.user.id, me.user.timezone || getUTCOffset());
    });
    const username = me.user.id;
    const utcoffset = me.user.timezone || getUTCOffset();
    document.getElementById("test-visit").onclick = async function (evt) {
        evt.preventDefault();
        await triggerTestVisit(username, utcoffset);
    };
    pollForSites();
}

// Once the first visits are ingested, a site shows up in the account's
// site list — that's the signal to hand the user over to the dashboard.
// /sites is the same source of truth boot() keys on.
function pollForSites() {
    setInterval(async function () {
        const sites = await apiGetJSON("/sites");
        if (sites !== null && sites.length > 0) {
            window.location.href = "dashboard.html";
        }
    }, 5000);
}

// Send one /track and one /trackpage beacon, mimicking what the embedded
// tracking script does for a visitor's first and later pages, so the user
// can verify the pipeline (tracker -> Redis -> sync -> dashboard) without
// editing their site first. The tracker sits behind its own hostname
// (t.counter.dev / t.counterdev.test), like the API hostname in apiBase().
// The tracker requires an Origin header (the browser sends it on these
// cross-origin POSTs) and silently drops localhost origins and bots.
async function triggerTestVisit(username, utcoffset) {
    const host = window.location.hostname;
    let base = "";
    if (host === "counter.dev" || host === "www.counter.dev") base = "https://t.counter.dev";
    if (host === "counterdev.test" || host === "counterdev") base = "http://t." + host;
    if (!base) {
        throw new Error("unknown tracker host");
    }
    const params = new URLSearchParams({
        id: username,
        utcoffset: String(utcoffset),
        referrer: window.location.href,
        screen: "1920x1080",
        page: "/test-visit",
    });
    const track = await fetch(base + "/track", {
        method: "POST",
        body: params,
        credentials: "omit",
    });
    if (!track.ok) {
        throw new Error("/track answered " + track.status);
    }
    const trackpage = await fetch(base + "/trackpage", {
        method: "POST",
        body: params,
        credentials: "omit",
    });
    if (!trackpage.ok) {
        throw new Error("/trackpage answered " + trackpage.status);
    }
}

boot();

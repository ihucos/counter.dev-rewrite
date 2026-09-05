window.state = {};
Chart.defaults.global.tooltips = {
    ...Chart.defaults.global.tooltips,
    ...{
        enabled: true,
        mode: "index",
        borderWidth: 1,
        cornerRadius: 2,
        xPadding: 8,
        yPadding: 12,
        backgroundColor: "#ffffff",
        borderColor: "#121212",

        titleFontSize: 12,
        titleFontFamily: "Nunito Sans",
        titleFontColor: "#121212",

        bodyFontSize: 12,
        bodyFontFamily: "Nunito Sans",
        bodyFontColor: "#121212",
        displayColors: false,
    },
};

Chart.defaults.global.tooltips.callbacks.label = function (tooltipItem, data) {
    var value = data.datasets[0].data[tooltipItem.index];
    return numberFormat(value);
};

Chart.defaults.global.animation.duration = 0;

function getSelectorEl() {
    let selectorMatch = document.getElementsByTagName("dashboard-selector");
    if (selectorMatch.length > 0) {
        return selectorMatch[0];
    } else {
        throw `connectData: tag dashboard-selector not found`;
        return;
    }
}
selector = getSelectorEl(); // very import element

allConnectedData = [];
function connectData(selector, getData) {
    Array.from(document.querySelectorAll(selector)).forEach((el) => {
        allConnectedData.push([el, getData]);
    });
}

// helper function for working with connectData
function k(...keys) {
    return (dump) => {
        return keys.map((key) => dump.sites[selector.site].visits[selector.range][key]);
    };
}

// this one must be first
connectData("dashboard-selector", (dump) => [dump]);

connectData("dashboard-addbtn", (dump) => [dump.meta.sessionless]);

connectData("dashboard-download", (dump) => [dump.sites[selector.site].visits[selector.range], selector.site, selector.range, dump.meta.sessionless]);

// The tracking code keys on the username: the tracker buckets visits under
// the data-id it is given, sync.py maps that id to the account and the
// dashboard reads visit logs from log:<site>:<username>.
connectData("counter-trackingcode", (dump) => [dump.user.id, dump.user.prefs.utcoffset || getUTCOffset()]);

connectData("dashboard-dynamics", (dump) => [dump.sites[selector.site].visits[selector.range]["date"], dump.user.prefs.utcoffset || getUTCOffset()]);

connectData("dashboard-graph", (dump) => [dump.sites[selector.site].visits[selector.range]["date"], dump.sites[selector.site].visits[selector.range]["hour"], dump.user.prefs.utcoffset || getUTCOffset(), selector.range]);

connectData("dashboard-settings", (dump) => [
    {
        cursite: selector.site,
        id: dump.user.id,
        meta: dump.meta,
        utcoffset: dump.user.prefs.utcoffset || getUTCOffset(),
    },
]);

connectData("dashboard-counter-visitors", (dump) => [
    dump.sites[selector.site].visits,
    selector.range,
    dump.user.prefs.utcoffset || getUTCOffset(), // getUTCOffset() is a fallback for older users
]);
connectData("dashboard-counter-search", (dump) => [dump.sites[selector.site].visits, selector.range, dump.user.prefs.utcoffset || getUTCOffset()]);
connectData("dashboard-counter-social", (dump) => [dump.sites[selector.site].visits, selector.range, dump.user.prefs.utcoffset || getUTCOffset()]);
connectData("dashboard-counter-direct", (dump) => [dump.sites[selector.site].visits, selector.range, dump.user.prefs.utcoffset || getUTCOffset()]);
connectData("#devices dashboard-pie", k("device"));
connectData("#platforms dashboard-pie ", k("platform"));
connectData("#browsers dashboard-pie", k("browser"));
connectData("dashboard-sources-countries", k("ref", "country"));
connectData("dashboard-languages", k("lang"));
connectData("dashboard-screens", k("screen"));
connectData("dashboard-pages", k("page"));
connectData("dashboard-visits", (dump) => [dump.sites[selector.site].logs]);
connectData("dashboard-hour", k("hour"));
connectData("dashboard-week", k("weekday"));
connectData("dashboard-time", k("hour"));
connectData("dashboard-share-account", (dump) => [dump.user, dump.meta]);

// --- Data loading ---------------------------------------------------------------
// The dashboard fetches data only on page load and on user interactions
// (date-range or site changes); there is no live connection.

// Each preset range maps to the range the counters compare it against
// (dashboard/counter/_base.js); both buckets are fetched together.
const COMPARISON_RANGE = {
    day: "yesterday",
    yesterday: "last7",
    last7: "last30",
    last30: "all",
    month: "year",
    year: "all",
    all: "all",
    daterange: "all",
};

let me = null; // payload of /account
let siteList = []; // payload of /sites (the account's real host names)

// The dashboard expects every range bucket to carry all tracker categories;
// fill in empty maps for dimensions the backend had no data for.
const VISIT_DIMENSIONS = [
    "lang", "ref", "page", "date", "weekday", "platform",
    "browser", "device", "country", "screen", "hour",
];

function normalizeBucket(bucket) {
    bucket = bucket || {};
    for (const dim of VISIT_DIMENSIONS) {
        if (!bucket[dim]) {
            bucket[dim] = {};
        }
    }
    return bucket;
}

// Fixed presets are computed client-side as start/end values; the query
// endpoint only serves arbitrary (open-ended) ranges. Returns [start, end]
// with null meaning "unbounded".
function rangeDates(range, utcoffset) {
    const fmt = (m) => m.format("YYYY-MM-DD");
    const today = moment().utcOffset(utcoffset);
    switch (range) {
        case "day":
            return [fmt(today), fmt(today)];
        case "yesterday":
            return [fmt(today.clone().subtract(1, "days")), fmt(today.subtract(1, "days"))];
        case "last7":
            return [fmt(today.clone().subtract(6, "days")), fmt(today)];
        case "last30":
            return [fmt(today.clone().subtract(29, "days")), fmt(today)];
        case "month":
            return [fmt(today.clone().startOf("month")), fmt(today)];
        case "year":
            return [fmt(today.clone().startOf("year")), fmt(today)];
        case "all":
            return [null, null];
        case "daterange":
            return [window.state.daterange_from, window.state.daterange_to];
        default:
            return [null, null];
    }
}

// Site names as shown in the selector / used as dump.sites keys.
function displaySiteNames() {
    if (me.meta.demo) {
        return ["counter.dev"];
    }
    return siteList.map((s) => s.name);
}

// The site name used in /query calls (the demo account's real host may
// differ from the "counter.dev" name it is displayed under).
function querySiteName(displayName) {
    if (me.meta.demo) {
        return siteList.map((s) => s.name)[0];
    }
    return displayName;
}

function currentSite() {
    const names = displaySiteNames();
    const select = document.getElementById("site-select");
    if (select && names.includes(select.value)) {
        return select.value;
    }
    const pref = window.dump.user.prefs.site;
    return names.includes(pref) ? pref : names[0];
}

function currentRange() {
    const select = document.getElementById("range-select");
    return (select && select.value) || window.dump.user.prefs.range || "day";
}

function currentUTCOffset() {
    return window.dump.user.prefs.utcoffset || getUTCOffset();
}

async function fetchQuery(displaySite, range) {
    const params = new URLSearchParams(window.location.search);
    params.set("site", querySiteName(displaySite));
    const [start, end] = rangeDates(range, currentUTCOffset());
    if (start) params.set("start", start);
    if (end) params.set("end", end);
    const resp = await fetch(apiUrl("/query?") + params.toString(), { credentials: "include" });
    if (resp.status === 401) {
        return null;
    }
    return resp.json();
}

// Fetch one range for the currently selected site into the dump; returns
// false (after redirecting) when the session has expired.
async function loadRange(range) {
    const site = currentSite();
    const data = await fetchQuery(site, range);
    if (data === null) {
        window.location.href = "welcome.html";
        return false;
    }
    if (range === "daterange") {
        window.state.daterange = { [site]: data.visits };
    } else {
        window.dump.sites[site].visits[range] = normalizeBucket(data.visits);
        window.dump.sites[site].logs = data.logs;
    }
    return true;
}

function addDaterangeToDump(daterange, dump) {
    for (const site of Object.keys(dump.sites)) {
        let siteData = daterange[site];
        let nildata = Object.fromEntries(VISIT_DIMENSIONS.map((k) => [k, {}]));
        if (siteData) {
            dump.sites[site].visits.daterange = { ...nildata, ...siteData };
        } else {
            dump.sites[site].visits.daterange = nildata;
        }
        normalizeBucket(dump.sites[site].visits.daterange);
    }
}

function patchDump(dump) {
    if (window.state.daterange) {
        addDaterangeToDump(window.state.daterange, dump);
    }
}

function redraw() {
    let dump = window.dump;
    allConnectedData.forEach(([el, getData]) => {
        // One broken component must not blank out the rest of the dashboard.
        try {
            if (customElements.get(el.localName)) {
                el.draw(...getData(dump));
            } else {
                customElements.whenDefined(el.localName).then(() => el.draw(...getData(dump)));
            }
        } catch (err) {
            console.error("redraw of", el.localName, "failed:", err);
        }
    });
}

document.addEventListener("redraw", () => redraw());

// The site/range selectors announce their changes; the dashboard then
// fetches the affected data and redraws.
async function onStateChanged() {
    window.dump.user.prefs.range = currentRange();
    if (currentRange() !== "daterange") {
        const loaded = await loadRange(currentRange());
        if (!loaded) return;
    }
    // The counters compare the selected range against its comparison range.
    const comparison = COMPARISON_RANGE[currentRange()];
    if (comparison && !(window.dump.sites[currentSite()].visits[comparison])) {
        await loadRange(comparison);
    }
    patchDump(window.dump);
    document.dispatchEvent(new CustomEvent("redraw", { detail: window.dump }));
}

document.addEventListener("dashboard-state-changed", onStateChanged);

// A custom date range picked in the daterangeselector.
document.addEventListener("selector-daterange-fetched", async (evt) => {
    window.state.daterange_from = evt.detail.from.format("YYYY-MM-DD");
    window.state.daterange_to = evt.detail.to.format("YYYY-MM-DD");
    const loaded = await loadRange("daterange");
    if (!loaded) return;
    patchDump(window.dump);
    document.dispatchEvent(new CustomEvent("redraw", { detail: window.dump }));
});

// Pay-what-you-want prompt for accounts with 90+ days of data.
function maybePayWhatYouWant(daysTracked) {
    if (window.dump.meta.sessionless || daysTracked <= 90 || sessionStorage.getItem("pwyw") !== null) {
        return;
    }
    whenReady("base-pwyw", (el) => el.modal());
    sessionStorage.setItem("pwyw", "1");
}

// The "all time" bucket feeds the daterangeselector's oldest-date
// constraint and the pay-what-you-want check.
async function loadAllTimeBucket() {
    if (!window.dump.sites[currentSite()].visits.all) {
        await loadRange("all").catch(() => {});
    }
    const dates = Object.keys((window.dump.sites[currentSite()].visits.all || {}).date || {});
    return dates.sort()[0] || null;
}

async function boot() {
    me = await apiGetJSON("/account");
    if (me === null) {
        window.location.href = "welcome.html";
        return;
    }
    siteList = await apiGetJSON("/sites");
    if (siteList === null) {
        window.location.href = "welcome.html";
        return;
    }
    if (siteList.length === 0) {
        window.location.href = "setup.html";
        return;
    }

    window.dump = {
        user: me.user,
        meta: me.meta,
        sites: Object.fromEntries(displaySiteNames().map((name) => [name, { visits: {}, logs: [] }])),
    };
    if (me.meta.demo) {
        window.dump.user.prefs.site = "counter.dev";
    }

    const loaded = await loadRange(currentRange());
    if (!loaded) return;
    const comparison = COMPARISON_RANGE[currentRange()];
    if (comparison && comparison !== currentRange() && !window.dump.sites[currentSite()].visits[comparison]) {
        await loadRange(comparison).catch(() => {});
    }
    patchDump(window.dump);
    document.dispatchEvent(new CustomEvent("redraw", { detail: window.dump }));

    loadAllTimeBucket().then((oldest) => {
        customElements.whenDefined("dashboard-daterangeselector").then(() => {
            document.getElementsByTagName("dashboard-daterangeselector")[0].draw(oldest || moment().format("YYYY-MM-DD"));
        });
        maybePayWhatYouWant(Object.keys((window.dump.sites[currentSite()].visits.all || {}).date || {}).length);
    });
}

customElements.whenDefined(selector.localName).then(() => {
    customElements.upgrade(selector);
    boot().catch((err) => console.error("boot failed:", err));
});

function numberFormat(x) {
    return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

function percentRepr(value, total) {
    var percentRepr = Math.round((value / total) * 100) + "%";
    if (percentRepr === "0%") {
        percentRepr = "<1%";
    }
    return percentRepr;
}

function dGroupData(entries, cutAt) {
    var entrs = Object.entries(entries);
    entrs = entrs.sort((a, b) => b[1] - a[1]);
    var top = entrs.slice(0, cutAt);
    var bottom = entrs.slice(cutAt);

    otherVal = 0;
    bottom.forEach((el) => (otherVal += el[1]));
    if (otherVal) {
        top.push(["Other", otherVal]);
    }

    var res = Object.fromEntries(top);
    if ("Unknown" in res) {
        res["Other"] = (res["Other"] || 0) + res["Unknown"];
        delete res["Unknown"];
    }
    return res;
}

function getUTCNow(utcoffset) {
    return moment().add(parseInt(utcoffset), "hours").toDate();
}

function dFillDatesToNow(myDates, utcoffset) {
    // Hack, sort the keys in the object
    dates = Object.keys(myDates)
        .sort()
        .reduce(function (acc, key) {
            acc[key] = myDates[key];
            return acc;
        }, {});

    var daysRange = (s, e) => {
        var s = new Date(s);
        var e = new Date(e);
        var o = {};
        for (var a = [], d = new Date(s); d <= e; d.setDate(d.getDate() + 1)) {
            o[new Date(d).toISOString().substring(0, 10)] = 0;
        }
        return o;
    };

    var sortedAvailableDates = Object.keys(dates).sort((a, b) => {
        return a > b;
    });

    return {
        ...daysRange(sortedAvailableDates[0], getUTCNow(utcoffset)),
        ...dates,
    };
}

function dGroupDates(dates) {
    let allMonths = Object.entries(dates).reduce((acc, val) => {
        let group = moment(val[0]).format("MMMM YYYY");
        acc.add(group);
        return acc;
    }, new Set());

    let groupedByMonth = Object.entries(dates).reduce((acc, val) => {
        let group;
        if (allMonths.size <= 12) {
            group = moment(val[0]).format("MMMM");
        } else {
            group = moment(val[0]).format("MMM YYYY");
        }
        acc[group] = (acc[group] || 0) + val[1];
        return acc;
    }, {});

    let groupedByWeek = Object.entries(dates).reduce((acc, val) => {
        let group = moment(val[0]).format("[CW]w");
        acc[group] = (acc[group] || 0) + val[1];
        return acc;
    }, {});

    let groupedByYear = Object.entries(dates).reduce((acc, val) => {
        let group = moment(val[0]).format("YYYY");
        acc[group] = (acc[group] || 0) + val[1];
        return acc;
    }, {});

    var groupedDates = dates;
    if (Object.keys(groupedDates).length > 31) {
        groupedDates = groupedByWeek;
        // if it's still to big, use months. 16 is a magic number to swap to the per month view
        if (Object.keys(groupedDates).length > 16) {
            groupedDates = groupedByMonth;
            // Use years if we are displaying more than 32 month.
            if (Object.keys(groupedDates).length > 32) {
                groupedDates = groupedByYear
            }
        }
    }

    return [Object.keys(groupedDates), Object.values(groupedDates)];
}

HOUR_AM_PM = {
    0: "12 a.m.",
    1: "1 a.m.",
    2: "2 a.m.",
    3: "3 a.m.",
    4: "4 a.m.",
    5: "5 a.m.",
    6: "6 a.m.",
    7: "7 a.m.",
    8: "8 a.m.",
    9: "9 a.m.",
    10: "10 a.m.",
    11: "11 a.m.",
    12: "12 noon",
    13: "1 p.m.",
    14: "2 p.m.",
    15: "3 p.m.",
    16: "4 p.m.",
    17: "5 p.m.",
    18: "6 p.m.",
    19: "7 p.m.",
    20: "8 p.m.",
    21: "9 p.m.",
    22: "10 p.m.",
    23: "11 p.m.",
};

function dGetNormalizedHours(hours) {
    let pad = Object.fromEntries([...Array(24).keys()].map((i) => [HOUR_AM_PM[i], 0]));
    let formatedHours = Object.fromEntries(Object.entries(hours).map((i) => [HOUR_AM_PM[i[0]], i[1]]));
    return {
        ...pad,
        ...formatedHours,
    };
}
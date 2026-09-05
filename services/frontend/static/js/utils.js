var script = document.createElement("script");
script.dataset.id = "33671ad4-a966-4a52-b48f-56c92d10a678";
script.dataset.utcoffset = "1";
script.dataset.server = "https://simple-web-analytics.com";
script.src = "https://cdn.counter.dev/script-testing.js";
document.getElementsByTagName("head")[0].appendChild(script);

// The API lives on its own hostname (api.counter.dev / api.counterdev.test);
// unknown hosts (tests, direct backend access) keep same-origin URLs. The
// local frontend must be served as counterdev.test: subdomains of a bare
// "counterdev" are separate sites for the browser, which then drops the
// session cookie (subdomains of a two-label base like counterdev.test are
// same-site and the cookie flows over plain HTTP).
function apiBase() {
    var host = window.location.hostname;
    if (host === "counter.dev" || host === "www.counter.dev") return "https://api.counter.dev";
    if (host === "counterdev.test") return "http://api.counterdev.test";
    return "";
}

// Prefix API paths with the API host; other URLs (e.g. form action="")
// stay on the current origin.
function apiUrl(url) {
    return url.charAt(0) === "/" ? apiBase() + url : url;
}

// Modal openers are bound delegated at document level: most rel="modal:open"
// links live inside components injected after page load (navbar, settings),
// which a ready-time binding never reaches.
$(document).on("click", 'a[rel="modal:open"]', function (event) {
    $(this).modal({
        fadeDuration: 200,
        fadeDelay: 0,
    });
    return false;
});

function simpleForm(formSelector, arg) {
    var success, formEl;
    if (typeof arg === "function") {
        success = arg;
    } else {
        success = function (response) {
            window.location.href = arg;
        };
    }
    if (typeof formSelector === "string") {
        formEl = document.querySelector(formSelector);
    } else {
        formEl = formSelector;
    }

    formEl.onsubmit = (evt) => {
        var el = evt.target;
        $.ajax({
            type: el.getAttribute("method") || "POST",
            url: apiUrl(el.getAttribute("action")),
            data: $(el).serialize(),
            xhrFields: { withCredentials: true },
            success: success,
            error: function (request, status, error) {
                notify(request.responseText);
            },
        });
        return false;
    };
}

function getUTCOffset() {
    return Math.round((-1 * new Date().getTimezoneOffset()) / 60);
}

function escapeHtml(unsafe) {
    return (unsafe + "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

// GET a JSON endpoint with credentials, forwarding the current query string
// so guest (?user=&token=) and demo (?demo=1) access flows through.
// Returns the parsed body, or null on 401 ("not signed in").
function apiGetJSON(path) {
    var params = new URLSearchParams(window.location.search);
    return fetch(apiUrl(path) + (params.toString() ? "?" + params.toString() : ""), {
        credentials: "include",
    }).then(function (resp) {
        if (resp.status === 401) {
            return null;
        }
        if (!resp.ok) {
            throw resp;
        }
        return resp.json();
    });
}

function notify(msg, cb) {
    $("#modal-notify").remove();
    var html = `<div id="modal-notify" style="displaty: none;">
      <div class="modal-header">
        <a href="#" class="btn-close" rel="modal:close"></a>
      </div>
      <div class="modal-content">
        <span>
            ${escapeHtml(msg)}
        </span>
        <div class="mt24 mb32 flex">
          <a href="#" class="btn-primary" rel="modal:close">Okay</a>
        </div>
      </div>
    </div>`;
    $("body").append($(html));
    $("#modal-notify").modal({ closeExisting: false });
}

function whenReady(tag, cb) {
    customElements.whenDefined(tag).then(() => {
        var el = document.querySelector(tag);
        cb(el);
    });
}

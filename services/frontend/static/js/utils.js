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
document.addEventListener("click", function (event) {
    var opener = event.target.closest('a[rel="modal:open"]');
    if (opener) {
        event.preventDefault();
        var target = document.querySelector(opener.getAttribute("href"));
        if (target) openModal(target);
    }
    var closer = event.target.closest('a[rel="modal:close"]');
    if (closer) {
        event.preventDefault();
        closeModal();
    }
});

// Minimal modal system replacing jquery-modal. A modal element (any element,
// usually a hidden div) is shown centered over a full-screen blocker.
// Events dispatched on the modal element:
//   "modal-before-close", "modal-after-close" (bubbles, so parents can listen)
var openModalStack = [];
var modalZIndex = 998;

function openModal(el, opts) {
    opts = opts || {};
    if (opts.closeExisting !== false) {
        closeModal();
    }
    var blocker = document.createElement("div");
    blocker.className = "modal-blocker";
    blocker.style.zIndex = ++modalZIndex;
    document.body.appendChild(blocker);
    // The modal lives inside the blocker so it scrolls with the dimmed
    // viewport and sits above it; remember where to put it back.
    var savedParent = el.parentNode;
    var savedNext = el.nextSibling;
    blocker.appendChild(el);
    el.classList.add("modal");
    el.style.display = "block";
    document.body.classList.add("modal-open");
    openModalStack.push({ el: el, blocker: blocker, opts: opts, savedParent: savedParent, savedNext: savedNext });
    // fade in
    el.style.opacity = "0";
    blocker.style.opacity = "0";
    requestAnimationFrame(function () {
        el.style.opacity = "1";
        blocker.style.opacity = "1";
    });
    // Close when clicking the dimmed area outside the modal.
    blocker.addEventListener("click", function (event) {
        if (event.target !== blocker || opts.blockerClose === false) {
            return;
        }
        var top = openModalStack[openModalStack.length - 1];
        if (top && top.blocker === blocker) {
            closeModal();
        }
    });
}

function closeModal() {
    var entry = openModalStack.pop();
    if (!entry) {
        return;
    }
    entry.el.dispatchEvent(new CustomEvent("modal-before-close", { bubbles: true }));
    entry.el.style.display = "none";
    entry.el.style.opacity = "";
    entry.el.classList.remove("modal");
    if (entry.savedParent) {
        entry.savedParent.insertBefore(entry.el, entry.savedNext);
    }
    entry.blocker.remove();
    if (openModalStack.length === 0) {
        document.body.classList.remove("modal-open");
    }
    entry.el.dispatchEvent(new CustomEvent("modal-after-close", { bubbles: true }));
}

document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && openModalStack.length > 0) {
        var entry = openModalStack[openModalStack.length - 1];
        if (entry.opts.escapeClose !== false) {
            closeModal();
        }
    }
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
        var body = new URLSearchParams(new FormData(el)).toString();
        fetch(apiUrl(el.getAttribute("action")), {
            method: el.getAttribute("method") || "POST",
            body: body,
            credentials: "include",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
        }).then(async function (resp) {
            if (!resp.ok) {
                notify(await resp.text());
            } else {
                success(await resp.text());
            }
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
    document.querySelector("#modal-notify")?.remove();
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
    document.body.insertAdjacentHTML("beforeend", html);
    openModal(document.querySelector("#modal-notify"), { closeExisting: false });
}

function whenReady(tag, cb) {
    customElements.whenDefined(tag).then(() => {
        var el = document.querySelector(tag);
        cb(el);
    });
}

// Slide helpers replacing jQuery slideUp/slideDown.
function slideHide(el) {
    el.style.display = "none";
}

function slideShow(el) {
    el.style.display = "";
}

// Minimal tabs implementation replacing jquery.tabslet. Works on a container
// (e.g. .tabs or .responsive-tabs) holding a ul.tabs-menu / ul.responsive-tabs-menu
// whose links point at content element ids. destroy() shows all contents again.
function initTabs(container, opts) {
    opts = opts || {};
    if (container.dataset.tabsInit) {
        return;
    }
    container.dataset.tabsInit = "1";
    var menu = container.querySelector(".tabs-menu, .responsive-tabs-menu");
    var links = menu.querySelectorAll("a");
    var contents = [];
    links.forEach(function (link) {
        var content = container.querySelector(link.getAttribute("href"));
        if (content) contents.push(content);
    });
    function activate(link) {
        links.forEach(function (l) {
            l.parentElement.classList.toggle("active", l === link);
        });
        contents.forEach(function (c) {
            c.style.display = c.id === link.getAttribute("href").slice(1) ? "" : "none";
        });
    }
    menu.addEventListener("click", function (event) {
        var link = event.target.closest("a");
        if (!link || !container.querySelector(link.getAttribute("href"))) {
            return;
        }
        event.preventDefault();
        activate(link);
    });
    var activeIndex = opts.active ? opts.active - 1 : 0;
    activate(links[activeIndex]);
}

function destroyTabs(container) {
    if (!container.dataset.tabsInit) {
        return;
    }
    delete container.dataset.tabsInit;
    var menu = container.querySelector(".tabs-menu, .responsive-tabs-menu");
    menu.querySelectorAll("li").forEach(function (li) {
        li.classList.remove("active");
    });
    container.querySelectorAll(".tabs-menu a, .responsive-tabs-menu a").forEach(function (link) {
        var content = container.querySelector(link.getAttribute("href"));
        if (content) content.style.display = "";
    });
}
from lib import HtmlBuilder


t = HtmlBuilder("body")
with t.header:
    with t.section(klass="navbar"):
        # Feedback modal
        with t.div(id="modal-feedback", style="display: none"):
            with t.div(klass="modal-header"):
                t.img(src="/img/feedback.svg", width="24", height="24", alt="Feedback")
                t.h3("Feedback", klass="ml16")
                t.a(href="#", klass="btn-close", rel="modal:close")
            with t.div(klass="modal-content"):
                with t.form(action="/feedback", method="POST"):
                    with t.label(klass="width-full"):
                        t.text("How can we make the service better for you? ")
                        t.textarea(
                            klass="width-full",
                            name="feedback",
                            style="min-height: 200px;",
                        )
                        t.input(
                            id="feedback-mail",
                            type="email",
                            name="contact",
                            placeholder="Mail to receive reply (optional)",
                            klass="width-full",
                        )
                    with t.div(klass="account-btn-group flex mt24 mb32"):
                        t.a(
                            "Cancel",
                            href="#",
                            klass="btn-secondary full mr16",
                            rel="modal:close",
                        )
                        t.button("Send", type="submit", klass="btn-primary full")

        with t.div(klass="content"):
            t.a(href="/index.html", klass="logotype")
            # Navigation
            with t.nav(klass="nav-header"):
                t.a("Help", href="/help/", klass="mr32")
                t.a("Blog", href="/blog", klass="mr32")
                t.a(
                    "Feedback",
                    href="#modal-feedback",
                    klass="mr32",
                    target="_blank",
                    rel="modal:open",
                )
                t.a(
                    href="https://github.com/ihucos/counter.dev",
                    klass="github-blue mr16",
                    target="_blank",
                    rel="nofollow",
                )
                with t.div(klass="has-user dropdown", style="display: none"):
                    t.div(klass="profile-user fill-username")
                    with t.div(klass="dropdown-content"):
                        t.a("Dashboard", href="/dashboard")
                        t.a("Edit account", href="#modal-account", rel="modal:open")
                        t.a("Sign out", href="/logout")
                with t.span(klass="no-user profile-guest", style="display: none"):
                    t.a("Log in", href="/welcome.html?sign-in", klass="ml32 mr32")
                    t.a("Sign up", href="/welcome.html?sign-up", klass="btn-primary")
            # Hamburger
            with t.div(klass="hamburger-menu"):
                t.input(id="hamburger-toggle", type="checkbox")
                t.label(
                    klass="hamburger-btn", ffor="hamburger-toggle"
                )  # Note: ffor used if your lib maps HTML 'for' to avoid Python keyword collision
                with t.div(klass="hamburger-box"):
                    with t.div(klass="hamburger-content"):
                        t.img(
                            src="/img/avatar.svg",
                            width="96",
                            height="96",
                            alt="Avatar",
                        )
                        # Navigation
                        with t.nav(klass="nav-header-mob"):
                            # Guest
                            with t.span(
                                klass="no-user mt48 mb48", style="display: none"
                            ):
                                t.a(
                                    "Log in",
                                    href="/welcome.html?sign-in",
                                    klass="btn-primary mr16",
                                )
                                t.a(
                                    "Sign up",
                                    href="/welcome.html?sign-up",
                                    klass="btn-secondary",
                                )
                            # User
                            with t.div(klass="has-user", style="display: none"):
                                t.div(klass="mt24 fill-username")
                                with t.div(klass="mt24 mb48"):
                                    t.a(
                                        "Edit account",
                                        href="#modal-account",
                                        klass="btn-primary mr16",
                                        rel="modal:open",
                                        onClick="document.getElementById('hamburger-toggle').checked=false",
                                    )
                                    t.a(
                                        "Sign out",
                                        href="/logout",
                                        klass="btn-secondary",
                                    )
                            t.a("Blog", href="/blog", klass="mb24")
                            t.a(
                                "Dashboard",
                                href="/dashboard",
                                klass="has-user mb24",
                                target="_blank",
                                rel="nofollow",
                                style="display: none",
                            )
                            t.a(
                                "Feedback",
                                href="mailto:hey@counter.dev",
                                klass="mb24",
                                target="_blank",
                                rel="nofollow",
                            )
                            with t.span(klass="mt48"):
                                t.a(
                                    href="https://github.com/ihucos/counter.dev",
                                    klass="github-blue mr24",
                                    target="_blank",
                                    rel="nofollow",
                                )
                                t.a(
                                    href="https://twitter.com/NaiveTeamHQ",
                                    klass="twitter-blue",
                                    target="_blank",
                                    rel="nofollow",
                                )

    t.element("base-editaccount")

with t.div as content:
    pass

__all__ = ["content"]

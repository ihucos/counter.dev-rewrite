# from base import Element  # content, head
from lib import Element


t = Element("head")
with t:
    t.title("Counter: Welcome")
    t.meta(
        name="description",
        content="Web Analytics made simple and therefore privacy-friendly.",
    )
    t.meta(name="viewport", content="width=device-width, initial-scale=1")
    t.link(rel="shortcut icon", href="img/favicon.png")
    t.link(
        href="https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@400;700&family=Poppins:wght@700&display=swap",
        rel="stylesheet",
    )
    t.link(
        rel="stylesheet",
        type="text/css",
        href="https://cdnjs.cloudflare.com/ajax/libs/jquery-modal/0.9.2/jquery.modal.min.css",
    )
    t.script(src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.5.1/jquery.min.js")
    t.script(
        src="https://cdnjs.cloudflare.com/ajax/libs/jquery-modal/0.9.2/jquery.modal.min.js"
    )
    t.script(src="js/utils.js")
    t.script(src="/load.js")
    t.link(rel="stylesheet", type="text/css", href="css/welcome.css")


t = Element("body")
with t:
    # Welcome page
    with t.section(klass="welcome"):
        with t.div(klass="content"):
            # Text
            with t.div(klass="welcome-text"):
                t.h1("Welcome")
                t.div(
                    "Tracking code is shown after sign up.",
                    klass="title gray mt16 mb32",
                )

                # Features
                # Item
                with t.div(klass="welcome-features-item flex bg-white radius-sm mb16"):
                    t.img(
                        src="/img/free-sm.svg",
                        width="24",
                        height="24",
                        alt="Pay when ready",
                    )
                    t.h3("Pay when ready", klass="ml16")
                # Item
                with t.div(klass="welcome-features-item flex bg-white radius-sm mb16"):
                    t.img(
                        src="/img/open-sm.svg",
                        width="24",
                        height="24",
                        alt="Open Source",
                    )
                    t.h3("Open Source", klass="ml16")
                # Item
                with t.div(klass="welcome-features-item flex bg-white radius-sm"):
                    t.img(
                        src="/img/privacy-sm.svg",
                        width="24",
                        height="24",
                        alt="privacy-friendly",
                    )
                    t.h3("Privacy-friendly", klass="ml16")

            # Form
            with t.div(klass="welcome-form bg-white radius-sm shadow-lg tabs"):
                # Tabs
                with t.ul(klass="tabs-menu bg-blue radius-sm"):
                    with t.li:
                        t.a("Log in", href="#sign-in")
                    with t.li:
                        t.a("Sign up", href="#sign-up")

                # Log in
                with t.div(id="sign-in", style="display: none"):
                    with t.form(action="/login", method="POST"):
                        t.div("Log in to your account", klass="title mb16")
                        with t.label(klass="width-full mb8"):
                            t.text("Username")
                            t.input(
                                type="text",
                                name="user",
                                placeholder="Enter your username",
                                klass="width-full",
                            )
                        with t.label(klass="width-full"):
                            t.text("Password")
                            t.input(
                                name="password",
                                type="password",
                                placeholder="Enter your password",
                                klass="width-full",
                            )
                        with t.div(
                            style="justify-content: space-between", klass="flex"
                        ):
                            t.button(
                                "Log in", type="submit", klass="btn-secondary mt24"
                            )
                            t.a(
                                "Forgot password",
                                href="#modal-recover",
                                style="font-weight: 400",
                                rel="modal:open",
                                klass="btn-white mt24",
                            )

                # Sign up
                with t.div(id="sign-up"):
                    with t.form(action="/register", method="POST"):
                        t.div("Sign up to Counter", klass="title mb16")
                        with t.div(klass="flex mb8"):
                            with t.label(klass="width-half mr16"):
                                t.text("Username")
                                t.input(
                                    name="user",
                                    type="text",
                                    placeholder="Username",
                                    klass="width-full",
                                )
                            with t.label(klass="width-half"):
                                t.text("E-Mail")
                                t.input(
                                    name="mail",
                                    type="email",
                                    placeholder="E-Mail (optional)",
                                    klass="width-full",
                                )

                        t.script(
                            'document.write(`<input type="hidden" name="utcoffset" value="${getUTCOffset()}"></input>`);'
                        )

                        with t.label(klass="width-full"):
                            t.text("Password")
                            t.input(
                                name="password",
                                type="password",
                                placeholder="Choose a password",
                                klass="password-input width-full",
                            )
                        t.button("Sign up", type="submit", klass="btn-secondary mt24")

    # Forgot Password
    with t.div(id="modal-recover", style="display: none"):
        with t.div(klass="modal-header"):
            t.img(src="/img/account.svg", width="24", height="24", alt="Edit account")
            t.h3("Recover account", klass="ml16")
            t.a(href="#", klass="btn-close", rel="modal:close")
        with t.div(klass="modal-content"):
            with t.form(action="/recover", method="POST"):
                # mail
                with t.label(klass="width-full mb8"):
                    t.text("Email")
                    t.input(
                        name="mail",
                        type="email",
                        placeholder="Account E-Mail",
                        klass="width-full",
                    )
                # username
                with t.label(klass="width-full mb24"):
                    t.text("Username")
                    t.input(
                        type="text",
                        name="user",
                        placeholder="Enter your username",
                        klass="width-full",
                    )

                with t.span(klass="caption gray"):
                    t.text(
                        "This works if you actually provided us your email. Write to "
                    )
                    t.a("hey@counter.dev", href="mailto:hey@counter.dev")
                    t.text(" for a manual verification process if desired.")

                with t.div(klass="account-btn-group flex mt24 mb32"):
                    t.a(
                        "Cancel",
                        href="#",
                        klass="btn-secondary full mr16",
                        rel="modal:close",
                    )
                    t.button("Recover", type="submit", klass="btn-primary full")

    t.element("base-footer")
    t.script(src="js/welcome.js")

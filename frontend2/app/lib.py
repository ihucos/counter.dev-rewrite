from pyscript import document, window, ffi


class Element:
    """Wraps a live browser DOM element to handle chaining and attribute configuration."""

    def __init__(self, target):
        if isinstance(target, str):
            target = document.querySelector(target)
        self.stack = [target]

    def __getattr__(self, tag_name):
        normalized_tag = tag_name.replace("_", "-")
        dom_el = document.createElement(normalized_tag)
        self.stack[-1].appendChild(dom_el)
        return Element(dom_el)

    def __call__(self, text=None, klass=None, **kwargs):
        # 1. Handle explicit 'klass' parameter if provided
        if klass:
            # Handle spaced strings like "btn-secondary full mr16" or underscores
            classes = klass.replace("_", "-").split()
            for c in classes:
                self.el.classList.add(c)

        # 2. Handle plain text inner node assignment
        if text is not None:
            self.el.innerText = str(text)
            return self

        # 3. Handle HTML attributes
        for k, v in kwargs.items():
            normalized_key = k.replace("_", "-")
            if callable(v):
                if not hasattr(window, "_py_cbs"):
                    window._py_cbs = ffi.to_js({})
                window._py_cbs[id(v)] = v
                v = f"window._py_cbs[{id(v)}]()"
            self.el.setAttribute(normalized_key, str(v))
        return self

    def __enter__(self):
        self.builder.stack.append(self.el)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.builder.stack.pop()

    def __str__(self):
        return str(self.el.innerText)

    def __int__(self):
        return int(self.el.innerText)

    @property
    def el(self):
        return self.stack[-1]

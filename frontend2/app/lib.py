from pyscript import document, window, ffi


class LiveElementContext:
    """Wraps a live browser DOM element to handle chaining and attribute configuration."""

    def __init__(self, dom_element, builder):
        self.dom_element = dom_element
        self.builder = builder

    # def __getattr__(self, attribute_name):
    #     # We preserve this just in case you want to chain other properties,
    #     # but class handling is now primarily driven via the `klass` keyword.
    #     normalized = attribute_name.replace("_", "-")
    #     self.dom_element.classList.add(normalized)
    #     return self

    def __call__(self, text=None, klass=None, **kwargs):
        # 1. Handle explicit 'klass' parameter if provided
        if klass:
            # Handle spaced strings like "btn-secondary full mr16" or underscores
            classes = klass.replace("_", "-").split()
            for c in classes:
                self.dom_element.classList.add(c)

        # 2. Handle plain text inner node assignment
        if text is not None:
            self.dom_element.innerText = str(text)
            return self

        # 3. Handle HTML attributes
        for k, v in kwargs.items():
            normalized_key = k.replace("_", "-")
            if callable(v):
                if not hasattr(window, "_py_cbs"):
                    window._py_cbs = ffi.to_js({})
                window._py_cbs[id(v)] = v
                v = f"window._py_cbs[{id(v)}]()"
            self.dom_element.setAttribute(normalized_key, str(v))
        return self

    def __enter__(self):
        self.builder.stack.append(self.dom_element)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.builder.stack.pop()

    def __str__(self):
        return str(self.dom_element.innerText)

    def __int__(self):
        return int(self.dom_element.innerText)


class HtmlBuilder:
    """Interacts with the PyScript document proxy to assemble the UI tree on the fly."""

    def __init__(self, target=None):
        self.stack = []
        if isinstance(target, str):
            target = document.querySelector(target)
        self.target = target or document.body

    def __getattr__(self, tag_name):
        normalized_tag = tag_name.replace("_", "-")
        dom_el = document.createElement(normalized_tag)
        if self.stack:
            self.stack[-1].appendChild(dom_el)
        else:
            self.target.appendChild(dom_el)

        return LiveElementContext(dom_el, self)

    def element(self, custom_tag, klass=None, **kwargs):
        """Helper to safely instantiate custom elements like counter-flash."""
        dom_el = document.createElement(custom_tag)
        if self.stack:
            self.stack[-1].appendChild(dom_el)
        else:
            self.target.appendChild(dom_el)

        ctx = LiveElementContext(dom_el, self)
        if klass or kwargs:
            ctx(klass=klass, **kwargs)
        return ctx

    def __call__(self, text):
        text_node = document.createTextNode(str(text))
        if self.stack:
            self.stack[-1].appendChild(text_node)
        else:
            self.target.appendChild(text_node)
        return None


t = HtmlBuilder()

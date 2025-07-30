# %%
import colight.plot as Plot

# %% [markdown]
# 1. Intro

# 2. ADEV example

# 3. System guide

# %% [markdown]
# State: when to use it?

# %%
Plot.Column(
    {"gap": 4, "className": "p-5"},
    ["div.font-bold", "When to use state?"],
    [
        "ul.list-disc.space-y-2",
        ["li", "Data is used in more than one place, or"],
        ["li", "Data changes over time (via user interaction or from Python)"],
    ],
    ["div.font-bold.mt-6", "What does it give you?"],
    [
        "ul.list-disc.space-y-2",
        ["li", "Deduplication (during serialization)"],
        ["li", "Efficient change propagation between Python and JavaScript"],
        ["li", "Reactive UI updates within JavaScript"],
    ],
)

# %% [markdown]
# How does state work?

# %%
import colight.plot as Plot
from colight.plot import md

#
(
    Plot.html(["div.text-center.text-lg.!&_code:bg-none", "State API"])
    | Plot.Grid(
        ["div.col-span-2.bg-gray-100.font-bold.p-3", "python: plot definition"],
        md("`Plot.initialState(...)`"),
        "Set initial state",
        md("""`Plot.initialState({"foo": "bar"}, sync={"bar"})`"""),
        md("""...and sync `"bar"` """),
        md("""`Plot.onChange({"x": lambda widget, event: _})`"""),
        md("""Run callback when "x" changes"""),
        md("""`["div", {"onClick": lambda w,e: ...}, "inc"]`"""),
        "Run callback on user events",
        [
            "div.col-span-2.bg-gray-100.font-bold.p-3",
            "python: interacting with live widgets",
        ],
        md("`widget.state.foo`"),
        "Read",
        md("""`widget.state.foo = "baz"`"""),
        "Reset",
        md("""`widget.state.update({"bar": "baz"})`"""),
        "Reset multiple",
        md("""`widget.state.update(["points", "append", [x, y]])`"""),
        "Append, concat, setAt, reset (any number)",
        ["div.col-span-2.bg-gray-100.font-bold.p-3", "javascript"],
        md("""`$state.foo`"""),
        "Read",
        md("""`$state.foo = "baz"`"""),
        "Write",
        md("""`$state.update({"bar": "baz"})`"""),
        "Reset multiple",
        md("""`$state.update(["points", "append", [x, y]])`"""),
        "Append, concat, setAt, reset (any number)",
        widths=["auto", 1],
        gap=4,
    )
)

# DRAW DENSITY EXAMPLE

# %% [markdown]
# LAYOUT / HTML

# %%
import colight.plot as Plot
from colight.plot import md
import numpy as np

#
x = np.arange(10) / 10
points = np.c_[x, x + (np.arange(10) % 3) / 10]
plot1 = Plot.dot(points) + {"className": "bg-green-100"}
plot2 = Plot.md(
    r"""
$$\oint_{\partial \Omega} \mathbf{E} \cdot d\mathbf{S} = \frac{1}{\epsilon_0} \int_\Omega \rho \, dV$$
""",
    className="bg-yellow-100 p-3 flex items-center",
)
plot3 = Plot.dot(points) + {"className": "bg-pink-100"}
#
plot1 & plot2 | plot3 + {"height": 200} | "Hello, world!"

# %% [markdown]
# What is hiccup?

# %%
(
    Plot.Column(
        [
            "span.py-3",
            "Hiccup maps Python data structures 1:1 to HTML (or React):",
        ],
        [
            "span.bg-green-100.p-5.font-mono",
            Plot.bylight(
                """["button.bg-blue-100.p-3", {"disabled": true}, "Click me"]""",
                ['"button...3"', "{...}"],
            ),
        ],
        [
            "span.bg-yellow-100.p-5.font-mono",
            """<button class="bg-blue-100 p-3" disabled>Click me</button>""",
        ],
    )
)

# %% [markdown]
# How do we make plots?

# %%
Plot.Column(
    {"gap": 4},
    [
        "span.py-3",
        "`colight.plot` provides a 1:1 mapping between Observable Plot and python.",
    ],
    ["span.font-bold", "Observable Plot (js):"],
    Plot.md(
        """```
Plot.plot({
  inset: 10,
  marks: [
    Plot.density(faithful, {x: "waiting", y: "eruptions", stroke: "blue", strokeWidth: 0.25}),
    Plot.density(faithful, {x: "waiting", y: "eruptions", stroke: "blue", thresholds: 4}),
    Plot.dot(faithful, {x: "waiting", y: "eruptions", fill: "currentColor", r: 1.5})
  ]
})
```"""
    ),
    ["span.font-bold", "Colight (python):"],
    Plot.md(
        """```
(
    Plot.density(faithful, x="waiting", y="eruptions", stroke="blue", strokeWidth=0.25)
    + Plot.density(faithful, x="waiting", y="eruptions", stroke="blue", thresholds=4)
    + Plot.dot(faithful, x="waiting", y="eruptions", fill="currentColor", r=1.5)
    + Plot.inset(10)
)
```"""
    ),
)

# %% [markdown]
# 4. What can you do with all this? A couple more small examples:

# - RENDER PIXELS
# - EDIT AND EVALUATE CODE

# %% [markdown]
# 5. What's next?

# %%
Plot.Column(
    {"gap": 10, "className": "text-xl p-5"},
    ["div.font-bold", "What's Next?"],
    [
        "ul.list-disc.space-y-6.pl-5",
        ["li", "LLM prompt"],
        ["li", "3D viewer"],
        ["li", "...discuss!"],
    ],
)

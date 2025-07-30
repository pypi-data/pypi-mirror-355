# %% [markdown]
# # Colight JavaScript Import Guide
#
# Import JavaScript code from URLs, files, or inline source into your Colight plots.
#
# %% [markdown]
# ## Quick examples
#
# %%
# Import from CDN
import colight.plot as Plot

Plot.Import(source="https://cdn.skypack.dev/lodash-es", refer=["sum"]) | Plot.js(
    "sum([1, 2, 3])"
)

# %%
# Import inline source
Plot.Import(
    source="""
    export const greet = name => `Hello ${name}!`;
    """,
    refer=["greet"],
) | Plot.js("greet('world')")

# ## Things to know
# - Imports don't affect the global namespace: a `Plot.Import` only applies to the plot it is included in.
# - Imports are processed in the order they appear.
# - Imported modules are cached to avoid reloading.
# - ES Modules (ESM) format is supported by default. CommonJS modules can be used by setting format="commonjs". Differences:
#   - ESM can load from HTTP via `import` but can't access other plot imports
#   - CommonJS cannot load external modules (eg. `require` won't work) but can access other plot imports by reading from `colight.imports`
#
# ## Import Sources
# There are three ways to provide JavaScript code to import:
#
# - Remote URL: Import from a CDN or web URL starting with http(s)://
# - Local file: Import from a local file using "path:" prefix (relative to working directory)
# - Inline: Import JavaScript source code directly as a string
#
# ## Import Options
# Control how imports are exposed in your code:
#
# - `source`: Required. The JavaScript code to import (URL, file path, or inline code)
# - `alias`: Create a namespace object containing all exports
# - `default`: Import the default export with a specific name
# - `refer`: List of named exports to import
# - `refer_all`: Import all named exports (except those in `exclude`)
# - `rename`: Rename specific imports to avoid conflicts
# - `exclude`: List of exports to exclude when using `refer_all`
# - `format`: Module format - "esm" (default) or "commonjs"
#
# ## Colight API Access
# Your JavaScript code can access:
# - `colight.imports`: Previous imports in the current plot (only for CommonJS imports)
# - `React`, `d3`, `html` (for hiccup) and `colight.api` are defined globally
# %%
import colight.plot as Plot

# %%
# CDN import showing namespace alias and selective imports
Plot.Import(
    source="https://cdn.skypack.dev/lodash-es",
    alias="_",
    refer=["flattenDeep", "partition"],
    rename={"flattenDeep": "deepFlatten"},
) | Plot.js("deepFlatten([1, [2, [3, 4]]])")
# JS equivalent:
# import * as _ from "https://cdn.skypack.dev/lodash-es"
# import { flattenDeep as deepFlatten, partition } from "https://cdn.skypack.dev/lodash-es"

# %%
# Local file import - useful for project-specific code
Plot.Import(source="path:docs/system-guide/sample.js", refer=["formatDate"]) | Plot.js(
    "formatDate(new Date())"
)
# JS equivalent:
# import { formatDate } from "./docs/system-guide/sample.js"

# %%
# Inline source with namespace and selective exports
Plot.Import(
    source="""
    export const add = (a, b) => a + b;
    export const subtract = (a, b) => a - b;
    export const multiply = (a, b) => a * b;
    """,
    refer_all=True,
    alias="math",
    exclude=["multiply"],
) | Plot.js("[add(5, 3), subtract(5, 3), typeof multiply, math.multiply(3, 3), ]")
# JS equivalent:
# import * as math from "[inline module]"
# import { add, subtract } from "[inline module]"

# %%
# Cherry-picking specific functions from a module
Plot.Import(
    source="https://cdn.skypack.dev/d3-scale",
    refer=["scaleLinear", "scaleLog", "scaleTime"],
) | Plot.js("scaleLinear().domain([0, 1]).range([0, 100])(0.5)")
# JS equivalent:
# import { scaleLinear, scaleLog, scaleTime } from "https://cdn.skypack.dev/d3-scale"

# %%
# Using colight.api utilities
Plot.Import(
    source="""
    const {html} = colight.api;
    export const greeting = (name) => html(["div.p-5.bg-green-100", name])
    """,
    refer=["greeting"],
) | Plot.js("greeting('friend')")
# JS equivalent:
# import { greeting } from "[inline module]"

# %%
# CommonJS modules can access previous `colight.imports`
(
    Plot.Import(
        source="""
    export const add = (a, b) => a + b;
    """,
        refer=["add"],
    )
    | Plot.Import(
        source="""
    const {add} = colight.imports;
    module.exports.addTwice = (x) => add(x, x);
    """,
        format="commonjs",
        refer=["addTwice"],
    )
    | Plot.js("addTwice(5)")
)

# %% [markdown]
# ## Plot.Import vs Plot.js
#
# `Plot.Import` and `Plot.js` serve different purposes:
#
# - `Plot.js`: Used to create and control your plots, reactively computed, using $state. Often this is all you need.
# - `Plot.Import`: Used to define reusable code, functions and dependencies that can be used in `Plot.js`.
#
# #### Scope Access
# - `Plot.js`'s scope includes `$state`, `html`, `d3`, all imports, and `colight.api`.
# - `Plot.Import`'s scope includes `colight.api`. If `format="commonjs"`, then `colight.imports` are also available.
#
# %%
# Direct scope access in Plot.js
Plot.Import(
    source="""
    export const message = "Hello!";
    """,
    refer=["message"],
) | Plot.js("message")  # Direct access to 'message'

# %%
# Must use colight and commonjs format in Plot.Import
(
    Plot.Import(
        source="""
        export const message = "Hello!";
        """,
        refer=["message"],
    )
    | Plot.Import(
        source="""
        const { message } = colight.imports;  // Access previous imports
        exports.echo = () => message;
        """,
        refer=["echo"],
        format="commonjs",
    )
    | Plot.js("echo()")
)

# %% [markdown]
# ### Reactivity
# - `Plot.js` automatically re-runs when `$state` changes
# - `Plot.Import` code runs once at import time
# - Functions in `Plot.Import` can be reactive by accepting `$state` parameter
#
# %%
# Interactive counter example
(
    Plot.Import(
        source="""
    const { html } = colight.api;
    export const Counter = ($state) => {
        return html([
            "div.p-3",
            ["div.text-lg.mb-2", `Count: ${$state.count}`],
            ["button.px-4.py-2.bg-blue-500.text-white.rounded",
             { onClick: () => $state.count ++ },
             "Increment"]
        ]);
    };
    """,
        refer=["Counter"],
    )
    | Plot.js("Counter($state)")
    | Plot.initialState({"count": 0})
)

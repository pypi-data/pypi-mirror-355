# %%
# when js has computed state, it updates in the same transaction as its dependencies

import colight.plot as Plot
from colight.plot import js

(
    Plot.initialState(
        {"clicks": 0, "doubled": js("$state.clicks * 2"), "tripled": 0}, sync=True
    )
    | Plot.onChange(
        {
            "clicks": Plot.js(
                "() => $state.update(['tripled', 'reset', $state.clicks * 3])"
            )
        }
    )
    | Plot.html(
        [
            "div",
            {"onClick": js("(e) => $state.update({'clicks': $state.clicks + 1})")},
            "CLICKS: ",
            js("console.log($state.clicks) || $state.clicks"),
            ", DOUBLED: ",
            js("console.log($state.doubled) || $state.doubled"),
        ]
    )
    | Plot.onChange(
        {"clicks": lambda w, e: print(w.state.clicks, w.state.doubled, w.state.tripled)}
    )
)

# %%
# when python has onChange listeners, they are called after an entire update-list from js is sent

import colight.plot as Plot
from colight.plot import js

(
    Plot.initialState(
        {"a": 0, "b": 0, "c": 0},
        sync=True,
    )
    | Plot.html(
        [
            "div",
            {
                "onClick": js(
                    "(e) => $state.update(['a', 'reset', $state.a + 1], ['b', 'reset', $state.b + 1])"
                )
            },
            "Update a + b: ",
            js("$state.a"),
            ", ",
            js("$state.b"),
        ]
    )
    | Plot.onChange({"a": lambda w, e: print(w.state.a, w.state.b)})
)

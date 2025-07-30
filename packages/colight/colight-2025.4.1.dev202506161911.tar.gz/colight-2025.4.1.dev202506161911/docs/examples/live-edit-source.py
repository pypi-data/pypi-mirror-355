# %% [markdown]
# This example demonstrates how to create an interactive code editor with live evaluation and plotting. You'll see state management using `Plot.initialState`, `widget.state.update`, and `Plot.onChange`, as well as live code evaluation using Python's `exec`.

# %%
import jax
import jax.numpy as jnp
import colight.plot as Plot
from colight.plot import js

key = jax.random.key(314159)
thetas = jnp.arange(0.0, 1.0, 0.0005)

sigma = 0.05


def noisy_jax_model(key, theta, sigma):
    # Sample a bernoulli random variable to determine which noise model to use
    b = jax.random.bernoulli(key, theta)
    # If b=True: noise proportional to theta, if b=False: constant noise plus linear term
    return jax.lax.cond(
        b,
        lambda theta: jax.random.normal(key) * sigma * theta,
        lambda theta: jax.random.normal(key) * sigma + theta * 2,
        theta,
    )


def make_samples(key, thetas, sigma, model_func):
    # Vectorize model over array of thetas using unique random keys for each
    return jax.vmap(model_func, in_axes=(0, 0, None))(
        jax.random.split(key, len(thetas)), thetas, sigma
    )


initial_source = """sigma = 0.05
def noisy_jax_model(key, theta, sigma):
    # Sample a bernoulli random variable to determine which noise model to use
    b = jax.random.bernoulli(key, theta)
    # If b=True: noise proportional to theta, if b=False: constant noise plus linear term
    return jax.lax.cond(
        b,
        lambda theta: jax.random.normal(key) * sigma * theta,
        lambda theta: jax.random.normal(key) * sigma + theta * 2,
        theta,
    )"""

initial_state = Plot.initialState(
    {
        "samples": make_samples(key, thetas, sigma, noisy_jax_model),
        "thetas": thetas,
        "toEval": "",
        "source": initial_source,
    }
)


# Callback function
def evaluate(widget, _e):
    # Update random key and evaluate new code from text editor
    global key, sigma, noisy_jax_model
    key, subkey = jax.random.split(key, 2)
    source = f"global sigma, noisy_jax_model\n{widget.state.toEval}"
    exec(source)
    widget.state.update(
        {"samples": make_samples(subkey, thetas, sigma, noisy_jax_model)}
    )


# %% [markdown]
# `Plot.dot` will render our samples as a scatter plot. We pass `$state.thetas` and `$state.samples` in columnar format.

# %%
samples_plot = Plot.dot(
    {"x": js("$state.thetas"), "y": js("$state.samples")}, fill="rgba(0, 128, 128, 0.3)"
) + {"height": 400}

# %%
(
    initial_state
    | Plot.onChange({"toEval": evaluate})
    | Plot.html(
        [
            "form.!flex.flex-col.gap-3",
            {
                "onSubmit": js(
                    "e => { e.preventDefault(); $state.toEval = $state.source}"
                )
            },
            samples_plot,
            [
                "textarea.whitespace-pre-wrap.text-[13px].lh-normal.p-3.rounded-md.bg-gray-100.flex-1.h-[300px].font-mono",
                {
                    "rows": js("$state.source.split('\\n').length+1"),
                    "onChange": js("(e) => $state.source = e.target.value"),
                    "value": js("$state.source"),
                    "onKeyDown": js(
                        "(e) => { if (e.ctrlKey && e.key === 'Enter') { e.stopPropagation(); $state.toEval = $state.source } }"
                    ),
                },
            ],
            [
                "div.flex.items-stretch",
                [
                    "button.flex-auto.!bg-blue-500.!hover:bg-blue-600.text-white.text-center.px-4.py-2.rounded-md.cursor-pointer",
                    {"type": "submit"},
                    "Evaluate and Plot",
                ],
                [
                    "div.flex.items-center.p-2",
                    {
                        "onClick": lambda widget, _: widget.state.update(
                            {"source": initial_source}
                        )
                    },
                    "Reset Source",
                ],
            ],
        ]
    )
)

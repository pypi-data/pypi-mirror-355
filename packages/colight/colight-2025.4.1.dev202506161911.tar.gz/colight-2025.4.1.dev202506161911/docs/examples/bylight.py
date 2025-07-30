# %% [markdown]

# This example demonstrates how to create synchronized highlights across multiple elements using the [Bylight library](https://github.com/mhuebert/bylight?tab=readme-ov-file#bylight) in Colight.

# %% [markdown]
# First, let's import the necessary libraries and define our sample text:

# %%
import colight.plot as Plot

rhyme = """Roses are blue,
Violets are red,
In this rhyme's hue,
Colors are misled!"""

# %% [markdown]

# Use the `Plot.bylight` function to highlight specific words in our text:

# %%
Plot.bylight(rhyme, ["blue", "red", "Colors", "misled!"])

# %% [markdown]
# ## Animated Highlighting

# We can create an animated version that highlights each word in sequence.
# `Plot.Frames` creates a reactive variable that we access via [$state.frame](bylight:). In this example we [hide the slider](bylight:?match=slider=False).

# %%

Plot.Frames(
    [
        Plot.js("`frame: ${$state.frame}`") & Plot.bylight(rhyme, pattern)
        for pattern in rhyme.split()
    ],
    fps=2,
    slider=False,
)

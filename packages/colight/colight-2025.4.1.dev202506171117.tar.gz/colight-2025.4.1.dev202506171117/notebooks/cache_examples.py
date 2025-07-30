# %%

import colight.plot as Plot

# Only one console.log, Plot marks are automatically wrapped in Plot.ref(); all usages point to the same instance.
data = [[1, 2], [3, 4], [5, Plot.js("console.log('evaluating cached data') || 6")]]
d = Plot.dot(data)
d & d

# %% Frames
# Only one console.log, Plot marks are automatically wrapped in Plot.ref().
Plot.Frames([d for _ in range(6)], fps=2)

# %% Multiple marks wrapped in Plot.ref()
Plot.new(Plot.ref(Plot.dot([[2, 2]]) + Plot.dot([[1, 1]])))

# %% Add a mark to a ref mark
Plot.dot([[1, 1]]) + Plot.ref(Plot.dot([[2, 2]]))

# %%

import colight.plot as Plot

data1 = Plot.ref(["div", 1, 2, 3])
data2 = Plot.ref(["div", 9, 9, 9])
widget = (Plot.html(data1) & Plot.html(data2)).display_as("widget")
widget

# %% Updating refs
widget.state.update([data1, "append", 4])

widget.state.update([data2, "concat", [5, 6]])

# %% Tailed Widget Example

tailedData = Plot.ref([1, 2, 3])
tailedWidget = Plot.Frames(tailedData, tail=True, fps=2).widget()
tailedWidget


# %% Updating Tailed Widget
tailedWidget.state.update([tailedData, "concat", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]])

# %% initialize a variable
# We should see '123' logged once.
Plot.initialState({"foo": 123}) & Plot.js("console.log($state.foo) || $state.foo")

import colight.plot as Plot
from IPython.display import display

p = Plot.new()
display(p)

p.reset(Plot.initialState({"foo": "foo"}) | Plot.js("$state.foo"))

p.reset(Plot.initialState({"blah": "blah"}) | Plot.js("$state.blah"))

# %%

one = Plot.ref(Plot.js("$state.foo"))
two = Plot.ref(Plot.js("$state.bar"))
plot = Plot.new() | Plot.initialState({"foo": "FOO", "bar": "BAR"})
plot

plot.reset(one)

plot.reset(two)

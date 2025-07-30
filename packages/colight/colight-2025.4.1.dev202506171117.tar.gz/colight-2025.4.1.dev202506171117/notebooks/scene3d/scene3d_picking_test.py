# %% Common imports and configuration
import numpy as np
from colight.scene3d import (
    Ellipsoid,
    Cuboid,
    LineBeams,
    PointCloud,
    deco,
)
from colight.plot import js

# Common camera parameters
DEFAULT_CAMERA = {"up": [0, 0, 1], "fov": 45, "near": 0.1, "far": 100}

# %% 1) Point Cloud Picking
print("Test 1: Point Cloud Picking.\nHover over points to highlight them in yellow.")

scene_points = PointCloud(
    centers=np.array([[-2, 0, 0], [-2, 0, 1], [-2, 1, 0], [-2, 1, 1]]),
    colors=np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 0, 1]]),
    size=0.2,
    alpha=0.7,
    onHover=js("(i) => $state.update({hover_point: typeof i === 'number' ? [i] : []})"),
    decorations=[
        deco(
            js("$state.hover_point"),
            color=[1, 1, 0],
            scale=1.5,
        ),
        deco([0], scale=4),
        deco(None, scale=[1.2, 0.8, 1.0]),
    ],
) + (
    {
        "defaultCamera": {
            **DEFAULT_CAMERA,
            "position": [-4, 2, 2],
            "target": [-2, 0.5, 0.5],
        }
    }
)

# 2) Ellipsoid Picking
print(
    "Test 2: Ellipsoid and Axes Picking.\nHover over ellipsoids or their axes to highlight them independently."
)

scene_ellipsoids = (
    Ellipsoid(
        centers=np.array([[0, 0, 0], [0, 1, 0], [0, 0.5, 1]]),
        colors=np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]]),
        half_size=[0.4, 0.4, 0.4],
        alpha=0.7,
        quaternions=np.array(
            [[1, 0, 0, 0], [0, 0.707, 0, 0.707], [0.5, 0, 0.5, 0.707]]
        ),
        onHover=js(
            "(i) => $state.update({hover_ellipsoid: typeof i === 'number' ? [i] : []})"
        ),
        decorations=[
            deco(
                js("$state.hover_ellipsoid"),
                color=[1, 1, 0],
                scale=1.2,
            ),
            deco([0], scale=1.5),
            deco([1], scale=0.5),
        ],
    )
    + Ellipsoid(
        centers=np.array([[-1, 0, 0], [-1, 1, 0], [-1, 0.5, 1]]),
        colors=np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]]),
        half_size=0.4,
        alpha=0.5,
        onHover=js(
            "(i) => $state.update({hover_ellipsoid_2: typeof i === 'number' ? [i] : []})"
        ),
        decorations=[
            deco(
                js("$state.hover_ellipsoid_2"),
                color=[1, 1, 0],
                scale=1.2,
            ),
            deco([0], scale=1.5),
            deco([1], scale=0.5),
        ],
    )
    + Ellipsoid(
        fill_mode="MajorWireframe",
        centers=np.array(
            [[1, 0, 0], [1, 1, 0], [1, 0.5, 1]]
        ),  # Offset by 1 in x direction
        color=[0, 1, 0],
        half_sizes=[0.4, 0.4, 0.4],
        alpha=0.8,
        quaternions=np.array(
            [[0.866, 0, 0.5, 0], [0.707, 0.707, 0, 0], [0.5, 0.5, 0.5, 0.5]]
        ),
        onHover=js(
            "(i) => $state.update({hover_axes: typeof i === 'number' ? [i] : []})"
        ),
        decorations=[
            deco(
                js("$state.hover_axes"),
                color=[1, 1, 0],
            ),
            deco([0], scale=1.5),
            deco([1], scale=0.5),
        ],
    )
    + (
        {
            "defaultCamera": {
                **DEFAULT_CAMERA,
                "position": [2, 2, 2],
                "target": [
                    0.5,
                    0.5,
                    0.5,
                ],  # Adjusted target to center between ellipsoids and axes
            }
        }
    )
)

# 3) Cuboid Picking with Transparency
print(
    "Test 3: Cuboid Picking with Transparency.\nHover behavior with semi-transparent objects."
)

scene_cuboids = Cuboid(
    centers=np.array([[2, 0, 0], [2, 0, 1], [2, 0, 2]]),
    colors=np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]]),
    alphas=np.array([0.5, 0.7, 0.9]),
    half_size=0.4,
    quaternions=np.array([[1, 0, 0, 0], [0.707, 0, 0.707, 0], [0.5, 0.5, 0.5, 0.5]]),
    onHover=js(
        "(i) => $state.update({hover_cuboid: typeof i === 'number' ? [i] : []})"
    ),
    decorations=[
        deco(
            js("$state.hover_cuboid"),
            color=[1, 1, 0],
            alpha=1.0,
            scale=1.1,
        ),
        deco([0], scale=1.5),
        deco([1], scale=0.5),
    ],
) + (
    {
        "defaultCamera": {
            **DEFAULT_CAMERA,
            "position": [4, 2, 2],
            "target": [2, 0, 0.5],
        }
    }
)
scene_cuboids

# 4) Line Beams Picking
print("Test 4: Line Beams Picking.\nHover over line segments.")

scene_beams = LineBeams(
    points=np.array(
        [
            -2,
            -2,
            0,
            0,  # start x,y,z, dummy
            -1,
            -2,
            1,
            0,  # end x,y,z, dummy
            -1,
            -2,
            0,
            0,  # start of second beam
            -2,
            -2,
            1,
            0,  # end of second beam
        ],
        dtype=np.float32,
    ).reshape(-1),
    colors=np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]]),
    size=0.06,
    alpha=0.7,
    quaternions=np.array([[1, 0, 0, 0], [0.707, 0, 0.707, 0]]),
    onHover=js("(i) => $state.update({hover_beam: typeof i === 'number' ? [i] : []})"),
    decorations=[
        deco(
            js("$state.hover_beam"),
            color=[1, 1, 0],
        ),
        deco(None, scale=[1.2, 0.8, 1.0]),
    ],
) + (
    {
        "defaultCamera": {
            **DEFAULT_CAMERA,
            "position": [-4, -4, 2],
            "target": [-1.5, -2, 0.5],
        }
    }
)

# 5) Mixed Components Picking
print(
    "Test 5: Mixed Components Picking.\nTest picking behavior with overlapping different primitives."
)

mixed_scene = (
    Ellipsoid(
        centers=np.array([[2, -2, 0.5]]),
        colors=np.array([[1, 0, 0]]),
        half_sizes=[0.5, 0.5, 0.5],
        quaternions=np.array([[0.707, 0, 0.707, 0]]),
        onHover=js(
            "(i) => $state.update({hover_mixed_ellipsoid: typeof i === 'number' ? [i] : []})"
        ),
        decorations=[
            deco(
                js("$state.hover_mixed_ellipsoid"),
                color=[1, 1, 0],
            ),
            deco(None, scale=[1.5, 0.7, 1.0]),
        ],
    )
    + PointCloud(
        centers=np.array([[2, -2, 0], [2, -2, 1]]),
        colors=np.array([[0, 1, 0], [0, 0, 1]]),
        size=0.2,
        quaternions=np.array([[1, 0, 0, 0], [0.707, 0.707, 0, 0]]),
        onHover=js(
            "(i) => $state.update({hover_mixed_point: typeof i === 'number' ? [i] : []})"
        ),
        decorations=[
            deco(
                js("$state.hover_mixed_point"),
                color=[1, 1, 0],
            ),
            deco(None, scale=[0.8, 1.2, 1.0]),
        ],
    )
    + (
        {
            "defaultCamera": {
                **DEFAULT_CAMERA,
                "position": [4, -4, 2],
                "target": [2, -2, 0.5],
            }
        }
    )
)

(scene_points & scene_beams | scene_cuboids & scene_ellipsoids | mixed_scene)

# %% 6) Generated Cuboid Grid Picking
print(
    "Test 6: Generated Cuboid Grid.\nHover over cuboids in a programmatically generated grid pattern."
)

# Generate a 4x4x2 grid of cuboids with systematic colors
x, y, z = np.meshgrid(
    np.linspace(4, 5.5, 4), np.linspace(-2, -0.5, 4), np.linspace(0, 1, 2)
)
centers = np.column_stack((x.ravel(), y.ravel(), z.ravel()))

# Generate colors based on position
colors = np.zeros((len(centers), 3))
colors[:, 0] = (centers[:, 0] - centers[:, 0].min()) / (
    centers[:, 0].max() - centers[:, 0].min()
)
colors[:, 1] = (centers[:, 1] - centers[:, 1].min()) / (
    centers[:, 1].max() - centers[:, 1].min()
)
colors[:, 2] = (centers[:, 2] - centers[:, 2].min()) / (
    centers[:, 2].max() - centers[:, 2].min()
)

scene_grid_cuboids = (
    Cuboid(
        centers=centers[: len(centers) // 2],
        colors=colors[: len(colors) // 2],
        half_sizes=[0.15],
        alpha=0.85,
        onHover=js(
            "(i) => $state.update({hover_grid_cuboid1: typeof i === 'number' ? [i] : []})"
        ),
        decorations=[
            deco(
                js("$state.hover_grid_cuboid1"),
                color=[1, 1, 0],
                scale=1.2,
            ),
        ],
    )
    + Cuboid(
        centers=centers[len(centers) // 2 :],
        colors=colors[len(colors) // 2 :],
        half_sizes=[0.15],
        alpha=0.85,
        onHover=js(
            "(i) => $state.update({hover_grid_cuboid2: typeof i === 'number' ? [i] : []})"
        ),
        decorations=[
            deco(
                js("$state.hover_grid_cuboid2"),
                color=[1, 1, 0],
                scale=1.2,
            ),
        ],
    )
    + (
        {
            "defaultCamera": {
                **DEFAULT_CAMERA,
                "position": [6, -4, 2],
                "target": [4.75, -1.25, 0.5],
            }
        }
    )
)

(
    scene_points & scene_beams
    | scene_cuboids & scene_ellipsoids
    | mixed_scene & scene_grid_cuboids
)

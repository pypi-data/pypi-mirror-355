import traceback

from stgem.features import *
from stgem.exceptions import FeatureNotFoundError


def test_fv_get_set():
    # Test multiple features with the same name.
    try:
        fv = FeatureVector(name="", features=[Real("x1", 0, 1), Real("x1", 0, 1)])
    except AssertionError:
        pass

    fv = FeatureVector(name="FV",
                       features=[
                           Real("e1", -100, 100, clip=True),
                           Real("e2", 100, 200),
                           FeatureVector(name="e3",
                                         features=[
                                             Real("d1", -100, 100),
                                             Real("d2", 100, 200),
                                         ]),
                           Real("e4", 0, 500),
                       ])

    assert fv.name == "FV"

    # Check for feature existence.
    assert "e1" in fv
    assert "foo" not in fv
    assert fv.names == ["e1", "e2", "e3", "e4"]

    # Check for accessing features.
    assert fv.feature("e1") is fv._features[0]
    assert fv.feature("e3") is fv._features[2]
    assert fv.feature("e3.d1") is fv._features[2]._features[0]
    try:
        fv.feature("foo")
        assert False
    except FeatureNotFoundError:
        pass

    # Check for feature values.
    assert fv.e1 is None
    try:
        fv.set([-100])
        assert False
    except Exception as E:
        if not E.args[0].startswith("Cannot set"):
            traceback.print_exc()
            raise
    try:
        fv.set([-100, 150, 0, 250])
        assert False
    except ValueError:
        pass
    fv.set([-100, 150, [50, 175], 250])
    try:
        fv.foo == 5
        assert False
    except AttributeError:
        pass
    assert fv.e1 == -100
    assert fv["e1"] == -100
    assert fv[0] == -100
    assert fv.e3.d1 == 50
    assert fv["e3.d1"] == 50
    assert isinstance(fv.e3, FeatureVector)
    assert fv["e3"][0] == 50

    # Check setting feature values.
    fv.e1 = 0
    assert fv.e1 == 0
    try:
        fv.foo = 5
        assert False
    except AttributeError:
        pass
    fv.e3.d1 = 0
    assert fv.e3.d1 == 0
    fv["e1"] = -100
    assert fv["e1"] == -100
    fv["e3"]["d1"] = 50
    assert fv["e3.d1"] == 50
    fv[1] = 120
    assert fv["e2"] == 120
    fv["e3"][1] = 111
    assert fv["e3.d2"] == 111

    # Test for clipping.
    fv["e1"] = 110
    assert fv["e1"] == 100
    fv.e1 = -500
    assert fv.e1 == -100


def test_fv_dict():
    # Test converting to dictionary.
    fv = FeatureVector(name="FV",
                       features=[
                           Real("e1", -100, 100),
                           Real("e2", 100, 200),
                           FeatureVector(name="e3",
                                         features=[
                                             Real("d1", -100, 100),
                                             Real("d2", 100, 200),
                                         ]),
                           Real("e4", 0, 500),
                       ]).set([-100, 150, [50, 175], 250])

    d = {
        "e1": -100,
        "e2": 150,
        "e3": {
            "d1": 50,
            "d2": 175
        },
        "e4": 250
    }

    assert fv.to_dict() == d

    # Test the merge of two feature vectors using the operator |.
    fv2 = FeatureVector(name="FV2",
                        features=[
                            Real("e1", -200, 200),
                            Real("e5", 0, 10)
                        ]).set([0, 5])
    v = fv | fv2
    d = {
        "e1": 0,
        "e2": 150,
        "e3": {
            "d1": 50,
            "d2": 175
        },
        "e4": 250,
        "e5": 5
    }

    assert v.name == "FV"
    assert v.to_dict() == d


def test_fv_pack():
    # Test packing and unpacking without ranges.
    fv = FeatureVector(features=[RealVector(2, name="x")])
    try:
        fv.pack()
        assert False
    except Exception as E:
        if not E.args[0].startswith("Cannot pack without value range information."):
            traceback.print_exc()
            raise
    fv = FeatureVector(features=[Real(name="x")])
    try:
        fv.pack()
        assert False
    except Exception as E:
        if not E.args[0].startswith("Cannot pack without value range information."):
            traceback.print_exc()
            raise

    # Test packing with uninitialized values.
    features = [
        RealVector(2, name="x", min_value=0, max_value=500),
        Real("e1", -100, 100),
        PiecewiseConstantSignal([5]*1, min_value=0, max_value=100)
    ]
    for f in features:
        try:
            f.pack()
            assert False
        except ValueError:
            pass

    # Test packing and unpacking of Reals and RealVectors.
    fv = FeatureVector(features=[
        Real("e1", -100, 100),
        Real("e2", 100, 200),
        FeatureVector(name="e3",
                      features=[
                          Real("d1", -100, 100),
                          Real("d2", 100, 200),
                      ]),
        RealVector(2, name="e4", min_value=0, max_value=500)
    ]).set([-100, 150, [-50, 175], [0, 500]])
    d = {
        "e1": -100,
        "e2": 150,
        "e3": {
            "d1": -50,
            "d2": 175
        },
        "e4": [0, 500]
    }
    packed = np.array([-1, 0, -0.5, 0.5, -1, 1])

    assert len(fv) == 4
    assert fv.dimension == 6

    assert np.array_equal(fv.pack(), packed)
    assert fv.unpack(packed).to_list()[:3] == [-100.0, 150.0, [-50.0, 175.0]]
    assert np.array_equal(fv.unpack(packed).to_list()[-1], np.array([0, 500]))
    fv.set([100, 200, [100, 200], [500, 0]])
    fv.set_packed(packed)
    d2 = fv.to_dict()
    for k in ["e1", "e2", "e3"]:
        assert d2[k] == d[k]
    assert np.array_equal(d2["e4"], d["e4"])

    # Test packing and unpacking of signal representations.
    fv = FeatureVector(features=[
        PiecewiseConstantSignal([10] * 5, name="e1", min_value=1, max_value=5),
        Real("e2", 100, 200),
        PiecewiseConstantSignal([5] * 3, name="e3", min_value=-100, max_value=100)
    ]).set([[5, 4, 3, 2, 1], 150, [-100, 0, 100]])
    d = {
        "e1": [5, 4, 3, 2, 1],
        "e2": 150,
        "e3": [-100, 0, 100]
    }

    packed = np.array([1.0, 0.5, 0.0, -0.5, -1.0, 0.0, -1.0, 0, 1.0])

    assert len(fv) == 3
    assert fv.dimension == 5 + 1 + 3

    assert np.array_equal(fv.pack(), packed)
    assert np.array_equal(fv.unpack(packed)[0], np.array([5, 4, 3, 2, 1]))
    assert fv.unpack(packed)[1] == 150
    assert np.array_equal(fv.unpack(packed)[2], np.array([-100, 0, 100]))
    fv.set([[1] * 5, 100, [100] * 3])
    fv.set_packed(packed)
    d2 = fv.to_dict()
    assert np.array_equal(d2["e1"], d["e1"])
    assert d2["e2"] == d["e2"]
    assert np.array_equal(d2["e3"], d["e3"])


def test_fv_custom():
    """Test a custom feature."""

    Obstacle = FeatureVector(features=[
        Real("x", -100, 100),
        Real("y", -100, 100),
        Real("length", 0, 200),
        Real("angle", 0, 360),
    ])

    fvuav = FeatureVector(features=[
        Obstacle("obstacle1"),
        Obstacle("obstacle2"),
        Obstacle("obstacle3")
    ])

    assert fvuav.dimension == 3 * 4

    fvuav.obstacle1.x = 100
    fvuav.obstacle1.y = 100
    fvuav.obstacle2.x = 0
    fvuav.obstacle2.y = 0


def test_synthesize():
    fv = FeatureVector(
        name="inputs",
        features=[
            PiecewiseConstantSignal(
                name="THROTTLE",
                min_value=0,
                max_value=100,
                piece_durations=[5] * 6,
                sampling_period=0.01
            ),
            PiecewiseConstantSignal(
                name="BRAKE",
                min_value=0,
                max_value=325,
                piece_durations=[5] * 6,
                sampling_period=0.1
            )
        ]
    )
    fv.set([[1, 2, 3, 4, 5, 6], [6, 5, 4, 3, 2, 1]])

    t, v = fv.feature("THROTTLE").synthesize_signal()
    assert len(t) == int(30 / 0.01) + 1
    assert t[0] == 0
    assert t[-1] == 30
    for i in range(6):
        assert v[int(i * 5 / 0.01)] == i + 1

    t, v = fv.feature("BRAKE").synthesize_signal()
    assert len(t) == int(30 / 0.1) + 1
    assert t[0] == 0
    assert t[-1] == 30
    for i in range(6):
        assert v[int(i * 5 / 0.1)] == 6 - i
    
    fv = FeatureVector(
        name="inputs",
        features=[
            PiecewiseLinearSignal(
                name="SLOPES",
                min_value=-5,
                max_value=95,
                piece_durations=[3, 2, 5],
                sampling_period=0.1
            )
        ]
    )
    fv.set([[0, 10, -5, 95]])
    
    t, v = fv.feature("SLOPES").synthesize_signal()
    eps = 0.00001
    for i in range(len(t)):
        if t[i] <= 3:
            a = (10/3)
            b = 0
        elif t[i] <= 3 + 2:
            a = -15/2
            b = 10 - 3*a
        elif t[i] <= 3 + 2 + 5:
            a = 100/5
            b = -5*(1 + a)
        assert abs(v[i] - (a*t[i] + b)) < eps

def test_iteration():
    fv = FeatureVector(features=[
        Real("v1"),
        Real("v2")
    ])
    for f in fv:
        assert isinstance(f, Real)

import os
import urllib.request

from stgem.features import FeatureVector, PiecewiseConstantSignal, Signal
from stgem.limit import ExecutionCount
from stgem.system.fmu import FMU
from stgem.task import generate_critical_tests


def download_files(dir, url_list):
    for url in url_list:
        name = url.rsplit('/', 1)[-1]

        # Combine the name and the downloads directory to get the local filename
        filename = os.path.join(dir, name)

        # Download the file if it does not exist
        if not os.path.isfile(filename):
            urllib.request.urlretrieve(url, filename)


def test_fmu():
    download_files("data", [
        "https://github.com/modelica/fmi-cross-check/raw/master/fmus/2.0/cs/c-code/MapleSim/2018/CoupledClutches/CoupledClutches.fmu"])
    sut = FMU(model_file='data/CoupledClutches.fmu',
              inputs=FeatureVector(features=[
                  PiecewiseConstantSignal(name='input', min_value=0, max_value=1, piece_durations=[5] * 4,
                                          sampling_period=0.01)
              ]),
              outputs=FeatureVector(features=[
                  Signal(name='o1', min_value=0, max_value=10),
                  Signal(name='o2', min_value=0, max_value=10),
                  Signal(name='o3', min_value=0, max_value=10),
                  Signal(name='o4', min_value=0, max_value=10)
              ]))
    critical, all, tester = generate_critical_tests(
        sut=sut,
        formula='o1>0',
        limit=ExecutionCount(10),
        generator='Random'
    )

    print(all)


if __name__ == '__main__':
    test_fmu()

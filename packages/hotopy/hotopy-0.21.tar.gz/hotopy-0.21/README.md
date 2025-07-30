HoToPy - A toolbox for X-ray holo-tomography in Python

# HoToPy

## Installation

### pip installation

HoToPy can be installed through pip by running
```commandline
pip install hotopy
```
for a basic HoToPy installation. 

The basic version does not contain the [`astra-toolbox`][astra] for tomographic reconstructions. If you intend to use
the _tomographic reconstruction functions_ in `hotopy.tomo` you can install its dependencies either by running
```commandline
pip install hotopy[tomo]
```
or you can have a look at the [astra-toolbox][astra] documentation for an installation method that fits your needs.

## Getting started

You can find examples in the dedicated [HoToPy-Examples repository](https://gitlab.gwdg.de/irp/hotopy-examples).

## Documentation

https://irp.pages.gwdg.de/hotopy/

## Citation

If you use HoToPy, please cite

```
@misc{Lucht2025hotopy,
      title={HoToPy: A toolbox for X-ray holo-tomography in Python},
      author={Jens Lucht and Paul Meyer and Leon Merten Lohse and Tim Salditt},
      year={2025},
      eprint={2506.11567},
      archivePrefix={arXiv},
      primaryClass={physics.optics},
      url={https://arxiv.org/abs/2506.11567},
}
```

[holotomo]: https://gitlab.gwdg.de/irp/holotomotoolbox
[astra]: https://astra-toolbox.com/
[mircomamba]: https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html

# DjangoLDP CQCM Map

[![pypi](https://img.shields.io/pypi/v/djangoldp-cqcm-map)](https://pypi.org/project/djangoldp-cqcm-map/)

## Description

This packages is a Django package, based on DjangoLDP, that provides models requires by CQCM Map.

## Installation

This package is intended to be used as a dependency within a Django project that uses `djangoldp`.

### Install the package

```bash
pip install djangoldp-cqcm-map
```

### Configure your server

Add to `settings.yml`

Within your Django project's `settings.yml` file, add `djangoldp-cqcm-map` to the `dependencies` list and the wanted individual model packages to the `ldppackages` list. The order in `ldppackages` matters, so maintain the order shown below.

```yaml
dependencies:
  - djangoldp-cqcm-map

ldppackages:
  - djangoldp_cqcm_map
```

If you do not have a settings.yml file, you should follow the djangoldp server installation guide.

### Run migrations

```bash
./manage.py migrate
```

## Sample Data

A sample fixture is provided to demonstrate the structure and relationships of the models.

To load the sample data:

```bash
./manage.py loaddata cqcm_poles
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

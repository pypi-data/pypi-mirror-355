# AstDyS Python Wrapper

This is a Python wrapper for the [AstDyS catalogue](https://newton.spacedys.com/astdys2/index.php?pc=0) of asteroids in the Solar system, providing access to both osculating orbital elements and synthetic proper elements.

## Installation

```bash
pip install astdys
```

## Quick Start

```python
import astdys

# Get osculating elements for asteroid 1 (Ceres)
elements = astdys.search(1)
print(elements)

# Get synthetic proper elements for the same asteroid
astdys.set_type("synthetic")
proper_elements = astdys.search(1)
print(proper_elements)
```

## Usage

### Basic Search

Search for a single asteroid by number:

```python
import astdys

# Search for asteroid 1 (Ceres)
elements = astdys.search(1)
if elements:
    print(f"Semi-major axis: {elements['a']} AU")
    print(f"Eccentricity: {elements['e']}")
    print(f"Inclination: {elements['inc']} radians")
```

Search for multiple asteroids:

```python
# Search for multiple asteroids
objects = astdys.search([1, 2, 3, 4, 5])
for num, elements in objects.items():
    print(f"Asteroid {num}: a={elements['a']:.3f} AU")
```

### Search by Semi-major Axis

Find asteroids within a specific range of semi-major axis:

```python
# Find asteroids around 2.7 AU (with default sigma=0.1 AU)
asteroids = astdys.search_by_axis(2.70)
print(f"Found {len(asteroids)} asteroids")

# Use custom range (sigma=0.05 AU)
asteroids = astdys.search_by_axis(2.70, sigma=0.05)
print(asteroids[['a', 'e', 'inc']].head())
```

### Working with Different Catalog Types

The library supports two types of orbital elements:

#### Osculating Elements (Default)

Classical Keplerian orbital elements at a specific epoch:

```python
# Default catalog type is 'osculating'
astdys.set_type("osculating")  # This is the default
elements = astdys.search(1)

# Available elements:
# - a: semi-major axis (AU)
# - e: eccentricity
# - inc: inclination (radians)
# - Omega: longitude of ascending node (radians)
# - omega: argument of perihelion (radians)
# - M: mean anomaly (radians)
# - epoch: epoch (MJD)
```

#### Synthetic Proper Elements

Proper elements are averaged orbital elements that eliminate short-term perturbations, useful for asteroid family studies:

```python
# Switch to synthetic proper elements
astdys.set_type("synthetic")
elements = astdys.search(1)

# Available elements:
# - a: proper semi-major axis (AU)
# - e: proper eccentricity
# - sinI: sine of proper inclination
# - n: mean motion frequency (arcsec/year)
# - g: perihelion precession frequency (arcsec/year)
# - s: node precession frequency (arcsec/year)
# - lce: Lyapunov Characteristic Exponent
# - my: integration time (Myr)
# - mag: absolute magnitude
```

### Catalog Information

Get information about the catalog:

```python
# Get catalog epoch as string
date_str = astdys.catalog_time()
print(f"Catalog epoch: {date_str}")

# Get catalog epoch as datetime object
import astdys
date = astdys.datetime()
print(f"Catalog date: {date}")
```

### Rebuilding the Catalog

Force a fresh download and rebuild of the catalog:

```python
# This will download fresh data from AstDyS
astdys.rebuild()
```

### Angle Conversions

Note that angular elements (inclination, node, perihelion, mean anomaly) are returned in **radians**.

### Comparing osculating and proper elements

```python
import astdys

asteroid_num = 4  # Vesta

# Get osculating elements
astdys.set_type("osculating")
osc = astdys.search(asteroid_num)

# Get proper elements
astdys.set_type("synthetic")
prop = astdys.search(asteroid_num)

print("Osculating vs Proper elements:")
print(f"Semi-major axis: {osc['a']:.4f} vs {prop['a']:.4f} AU")
print(f"Eccentricity: {osc['e']:.4f} vs {prop['e']:.4f}")
```

## License

MIT

## Credits

This wrapper provides access to the AstDyS database. The AstDyS catalog and synthetic proper elements were created by:

**Zoran Knežević** (Astronomical Observatory, Belgrade) and **Andrea Milani** (University of Pisa)

Key references:

- Knežević, Z. & Milani, A. (2003). "Proper element catalogs and asteroid families." _Astronomy & Astrophysics_, 403, 1165-1173.
- Knežević, Z. & Milani, A. (2001). "Synthetic proper elements for outer main belt asteroids." _Celestial Mechanics and Dynamical Astronomy_, 78, 17-46.

The AstDyS service is available at: https://newton.spacedys.com/astdys2/

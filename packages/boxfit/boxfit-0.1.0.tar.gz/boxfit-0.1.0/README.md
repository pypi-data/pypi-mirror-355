# BoxFit: Volumetric Fit Algorithm

**BoxFit** is a fitting algorithm designed to account for uncertainites arising from detector resolution that result in no or unusual minimization. Unlike traditional methods that treat each "hit" as a point with associated uncertainties, BoxFit models each hit as a 3D volume of equal likelihood. This approach provides a more realistic representation of spatial uncertainty in low-resolution tracking detectors.

## Installation

You can install BoxFit using pip:

```
pip install boxfit


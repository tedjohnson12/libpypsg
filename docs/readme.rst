``PyPSG``
=========

A Python wrapper for the Planetary Spectrum Generator.

The goal of this package is to make PSG more accessible to
new users, but still be powerfull enough that expert users
will find it useful.

In the simplest use case, users can create a PSG config file from scratch
using the ``PyConfig`` class.


.. code-block:: python


    import pypsg

    cfg = pypsg.cfg.PyConfig(
        target=pypsg.cfg.Target(object='Exoplanet',name='Proxima Cen b')
        )
    print(cfg.content)

.. code-block:: none
    
    b'<OBJECT-NAME>Proxima Cen b\n<OBJECT>Exoplanet'

We can then call PSG with our setup.

.. code-block:: python

    psg = pypsg.APICall(
            cfg=cfg,
            output_type='rad',
        )
    response = psg()





Now let's take a look at the rad file we get back.
The ``PyRad`` class inherits from ``astropy.table.QTable``.

.. code-block:: python

    rad = response.rad

    rad

.. code-block:: none

    Wave/freq     Total          Object       Reflected       Thermal    
        um    W / (sr um m2) W / (sr um m2) W / (sr um m2) W / (sr um m2)
    float64     float64        float64        float64        float64    
    --------- -------------- -------------- -------------- --------------
        1.0      231.99203        231.992        231.992    1.76851e-13
        1.1      184.89523        184.895        184.895    8.59289e-12
        ...            ...            ...            ...            ...
        1.8       45.45587        45.4559        45.4559    1.69172e-05
        1.9      38.276023         38.276         38.276    5.24737e-05

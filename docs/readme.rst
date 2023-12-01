``PyPSG``
=========

A Python wrapper for the Planetary Spectrum Generator.

The goal of this package is to make PSG more accessible to
new users, but still be powerfull enough that expert users
will find it usefull.

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





Now let's take a look at the rad file we get back

.. code-block:: python

    rad = response.rad

    total = rad.total

    print(total.spectral_axis)
    print(total.flux)

.. code-block:: none

    [1.  1.1 1.2 1.3 1.4 1.5 1.6 1.7 1.8 1.9] um
    [231.99203  184.89523  148.08486  119.38777   96.962337  79.349429
      65.427132  54.343872  45.45587   38.276023] W / (sr um m2)

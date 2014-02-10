"""
PURPOSE
    To find the optimum aperture
"""
import sys
import numpy as np
import random as r
import getNoise as gn
import createSexConfig as sc
import createSexParam as sp
import phot_utils as pu
import Sources as S
import matplotlib.pyplot as plt
from subprocess import call
import Quadtree as q

def main():
    sname = "sign"
    nname = "noise"
    image = "NGC4374_i.fits"
    filter_file = "default.conv"

    x = []
    y = []
    for i in range(0,10000):
        x.append(r.uniform(1,10000))
        y.append(r.uniform(1,8000))

    output = open("MeasureFluxAt.txt", "w")
    for i in range(len(x)):
        output.write('%.3f' % x[i] + '%10.3f' % y[i]  + '\n')

    aperture = np.linspace(0.5, 10, num=1)
    #noise = gn.getNoise(aperture, name, filter_file, image,  False)

    sp.createSexParam(sname, False)
    sp.createSexParam(nname, True)
    sparam_file = sname + ".param"
    nparam_file = nname + ".param"
    assoc_file = "MeasureFluxAt.txt"

    signal = []
    noise = []
    for ap in aperture:
        sc.createSexConfig(sname, filter_file, sparam_file, "nill", ap, False)
        call(['sex', '-c', sname + '.config', image])

        sc.createSexConfig(nname, filter_file, nparam_file, assoc_file, ap, True)
        call(['sex', '-c', nname + '.config', image])

        scat = open(sname + ".cat")
        stmp = filter(lambda line: pu.noHead(line), scat)
        #ssources = map(lambda line: S.SCAMSource(line), stmp)
        #sflux = map(lambda s: s.mag_aper, ssources)
        #signal.append(pu.calcMAD(sflux))

        ncat = open(nname + ".cat")
        ntmp = filter(lambda line: pu.noHead(line), ncat)
        #nflux = map(lambda s: s.mag_aper, nsources)
        #noise.append(pu.calcMAD(nflux))

        # Make sure that the background measuresments don't overlap with the source detections
        # Also don't include mag_aper == 99.0
        quadtree = q.Quadtree(0, 0, 10000, 8000)
        map(lambda line: q.insertsource(quadtree, S.SCAMSource(line)), stmp )
        nsources = map(lambda line: S.SCAMSource(line), ntmp)

    snr = []
    for i in range(len(signal)):
        snr.append(signal[i]/noise[i])

    plt.plot(aperture, snr, linestyle='none', marker='o')
    plt.show()

if __name__ == '__main__':
    sys.exit(main())


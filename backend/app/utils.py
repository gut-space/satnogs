


def coords(lon, lat):
    t = "%2.4f" % lat
    if (lat>0):
        t += "N"
    else:
        t += "S"

    t += " %2.4f" % lon
    if (lon>0):
        t += "E"
    else:
        t += "W"
    return t
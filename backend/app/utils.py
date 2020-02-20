import subprocess

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

def make_thumbnail(input_path, output_path, width=200):
    subprocess.check_call(["convert" ,"-thumbnail", str(width), input_path, output_path])
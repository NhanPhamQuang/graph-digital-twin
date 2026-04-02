import os

def build():
    os.system(
        "netconvert "
        "--osm-files data/map.osm "
        "-o network/map.net.xml "
        "--geometry.remove "
        "--ramps.guess "
        "--junctions.join "
        "--tls.guess-signals "
        "--tls.discard-simple "
        "--tls.join "
        "--no-turnarounds true"
    )

if __name__ == "__main__":
    build()
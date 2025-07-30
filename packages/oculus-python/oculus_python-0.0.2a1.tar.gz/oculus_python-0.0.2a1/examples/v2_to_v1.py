from bps_oculus import io


if __name__ == "__main__":
    # create some fake command line arguments
    argv = ["../data/test.v2.oculus", "--output", "bpsv1"]
    # Pass them into the bps_oculus.io:main method
    io.main(argv)

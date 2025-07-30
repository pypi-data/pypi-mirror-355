from bps_oculus import io


if __name__ == "__main__":
    # create some fake command line arguments
    argv = ["../data/test.v1.oculus", "--output", "bpsv2"]
    # Pass them into the bps_oculus.io:main method
    io.main(argv)

from bps_oculus import io

if __name__ == "__main__":
    # Replace "path/to/your/file/test.oculus" with the actual path to your .oculus file
    input_file = "path/to/your/file/test.oculus"

    # create command line arguments
    argv = [input_file, "--output", "hevc", "--param", "color=True"]

    # Pass them into the bps_oculus.io:main method
    io.main(argv)

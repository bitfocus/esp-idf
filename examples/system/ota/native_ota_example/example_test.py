import re
import os
import sys
import socket
import BaseHTTPServer
import SimpleHTTPServer
from threading import Thread
import ssl

try:
    import IDF
except ImportError:
    # this is a test case write with tiny-test-fw.
    # to run test cases outside tiny-test-fw,
    # we need to set environment variable `TEST_FW_PATH`,
    # then get and insert `TEST_FW_PATH` to sys path before import FW module
    test_fw_path = os.getenv("TEST_FW_PATH")
    if test_fw_path and test_fw_path not in sys.path:
        sys.path.insert(0, test_fw_path)
    import IDF

import DUT
import random

server_cert = "-----BEGIN CERTIFICATE-----\n" \
              "MIIDXTCCAkWgAwIBAgIJAP4LF7E72HakMA0GCSqGSIb3DQEBCwUAMEUxCzAJBgNV\n"\
              "BAYTAkFVMRMwEQYDVQQIDApTb21lLVN0YXRlMSEwHwYDVQQKDBhJbnRlcm5ldCBX\n"\
              "aWRnaXRzIFB0eSBMdGQwHhcNMTkwNjA3MDk1OTE2WhcNMjAwNjA2MDk1OTE2WjBF\n"\
              "MQswCQYDVQQGEwJBVTETMBEGA1UECAwKU29tZS1TdGF0ZTEhMB8GA1UECgwYSW50\n"\
              "ZXJuZXQgV2lkZ2l0cyBQdHkgTHRkMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIB\n"\
              "CgKCAQEAlzfCyv3mIv7TlLkObxunKfCdrJ/zgdANrsx0RBtpEPhV560hWJ0fEin0\n"\
              "nIOMpJSiF9E6QsPdr6Q+eogH4XnOMU9JE+iG743N1dPfGEzJvRlyct/Ck8SswKPC\n"\
              "9+VXsnOdZmUw9y/xtANbURA/TspvPzz3Avv382ffffrJGh7ooOmaZSCZFlSYHLZA\n"\
              "w/XlRr0sSRbLpFGY0gXjaAV8iHHiPDYLy4kZOepjV9U51xi+IGsL4w75zuMgsHyF\n"\
              "3nJeGYHgtGVBrkL0ZKG5udY0wcBjysjubDJC4iSlNiq2HD3fhs7j6CZddV2v845M\n"\
              "lVKNxP0kO4Uj4D8r+5USWC8JKfAwxQIDAQABo1AwTjAdBgNVHQ4EFgQU6OE7ssfY\n"\
              "IIPTDThiUoofUpsD5NwwHwYDVR0jBBgwFoAU6OE7ssfYIIPTDThiUoofUpsD5Nww\n"\
              "DAYDVR0TBAUwAwEB/zANBgkqhkiG9w0BAQsFAAOCAQEAXIlHS/FJWfmcinUAxyBd\n"\
              "/xd5Lu8ykeru6oaUCci+Vk9lyoMMES7lQ+b/00d5x7AcTawkTil9EWpBTPTOTraA\n"\
              "lzJMQhNKmSLk0iIoTtAJtSZgUSpIIozqK6lenxQQDsHbXKU6h+u9H6KZE8YcjsFl\n"\
              "6vL7sw9BVotw/VxfgjQ5OSGLgoLrdVT0z5C2qOuwOgz1c7jNiJhtMdwN+cOtnJp2\n"\
              "fuBgEYyE3eeuWogvkWoDcIA8r17Ixzkpq2oJsdvZcHZPIZShPKW2SHUsl98KDemu\n"\
              "y0pQyExmQUbwKE4vbFb9XuWCcL9XaOHQytyszt2DeD67AipvoBwVU7/LBOvqnsmy\n"\
              "hA==\n"\
              "-----END CERTIFICATE-----\n"

server_key = "-----BEGIN PRIVATE KEY-----\n"\
             "MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCXN8LK/eYi/tOU\n"\
             "uQ5vG6cp8J2sn/OB0A2uzHREG2kQ+FXnrSFYnR8SKfScg4yklKIX0TpCw92vpD56\n"\
             "iAfhec4xT0kT6Ibvjc3V098YTMm9GXJy38KTxKzAo8L35Veyc51mZTD3L/G0A1tR\n"\
             "ED9Oym8/PPcC+/fzZ999+skaHuig6ZplIJkWVJgctkDD9eVGvSxJFsukUZjSBeNo\n"\
             "BXyIceI8NgvLiRk56mNX1TnXGL4gawvjDvnO4yCwfIXecl4ZgeC0ZUGuQvRkobm5\n"\
             "1jTBwGPKyO5sMkLiJKU2KrYcPd+GzuPoJl11Xa/zjkyVUo3E/SQ7hSPgPyv7lRJY\n"\
             "Lwkp8DDFAgMBAAECggEAfBhAfQE7mUByNbxgAgI5fot9eaqR1Nf+QpJ6X2H3KPwC\n"\
             "02sa0HOwieFwYfj6tB1doBoNq7i89mTc+QUlIn4pHgIowHO0OGawomeKz5BEhjCZ\n"\
             "4XeLYGSoODary2+kNkf2xY8JTfFEcyvGBpJEwc4S2VyYgRRx+IgnumTSH+N5mIKZ\n"\
             "SXWNdZIuHEmkwod+rPRXs6/r+PH0eVW6WfpINEbr4zVAGXJx2zXQwd2cuV1GTJWh\n"\
             "cPVOXLu+XJ9im9B370cYN6GqUnR3fui13urYbnWnEf3syvoH/zuZkyrVChauoFf8\n"\
             "8EGb74/HhXK7Q2s8NRakx2c7OxQifCbcy03liUMmyQKBgQDFAob5B/66N4Q2cq/N\n"\
             "MWPf98kYBYoLaeEOhEJhLQlKk0pIFCTmtpmUbpoEes2kCUbH7RwczpYko8tlKyoB\n"\
             "6Fn6RY4zQQ64KZJI6kQVsjkYpcP/ihnOY6rbds+3yyv+4uPX7Eh9sYZwZMggE19M\n"\
             "CkFHkwAjiwqhiiSlUxe20sWmowKBgQDEfx4lxuFzA1PBPeZKGVBTxYPQf+DSLCre\n"\
             "ZFg3ZmrxbCjRq1O7Lra4FXWD3dmRq7NDk79JofoW50yD8wD7I0B7opdDfXD2idO8\n"\
             "0dBnWUKDr2CAXyoLEINce9kJPbx4kFBQRN9PiGF7VkDQxeQ3kfS8CvcErpTKCOdy\n"\
             "5wOwBTwJdwKBgDiTFTeGeDv5nVoVbS67tDao7XKchJvqd9q3WGiXikeELJyuTDqE\n"\
             "zW22pTwMF+m3UEAxcxVCrhMvhkUzNAkANHaOatuFHzj7lyqhO5QPbh4J3FMR0X9X\n"\
             "V8VWRSg+jA/SECP9koOl6zlzd5Tee0tW1pA7QpryXscs6IEhb3ns5R2JAoGAIkzO\n"\
             "RmnhEOKTzDex611f2D+yMsMfy5BKK2f4vjLymBH5TiBKDXKqEpgsW0huoi8Gq9Uu\n"\
             "nvvXXAgkIyRYF36f0vUe0nkjLuYAQAWgC2pZYgNLJR13iVbol0xHJoXQUHtgiaJ8\n"\
             "GLYFzjHQPqFMpSalQe3oELko39uOC1CoJCHFySECgYBeycUnRBikCO2n8DNhY4Eg\n"\
             "9Y3oxcssRt6ea5BZwgW2eAYi7/XqKkmxoSoOykUt3MJx9+EkkrL17bxFSpkj1tvL\n"\
             "qvxn7egtsKjjgGNAxwXC4MwCvhveyUQQxtQb8AqGrGqo4jEEN0L15cnP38i2x1Uo\n"\
             "muhfskWf4MABV0yTUaKcGg==\n"\
             "-----END PRIVATE KEY-----\n"


def get_my_ip():
    s1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s1.connect(("8.8.8.8", 80))
    my_ip = s1.getsockname()[0]
    s1.close()
    return my_ip


def start_https_server(ota_image_dir, server_ip, server_port):
    # parser = argparse.ArgumentParser()
    # parser.add_argument('-p', '--port', dest='port', type= int,
    #     help= "Server Port", default= 8000)
    # args = parser.parse_args()
    os.chdir(ota_image_dir)

    server_file = os.path.join(ota_image_dir, "server_cert.pem")
    cert_file_handle = open(server_file, "w+")
    cert_file_handle.write(server_cert)
    cert_file_handle.close()

    key_file = os.path.join(ota_image_dir, "server_key.pem")
    key_file_handle = open("server_key.pem", "w+")
    key_file_handle.write(server_key)
    key_file_handle.close()

    httpd = BaseHTTPServer.HTTPServer((server_ip, server_port),
                                      SimpleHTTPServer.SimpleHTTPRequestHandler)

    httpd.socket = ssl.wrap_socket(httpd.socket,
                                   keyfile=key_file,
                                   certfile=server_file, server_side=True)
    httpd.serve_forever()


@IDF.idf_example_test(env_tag="Example_WIFI")
def test_examples_protocol_native_ota_example(env, extra_data):
    """
    This is a positive test case, which downloads complete binary file multiple number of times.
    Number of iterations can be specified in variable iterations.
    steps: |
      1. join AP
      2. Fetch OTA image over HTTPS
      3. Reboot with the new OTA image
    """
    dut1 = env.get_dut("native_ota_example", "examples/system/ota/native_ota_example")
    # No. of times working of application to be validated
    iterations = 3
    # File to be downloaded. This file is generated after compilation
    bin_name = "native_ota.bin"
    # check and log bin size
    binary_file = os.path.join(dut1.app.binary_path, bin_name)
    bin_size = os.path.getsize(binary_file)
    IDF.log_performance("native_ota_bin_size", "{}KB".format(bin_size // 1024))
    IDF.check_performance("native_ota_bin_size", bin_size // 1024)
    # start test
    host_ip = get_my_ip()
    thread1 = Thread(target=start_https_server, args=(dut1.app.binary_path, host_ip, 8005))
    thread1.daemon = True
    thread1.start()
    dut1.start_app()
    for i in range(iterations):
        dut1.expect("Loaded app from partition at offset", timeout=30)
        try:
            ip_address = dut1.expect(re.compile(r" sta ip: ([^,]+),"), timeout=30)
            print("Connected to AP with IP: {}".format(ip_address))
        except DUT.ExpectTimeout:
            raise ValueError('ENV_TEST_FAILURE: Cannot connect to AP')
            thread1.close()
        dut1.expect("Connect to Wifi ! Start to Connect to Server....", timeout=30)

        print("writing to device: {}".format("https://" + host_ip + ":8005/" + bin_name))
        dut1.write("https://" + host_ip + ":8005/" + bin_name)
        dut1.expect("Loaded app from partition at offset", timeout=60)
        dut1.expect("Starting OTA example", timeout=30)
        dut1.reset()


@IDF.idf_example_test(env_tag="Example_WIFI")
def test_examples_protocol_native_ota_example_truncated_bin(env, extra_data):
    """
    Working of OTA if binary file is truncated is validated in this test case.
    Application should return with error message in this case.
    steps: |
      1. join AP
      2. Generate truncated binary file
      3. Fetch OTA image over HTTPS
      4. Check working of code if bin is truncated
    """
    dut1 = env.get_dut("native_ota_example", "examples/system/ota/native_ota_example")
    # Original binary file generated after compilation
    bin_name = "native_ota.bin"
    # Truncated binary file to be generated from original binary file
    truncated_bin_name = "truncated.bin"
    # Size of truncated file to be grnerated. This value can range from 288 bytes (Image header size) to size of original binary file
    # truncated_bin_size is set to 64000 to reduce consumed by the test case
    truncated_bin_size = 64000
    # check and log bin size
    binary_file = os.path.join(dut1.app.binary_path, bin_name)
    f = open(binary_file, "r+")
    fo = open(os.path.join(dut1.app.binary_path, truncated_bin_name), "w+")
    fo.write(f.read(truncated_bin_size))
    fo.close()
    f.close()
    binary_file = os.path.join(dut1.app.binary_path, truncated_bin_name)
    bin_size = os.path.getsize(binary_file)
    IDF.log_performance("native_ota_bin_size", "{}KB".format(bin_size // 1024))
    IDF.check_performance("native_ota_bin_size", bin_size // 1024)
    # start test
    host_ip = get_my_ip()
    thread1 = Thread(target=start_https_server, args=(dut1.app.binary_path, host_ip, 8006))
    thread1.daemon = True
    thread1.start()
    dut1.start_app()
    dut1.expect("Loaded app from partition at offset", timeout=30)
    try:
        ip_address = dut1.expect(re.compile(r" sta ip: ([^,]+),"), timeout=60)
        print("Connected to AP with IP: {}".format(ip_address))
    except DUT.ExpectTimeout:
        raise ValueError('ENV_TEST_FAILURE: Cannot connect to AP')
    dut1.expect("Connect to Wifi ! Start to Connect to Server....", timeout=30)

    print("writing to device: {}".format("https://" + host_ip + ":8006/" + truncated_bin_name))
    dut1.write("https://" + host_ip + ":8006/" + truncated_bin_name)
    dut1.expect("native_ota_example: Image validation failed, image is corrupted", timeout=20)


@IDF.idf_example_test(env_tag="Example_WIFI")
def test_examples_protocol_native_ota_example_truncated_header(env, extra_data):
    """
    Working of OTA if headers of binary file are truncated is vaildated in this test case.
    Application should return with error message in this case.
    steps: |
      1. join AP
      2. Generate binary file with truncated headers
      3. Fetch OTA image over HTTPS
      4. Check working of code if headers are not sent completely
    """
    dut1 = env.get_dut("native_ota_example", "examples/system/ota/native_ota_example")
    # Original binary file generated after compilation
    bin_name = "native_ota.bin"
    # Truncated binary file to be generated from original binary file
    truncated_bin_name = "truncated_header.bin"
    # Size of truncated file to be grnerated. This value should be less than 288 bytes (Image header size)
    truncated_bin_size = 180
    # check and log bin size
    binary_file = os.path.join(dut1.app.binary_path, bin_name)
    f = open(binary_file, "r+")
    fo = open(os.path.join(dut1.app.binary_path, truncated_bin_name), "w+")
    fo.write(f.read(truncated_bin_size))
    fo.close()
    f.close()
    binary_file = os.path.join(dut1.app.binary_path, truncated_bin_name)
    bin_size = os.path.getsize(binary_file)
    IDF.log_performance("native_ota_bin_size", "{}KB".format(bin_size // 1024))
    IDF.check_performance("native_ota_bin_size", bin_size // 1024)
    # start test
    host_ip = get_my_ip()
    thread1 = Thread(target=start_https_server, args=(dut1.app.binary_path, host_ip, 8007))
    thread1.daemon = True
    thread1.start()
    dut1.start_app()
    dut1.expect("Loaded app from partition at offset", timeout=30)
    try:
        ip_address = dut1.expect(re.compile(r" sta ip: ([^,]+),"), timeout=60)
        print("Connected to AP with IP: {}".format(ip_address))
    except DUT.ExpectTimeout:
        raise ValueError('ENV_TEST_FAILURE: Cannot connect to AP')
    dut1.expect("Connect to Wifi ! Start to Connect to Server....", timeout=30)

    print("writing to device: {}".format("https://" + host_ip + ":8007/" + truncated_bin_name))
    dut1.write("https://" + host_ip + ":8007/" + truncated_bin_name)
    dut1.expect("native_ota_example: received package is not fit len", timeout=20)


@IDF.idf_example_test(env_tag="Example_WIFI")
def test_examples_protocol_native_ota_example_random(env, extra_data):
    """
    Working of OTA if random data is added in binary file are validated in this test case.
    Magic byte verification should fail in this case.
    steps: |
      1. join AP
      2. Generate random binary image
      3. Fetch OTA image over HTTPS
      4. Check working of code for random binary file
    """
    dut1 = env.get_dut("native_ota_example", "examples/system/ota/native_ota_example")
    # Random binary file to be generated
    random_bin_name = "random.bin"
    # Size of random binary file. 32000 is choosen, to reduce the time required to run the test-case
    random_bin_size = 32000
    # check and log bin size
    binary_file = os.path.join(dut1.app.binary_path, random_bin_name)
    fo = open(binary_file, "w+")
    for i in range(random_bin_size):
        fo.write(str(random.randrange(0,255,1)))
    fo.close()
    bin_size = os.path.getsize(binary_file)
    IDF.log_performance("native_ota_bin_size", "{}KB".format(bin_size // 1024))
    IDF.check_performance("native_ota_bin_size", bin_size // 1024)
    # start test
    host_ip = get_my_ip()
    thread1 = Thread(target=start_https_server, args=(dut1.app.binary_path, host_ip, 8008))
    thread1.daemon = True
    thread1.start()
    dut1.start_app()
    dut1.expect("Loaded app from partition at offset", timeout=30)
    try:
        ip_address = dut1.expect(re.compile(r" sta ip: ([^,]+),"), timeout=60)
        print("Connected to AP with IP: {}".format(ip_address))
    except DUT.ExpectTimeout:
        raise ValueError('ENV_TEST_FAILURE: Cannot connect to AP')
    dut1.expect("Connect to Wifi ! Start to Connect to Server....", timeout=30)

    print("writing to device: {}".format("https://" + host_ip + ":8008/" + random_bin_name))
    dut1.write("https://" + host_ip + ":8008/" + random_bin_name)
    dut1.expect("esp_ota_ops: OTA image has invalid magic byte", timeout=20)


if __name__ == '__main__':
    test_examples_protocol_native_ota_example()
    test_examples_protocol_native_ota_example_truncated_bin()
    test_examples_protocol_native_ota_example_truncated_header()
    test_examples_protocol_native_ota_example_random()

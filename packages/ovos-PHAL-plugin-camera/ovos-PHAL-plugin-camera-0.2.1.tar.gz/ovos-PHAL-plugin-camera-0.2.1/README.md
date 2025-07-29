# Camera Plugin for OVOS PHAL

This plugin allows users to interact with cameras using OpenCV or libcamera, take snapshots, and serve video streams over HTTP. It also provides methods for handling camera operations via message bus events.

## Features

- Detect and use compatible camera systems (libcamera on Raspberry Pi or OpenCV on other systems).
- Open and close the camera dynamically.
- Capture frames and save them to a file or return them as base64-encoded strings.
- Serve video streams as an MJPEG feed over HTTP.

---

## HiveMind Support

This plugin can be used both in OVOS and with [HiveMind](https://github.com/JarbasHiveMind) satellites.

Be sure to allow `"ovos.phal.camera.pong"` in your hivemind for your satellite to be able to report camera support

```bash
hivemind-core allow-msg "ovos.phal.camera.pong"
```

---

## Installation

1. Install required dependencies:

   ```bash
   pip install ovos-phal-plugin-camera
   ```

2. Add the plugin to your OVOS PHAL configuration:

   ```json
   {
       "PHAL": {
           "ovos-phal-plugin-camera": {
               "video_source": 0,
               "start_open": false,
               "serve_mjpeg": false,
               "mjpeg_host": "0.0.0.0",
               "mjpeg_port": 5000
           }
       }
   }
   ```

### Additional Steps for Raspberry Pi Users

If you plan to use this skill on a Raspberry Pi, it requires access to the `libcamera` package for the Picamera2 library to function correctly. Due to how `libcamera` is installed on the Raspberry Pi (system-wide), additional steps are necessary to ensure compatibility when using a Python virtual environment (venv).

In these examples we use the default .venv location from ovos-installer, `~/.venvs/ovos`, adjust as needed

#### **Steps to Enable `libcamera` in Your Virtual Environment**

1. **Install Required System Packages**  
   Before proceeding, ensure that `libcamera` and its dependencies are installed on your Raspberry Pi. Run the following commands:  
   ```bash
   sudo apt install -y python3-libcamera python3-kms++ libcap-dev
   ```

2. **Modify the Virtual Environment Configuration**  
   If you already have a virtual environment set up, enable access to system-wide packages by modifying the `pyvenv.cfg` file in the virtual environment directory:  
   ```bash
   nano ~/.venvs/ovos/pyvenv.cfg
   ```

   Add or update the following line:  
   ```plaintext
   include-system-site-packages = true
   ```

   Save the file and exit.

3. **Verify Access to `libcamera`**  
   Activate your virtual environment:  
   ```bash
   source ~/.venvs/ovos/bin/activate
   ```

   Check if the `libcamera` package is accessible:  
   ```bash
   python3 -c "import libcamera; print('libcamera is accessible')"
   ```

#### **Why Are These Steps Necessary?**
The `libcamera` package is not available on PyPI and is installed system-wide on the Raspberry Pi. Virtual environments typically isolate themselves from system-wide Python packages, so these adjustments allow the skill to access `libcamera` while still benefiting from the isolation provided by a venv.

#### **Notes**
- These steps are specific to Raspberry Pi users who want to utilize the Picamera2 library for camera functionality. On other platforms, the skill defaults to using OpenCV, which does not require additional configuration.
- Ensure that `libcamera` is installed on your Raspberry Pi before attempting these steps. You can test this by running:  
  ```bash
  libcamera-still --version
  ```
  
---

## Configuration Options

| Option         | Type   | Default   | Description                                           |
| -------------- | ------ | --------- | ----------------------------------------------------- |
| `video_source` | `int`  | `0`       | Index of the video source to use for the camera.      |
| `start_open`   | `bool` | `false`   | Whether to open the camera at plugin startup.         |
| `serve_mjpeg`  | `bool` | `false`   | Whether to start an MJPEG server for video streaming. |
| `mjpeg_port`   | `int`  | `5000`    | Port for the MJPEG server.                            |

---

## Bus Events

### Handled Events

| Event Name               | Description                       | Payload                     |
| ------------------------ | --------------------------------- | --------------------------- |
| `ovos.phal.camera.open`  | Opens the camera.                 | None                        |
| `ovos.phal.camera.close` | Closes the camera.                | None                        |
| `ovos.phal.camera.get`   | Captures a frame from the camera. | `{ "path": "<file_path>" }` |

### Emitted Events

| Event Name                      | Description                      | Payload                                                           |
| ------------------------------- | -------------------------------- | ----------------------------------------------------------------- |
| `ovos.phal.camera.get.response` | Response for the captured frame. | `{ "path": "<file_path>" }` or `{ "b64_frame": "<base64_data>" }` |

---

## Usage

### Open the Camera

Send the following message to open the camera:

```python
bus.emit(Message("ovos.phal.camera.open"))
```

### Close the Camera

Send the following message to close the camera:

```python
bus.emit(Message("ovos.phal.camera.close"))
```

### Capture a Frame

Send the following message to capture a frame:

```python
bus.emit(Message("ovos.phal.camera.get", {"path": "/path/to/save/image.jpg"}))
```

If the `path` is not provided, the frame will be returned as a base64-encoded string.

### MJPEG Server

If the `serve_mjpeg` option is enabled in the configuration, the MJPEG feed will be accessible at:

```
http://<mjpeg_host>:<mjpeg_port>/video_feed
```

You can use the MJPEG feed to integrate this camera [into Home Assistant](https://www.home-assistant.io/integrations/mjpeg/)


---

## License

This project is licensed under the [Apache 2.0 License](LICENSE).

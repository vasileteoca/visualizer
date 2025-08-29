import sounddevice as sd
import threading
import numpy as np
from collections import defaultdict

audio_levels = defaultdict(float)
audio_locks = defaultdict(threading.Lock)
selected_sources = set()
_monitor_threads = {}

def enumerate_devices():
    """
    Enumerate all devices (input and output) that can produce audio.
    Returns list of dicts: {id, name, channels, default_samplerate, is_output, hostapi_name}
    """
    devices = []
    hostapis = sd.query_hostapis()
    for idx, dev in enumerate(sd.query_devices()):
        # Skip devices with no input or output channels
        if dev['max_input_channels'] == 0 and dev['max_output_channels'] == 0:
            continue

        hostapi_name = hostapis[dev['hostapi']]['name']
        devices.append({
            "id": idx,
            "name": dev['name'],
            "channels": max(dev['max_input_channels'], dev['max_output_channels']),
            "default_samplerate": dev['default_samplerate'],
            "is_output": dev['max_output_channels'] > 0,
            "hostapi_name": hostapi_name
        })
    return devices

def get_default_output_device():
    """Return default output device (loopback if Windows WASAPI)"""
    try:
        default_out_idx = sd.default.device[1]  # output
        dev = sd.query_devices(default_out_idx)
        hostapi_name = sd.query_hostapis()[dev['hostapi']]['name']
        return {
            "id": default_out_idx,
            "name": dev['name'],
            "channels": dev['max_output_channels'],
            "default_samplerate": dev['default_samplerate'],
            "is_output": True,
            "hostapi_name": hostapi_name
        }
    except Exception:
        return None

def start_monitor_thread(device_info):
    """
    Start a thread that continuously reads audio from the device.
    Works for input devices and output devices (loopback on WASAPI Windows).
    """
    device_id = device_info['id']
    if device_id in _monitor_threads:
        return  # Already running

    def monitor():
        try:
            extra = None
            if sd._platform == 'windows' and device_info['is_output'] and 'WASAPI' in device_info['hostapi_name']:
                extra = sd.WasapiSettings(loopback=True)

            channels = min(2, device_info['channels'])  # safe for stereo
            with sd.InputStream(
                device=device_id,
                channels=channels,
                samplerate=int(device_info['default_samplerate']),
                dtype='float32',
                latency='low',
                extra_settings=extra
            ) as stream:
                while device_id in selected_sources:
                    available = stream.read_available
                    if available < 1:
                        continue
                    data, _ = stream.read(min(1024, available))
                    if data.size == 0:
                        continue
                    amplitude = float(np.linalg.norm(data) / np.sqrt(data.size))
                    lock = audio_locks[device_id]
                    with lock:
                        audio_levels[device_id] = amplitude
        except Exception as e:
            print(f"[Monitor] Failed device {device_info['name']} ({device_id}): {e}")
            with audio_locks[device_id]:
                audio_levels[device_id] = 0.0

    thread = threading.Thread(target=monitor, daemon=True)
    thread.start()
    _monitor_threads[device_id] = thread

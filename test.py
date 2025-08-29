import sounddevice as sd

for idx, dev in enumerate(sd.query_devices()):
    print(idx, dev['name'], dev['max_input_channels'], dev['max_output_channels'], dev['hostapi'])

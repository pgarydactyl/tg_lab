import datetime
import json
import threading
from pathlib import Path

import imagingcontrol4 as ic4
import numpy as np

from tg_lab.ion_event_counting.fastvimprocess import event_counting


@ic4.Library.init_context(
    api_log_level=ic4.LogLevel.INFO, log_targets=ic4.LogTarget.STDERR
)
def process_on_trigger(
    output_dir,
    max_images,
    threshold,
    mode,
    nxnarea,
    multiply_factor,
    int_offset,
    event_size=1,
    keyboard_control=False,
):
    # Let the user select one of the connected cameras
    device_list = ic4.DeviceEnum.devices()
    for i, dev in enumerate(device_list):
        print(f"[{i}] {dev.model_name} ({dev.serial}) [{dev.interface.display_name}]")
    print(f"Select device [0..{len(device_list) - 1}]: ", end="")
    selected_index = int(input())
    dev_info = device_list[selected_index]

    # Open the selected device in a new Grabber
    grabber = ic4.Grabber(dev_info)
    map = grabber.device_property_map

    # Reset all device settings to default
    # Not all devices support this, so ignore possible errors
    map.try_set_value(ic4.PropId.USER_SET_SELECTOR, "Default")
    map.try_set_value(ic4.PropId.USER_SET_LOAD, 1)

    # Select FrameStart trigger (for cameras that support this)
    map.try_set_value(ic4.PropId.TRIGGER_SELECTOR, "FrameStart")

    # Enable trigger mode
    map.set_value(ic4.PropId.TRIGGER_MODE, "On")

    event = threading.Event()

    # Define a listener class to receive queue sink notifications
    class Listener(ic4.QueueSinkListener):
        def __init__(self):
            self._start_time = datetime.datetime.now()
            self.image_counter = 0
            self.event_counter = 0
            self.sum_arr = np.zeros(
                (
                    grabber.device_property_map.get_value_int(ic4.PropId.HEIGHT),
                    grabber.device_property_map.get_value_int(ic4.PropId.WIDTH),
                )
            )

        def sink_connected(
            self,
            sink: ic4.QueueSink,
            image_type: ic4.ImageType,
            min_buffers_required: int,
        ) -> bool:
            # No need to configure anything, just accept the connection
            return True

        def frames_queued(self, sink: ic4.QueueSink):
            # Get the queued image buffer
            buffer = sink.pop_output_buffer()

            # image array can come out as multi dimensional, take a grayscale mean
            arr = buffer.numpy_wrap().mean(axis=2)

            event_count, num_events = event_counting(
                arr, threshold, mode, nxnarea, multiply_factor, int_offset, event_size
            )

            self.sum_arr += event_count

            self.event_counter += num_events
            self.image_counter += 1
            if self.image_counter == max_images:
                event.set()

        def write_out(self, output_dir: str):
            output_dir = Path(output_dir)
            end_time = datetime.datetime.now()
            metadata = {
                "image_count": self.image_counter,
                "event_count": self.event_counter,
                "image_shape": self.sum_arr.shape,
                "start_time": self._start_time.strftime("%Y/%m/%d, %H:%M:%S"),
                "end_time": end_time.strftime("%Y/%m/%d, %H:%M:%S"),
                "elapsed_time (s)": (end_time - self._start_time).total_seconds(),
            }
            np.savetxt(output_dir / "event_count.csv", self.sum_arr)
            with open(output_dir / "metadata.json", "w") as f:
                json.dump(metadata, f, indent=4)

    # Create an instance of the listener type defined above
    listener = Listener()

    # Create a QueueSink to capture all images arriving from the video capture device
    sink = ic4.QueueSink(listener)

    # Start the video stream into the sink
    grabber.stream_setup(sink)
    msg = "Input hardware triggers"
    if keyboard_control:
        msg += ", or press ENTER to issue a software trigger"
        msg += "\nPress q + ENTER to quit"

    print("Stream started.")
    print("Waiting for triggers")
    print()
    print(msg)

    # define asynchronous thread worker that waits for an event to be set to end and write out results
    def worker():
        event.wait()
        grabber.stream_stop()
        listener.write_out(output_dir=output_dir)
        grabber.device_close()

    thread = threading.Thread(target=worker)
    thread.start()

    if keyboard_control:
        while input() != "q":
            map.execute_command(ic4.PropId.TRIGGER_SOFTWARE)
        event.set()

    thread.join()

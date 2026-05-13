from deep_sort_realtime.deepsort_tracker import DeepSort

tracker = DeepSort(
    max_age=30,
    n_init=2
)

def update_tracks(detections, frame):

    ds_detections = []

    for det in detections:

        x1,y1,x2,y2 = det["bbox"]

        w = x2 - x1
        h = y2 - y1

        ds_detections.append(
            ([x1,y1,w,h], det["conf"], det["class"])
        )

    tracks = tracker.update_tracks(
        ds_detections,
        frame=frame
    )

    return tracks
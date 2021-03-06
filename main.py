import cv2
import time
import numpy as np
import os
import json
import base64

# Preload models for performance
print("[INFO] loading YOLO...")
net = cv2.dnn.readNetFromDarknet("./yolo_configs/yolov3-obj.cfg", "./yolo_configs/posture_yolov3.weights")

print("[INFO] loading labels...")
with open("./yolo_configs/posture.names", 'rt') as f:
    NAMES = f.read().rstrip('\n').split('\n')

# Assign colors for drawing bounding boxes
COLORS = [
    [0, 200, 0], [20, 45, 144],
    [157, 224, 173], [0, 0, 232],
    [26, 147, 111], [64, 100, 44]
]


def rescale_image(input_img: np.ndarray) -> np.ndarray:
    (h, w) = input_img.shape[:2]
    return input_img if h < 1000 else cv2.resize(input_img, (int(w / (int(str(h)[0]) + 1)), int(h / (int(str(h)[0]) + 1))))


def predict_yolo(input_img: np.ndarray) -> list:
    ln = net.getLayerNames()
    ln = [ln[i[0] - 1] for i in net.getUnconnectedOutLayers()]
    blob = cv2.dnn.blobFromImage(input_img, 1 / 255.0, (256, 256), swapRB=True, crop=False)
    net.setInput(blob)
    start = time.time()
    layer_outputs = net.forward(ln)
    end = time.time()
    print("[INFO] YOLO took {:.6f} seconds".format(end - start))
    return layer_outputs


def draw_bound(input_img: np.ndarray, layer_outputs: list, confidence_level: float, threshold: float) -> [np.ndarray, list]:
    boxes = []
    confidences = []
    class_id = []
    (H, W) = input_img.shape[:2]

    for output in layer_outputs:
        for detection in output:
            scores = detection[5:]
            class_ids = np.argmax(scores)
            confidence = scores[class_ids]

            if confidence > confidence_level:
                box = detection[0:4] * np.array([W, H, W, H])
                (centerX, centerY, width, height) = box.astype("int")

                # use the center (x, y)-coordinates to derive the top and
                x = int(centerX - (width / 2))
                y = int(centerY - (height / 2))

                boxes.append([x, y, int(width), int(height)])
                confidences.append(float(confidence))
                class_id.append(class_ids)

    # Non maxima
    idxs = cv2.dnn.NMSBoxes(boxes, confidences, confidence_level, threshold)
    results = []

    if len(idxs) > 0:
        for i in idxs.flatten():
            # extract the bounding box coordinates
            (x, y) = (boxes[i][0], boxes[i][1])
            (w, h) = (boxes[i][2], boxes[i][3])
            # draw a bounding box rectangle and label on the image
            color = [int(c) for c in COLORS[class_id[i]]]
            cv2.rectangle(input_img, (x, y), (x + w, y + h), color, 2)
            text = "{}: {:.4f}".format(NAMES[class_id[i]], confidences[i])
            cv2.putText(input_img, text, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            results.append([NAMES[class_id[i]], confidences[i]])

    return [input_img, results]


def predict(filename) -> [{}]:
    image = cv2.imdecode(np.fromstring(filename.read(),np.uint8), cv2.IMREAD_COLOR)
    image = rescale_image(image)

    layer_outputs = predict_yolo(image)
    results = draw_bound(image, layer_outputs, 0.5, 0.4)

    ret, buffer = cv2.imencode('.png', results[0])
    encoded_im = base64.b64encode(buffer).decode()
    mime = "image/jpeg"
    #output = os.path.join("input/"+ filename+"")
    #cv2.imwrite(output, results[0])
    return [{
        "prediction": results[1],
        "uri": "data:%s;base64,%s" %(mime, encoded_im)
    }]


if __name__ == "__main__":
    for f in os.listdir("./input"):
        image = cv2.imread("./input/" + f)
        image = rescale_image(image)

        layer_outputs = predict_yolo(image)
        results = draw_bound(image, layer_outputs, 0.5, 0.4)

        print(f, results[1])

        # show the output image
        cv2.imshow(f, results[0])
        print("")

    cv2.waitKey(0)
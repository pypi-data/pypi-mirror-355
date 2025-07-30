import cv2
import numpy as np
import imageio
from tqdm import tqdm
from .imageutils import resize_fix, cvt_color

__all__ = ["VideoCaptureWrapper", "generate_mp4", "images_to_video", "merge_video", "perframe_process"]


class VideoCaptureWrapper():
    def __init__(self, video_path):
        self.capture = cv2.VideoCapture(video_path)
        self.frame_count = int(self.capture.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.capture.get(cv2.CAP_PROP_FPS)
        self.height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        print(f"Open video {video_path.split('/')[-1]}...")
        print(f"frame count: {self.frame_count}")
        print(f"fps: {self.fps}")
        print(f"height, width: {self.height}, {self.width}")

    def get_frame(self, frame_id):
        self.capture.set(cv2.CAP_PROP_POS_FRAMES, int(frame_id))
        ret, frame = self.capture.read()
        return frame

    def __len__(self):
        return self.frame_count

    def __del__(self):
        self.capture.release()


def images_to_video(image_paths, output_path, size, fps=30, pad_start_end=None, latent_frame=False):
    height, width = size
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    if pad_start_end:
        pad_img = np.zeros((height, width, 3), dtype=np.uint8)
        [out.write(pad_img) for i in range(pad_start_end)]
    for path in tqdm(image_paths):
        img = cv2.imread(path)
        # Resize the image if necessary
        img = resize_fix(img, height, width)
        if latent_frame:
            [out.write(img) for i in range(fps)]
        else:
            out.write(img)
    if pad_start_end:
        [out.write(img) for i in range(pad_start_end)]
    out.release()

def generate_mp4(out_path, images, bgr=True, **kwargs):
    writer = imageio.get_writer(out_path, **kwargs)
    for image in images:
        image = cvt_color(image) if bgr else image
        writer.append_data(image)
    writer.close()

def perframe_process(in_video, out_video, process_fn, out_fps=0):
    capture = cv2.VideoCapture(in_video)
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = int(capture.get(cv2.CAP_PROP_FPS))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))

    out_fps = fps if out_fps == 0 else out_fps
    _, frame = capture.read()
    frame = process_fn(frame)
    out_height = frame.shape[0]
    out_width = frame.shape[1]
    writer = cv2.VideoWriter(out_video, cv2.VideoWriter_fourcc('M','P','4','V'), out_fps, (out_width, out_height))
    writer.write(frame)

    for frame_id in range(1, frame_count):
        ret, frame = capture.read()
        if ret:
            frame = process_fn(frame)
            writer.write(frame)

    capture.release()
    writer.release()


def merge_video(input_videos, start_positions, end_positions):
    '''Merge few videos into one video

    Notice:
        1. all video should in same width and height
    
    Example:
        input_videos = glob.glob('*.mp4')
        start_positions = np.array([235, 56, 372, 235])
        end_positions = np.array([235+209, 56+209, 372+115, 235+209])
        merge_video(input_videos, start_positions, end_positions)
    '''
    captures = []
    captures += [cv2.VideoCapture(video_file) for video_file in input_videos]

    fps = []
    height = []
    width = []
    frame_count = []

    for cap in captures:
        fps += [int(cap.get(cv2.CAP_PROP_FPS)+0.5)]
        height += [int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))]
        width += [int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))]
        frame_count += [int(cap.get(cv2.CAP_PROP_FRAME_COUNT))]

    print(fps)
    print(height)
    print(width)
    print(frame_count)

    diff_positions = end_positions - start_positions
    num_frames = np.max(diff_positions)
    diff_rate = diff_positions / num_frames

    fourcc = cv2.VideoWriter_fourcc('D', 'I', 'V', 'X')
    videoWriter = cv2.VideoWriter('merge_video.avi', fourcc, fps[0], (np.sum(width), np.max(height)))

    for i in range(len(captures)):
        captures[i].set(cv2.CAP_PROP_POS_FRAMES, int(start_positions[i]))

    for frame_n in range(num_frames):
        merge_frame = []
        for i in range(len(captures)): 
            if diff_rate[i] != 1.0:
                captures[i].set(cv2.CAP_PROP_POS_FRAMES, int(start_positions[i] + diff_rate[i] * frame_n))
                ret, frame = captures[i].read()
            else:
                ret, frame = captures[i].read()
            merge_frame += [frame]
        merge_frame = np.concatenate(merge_frame, axis=1)
        videoWriter.write(merge_frame)

    videoWriter.release()

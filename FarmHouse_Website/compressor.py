import io
import tempfile

import ffmpeg
from PIL import Image
from FarmHouse_Website_Backend import settings


def compressImageWithBestQuality(image_bytes, max_quality=95, min_quality=10):

    print("input size : ", len(image_bytes))

    low = min_quality
    high = max_quality
    best_output = None

    while low <= high :

        mid = (low + high)/2

        input_image = Image.open(io.BytesIO(image_bytes))
        output_image = io.BytesIO()
        input_image.save(output_image, format='JPEG', quality=int(mid), optimize=True)

        if output_image.tell() <= settings.MAX_UPLOAD_SIZE() :
            best_output = output_image.getvalue()
            low = mid + 1
        else :
            high = mid - 1

    return best_output

import tempfile
import ffmpeg

def compressVideo(video_file):
    with tempfile.NamedTemporaryFile(mode='w+b', suffix='.mp4', delete=False) as temp_input, \
         tempfile.NamedTemporaryFile(mode='w+b', suffix='.mp4', delete=False) as temp_output:

        temp_input.write(video_file)
        temp_input.flush()

        (
            ffmpeg
            .input(temp_input.name)
            .output(
                temp_output.name,
                vf='scale=854:480',
                vcodec='libx264',
                video_bitrate='1.2M'
            )
            .run(overwrite_output=True, quiet=True, cmd=settings.PATH_TO_FFMPEG())
        )

        temp_output.seek(0)
        compressed_data = temp_output.read()

    return compressed_data


import io
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

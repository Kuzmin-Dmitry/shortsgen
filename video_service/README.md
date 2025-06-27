# Video Service

Микросервис для генерации видео из аудио и изображений.

## Текущий статус

**🟢 РАБОТАЕТ** - Сервис настроен и функционирует в режиме тестирования

### Режимы работы

1. **Простой режим (текущий)** - SimpleVideoService
   - Создает мок-видео для тестирования
   - Не требует MoviePy 
   - Генерирует метаданные видео
   - Подходит для интеграционного тестирования

2. **Полный режим** - VideoService с MoviePy
   - Реальная генерация видео
   - Требует установки MoviePy
   - Полная поддержка эффектов (Ken Burns и др.)

## Возможности

- Генерация видео из аудио файла и последовательности изображений
- Поддержка эффекта Ken Burns (плавное увеличение изображений)
- Настраиваемые переходы между слайдами
- Автоматическая синхронизация длительности видео с аудио
- Интеграция с Redis для обработки задач
- Поддержка различных разрешений и FPS

## API Endpoints

### GET /health
Проверка состояния сервиса.

### POST /generateVideo
Генерация видео из аудио и изображений.

**Параметры:**
- `audio_path`: Путь к аудио файлу
- `image_paths`: Список путей к изображениям
- `fps`: Частота кадров (по умолчанию: 24)
- `resolution`: Разрешение видео (по умолчанию: [1920, 1080])
- `slide_duration`: Длительность каждого слайда в секундах (по умолчанию: 3.0)
- `transition_duration`: Длительность перехода между слайдами (по умолчанию: 0.5)
- `enable_ken_burns`: Включить эффект Ken Burns (по умолчанию: true)
- `zoom_factor`: Коэффициент увеличения для эффекта Ken Burns (по умолчанию: 1.1)

## Redis Tasks

Сервис обрабатывает задачи из очереди `queue:video-service`:

### CreateVideo / GenerateVideo / CreateVideoFromSlides
Генерирует видео из аудио и изображений.

**Зависимости:**
- `voice_track_id`: ID задачи генерации аудио
- `slide_ids`: Список ID задач генерации изображений

**Параметры:**
- Все параметры аналогичны API endpoint

## Конфигурация

Переменные окружения:
- `REDIS_HOST`: Хост Redis (по умолчанию: "redis")
- `REDIS_PORT`: Порт Redis (по умолчанию: 6379)
- `OUTPUT_DIR`: Директория для выходных файлов (по умолчанию: "/app/output")

## Зависимости

**Базовые (всегда требуются):**
- FastAPI
- Redis
- Pillow
- NumPy

**Дополнительные (для полного режима):**
- MoviePy (закомментирован в requirements.txt для тестирования)

## Тестирование

Используйте PowerShell скрипт для тестирования:

```powershell
pwsh -File test_video_service.ps1
```

## Запуск

### В Docker (рекомендуется)
```bash
docker-compose up video-service
```

### Локально
```bash
uvicorn app:app --host 0.0.0.0 --port 8004
```

## Переключение на полный режим

Для включения полной функциональности с MoviePy:

1. Раскомментируйте `moviepy==2.2.1` в `requirements.txt`
2. Обновите импорт в `routes.py`:
   ```python
   from video_service import VideoService
   video_service = VideoService()
   ```
3. Пересоберите Docker контейнер

## Docker

```bash
docker build -t video-service .
docker run -p 8004:8004 video-service
```





## MoviePy

moviepy.video.compositing.CompositeVideoClip.concatenate_videoclips
moviepy.video.compositing.CompositeVideoClip.concatenate_videoclips(clips, method='chain', transition=None, bg_color=None, is_mask=False, padding=0)[source]
Concatenates several video clips.

Returns a video clip made by clip by concatenating several video clips. (Concatenated means that they will be played one after another).

There are two methods:

method=”chain”: will produce a clip that simply outputs the frames of the successive clips, without any correction if they are not of the same size of anything. If none of the clips have masks the resulting clip has no mask, else the mask is a concatenation of masks (using completely opaque for clips that don’t have masks, obviously). If you have clips of different size and you want to write directly the result of the concatenation to a file, use the method “compose” instead.

method=”compose”, if the clips do not have the same resolution, the final resolution will be such that no clip has to be resized. As a consequence the final clip has the height of the highest clip and the width of the widest clip of the list. All the clips with smaller dimensions will appear centered. The border will be transparent if mask=True, else it will be of the color specified by bg_color.

The clip with the highest FPS will be the FPS of the result clip.

Parameters
:
clips – A list of video clips which must all have their duration attributes set.

method – “chain” or “compose”: see above.

transition – A clip that will be played between each two clips of the list.

bg_color – Only for method=’compose’. Color of the background. Set to None for a transparent clip

padding – Only for method=’compose’. Duration during two consecutive clips. Note that for negative padding, a clip will partly play at the same time as the clip it follows (negative padding is cool for clips who fade in on one another). A non-null padding automatically sets the method to compose.




---------------------------------------------------------------






moviepy.audio.AudioClip.AudioClip
class moviepy.audio.AudioClip.AudioClip(frame_function=None, duration=None, fps=None)[source]
Base class for audio clips.

See AudioFileClip and CompositeAudioClip for usable classes.

An AudioClip is a Clip with a frame_function attribute of the form `` t -> [ f_t ]`` for mono sound and t-> [ f1_t, f2_t ] for stereo sound (the arrays are Numpy arrays). The f_t are floats between -1 and 1. These bounds can be trespassed without problems (the program will put the sound back into the bounds at conversion time, without much impact).

Parameters
:
frame_function – A function t-> frame at time t. The frame does not mean much for a sound, it is just a float. What ‘makes’ the sound are the variations of that float in the time.

duration – Duration of the clip (in seconds). Some clips are infinite, in this case their duration will be None.

nchannels – Number of channels (one or two for mono or stereo).

Examples

# Plays the note A in mono (a sine wave of frequency 440 Hz)
import numpy as np
frame_function = lambda t: np.sin(440 * 2 * np.pi * t)
clip = AudioClip(frame_function, duration=5, fps=44100)
clip.preview()

# Plays the note A in stereo (two sine waves of frequencies 440 and 880 Hz)
frame_function = lambda t: np.array([
    np.sin(440 * 2 * np.pi * t),
    np.sin(880 * 2 * np.pi * t)
]).T.copy(order="C")
clip = AudioClip(frame_function, duration=3, fps=44100)
clip.preview()
audiopreview(fps=None, buffersize=2000, nbytes=2, audio_flag=None, video_flag=None)[source]
Preview an AudioClip using ffplay

Parameters
:
fps – Frame rate of the sound. 44100 gives top quality, but may cause problems if your computer is not fast enough and your clip is complicated. If the sound jumps during the preview, lower it (11025 is still fine, 5000 is tolerable).

buffersize – The sound is not generated all at once, but rather made by bunches of frames (chunks). buffersize is the size of such a chunk. Try varying it if you meet audio problems (but you shouldn’t have to).

nbytes – Number of bytes to encode the sound: 1 for 8bit sound, 2 for 16bit, 4 for 32bit sound. 2 bytes is fine.

audio_flag – Instances of class threading events that are used to synchronize video and audio during VideoClip.preview().

video_flag – Instances of class threading events that are used to synchronize video and audio during VideoClip.preview().

display_in_notebook(filetype=None, maxduration=60, t=None, fps=None, rd_kwargs=None, center=True, **html_kwargs)
Displays clip content in an Jupyter Notebook.

Remarks: If your browser doesn’t support HTML5, this should warn you. If nothing is displayed, maybe your file or filename is wrong. Important: The media will be physically embedded in the notebook.

Parameters
:
clip (moviepy.Clip.Clip) – Either the name of a file, or a clip to preview. The clip will actually be written to a file and embedded as if a filename was provided.

filetype (str, optional) – One of "video", "image" or "audio". If None is given, it is determined based on the extension of filename, but this can bug.

maxduration (float, optional) – An error will be raised if the clip’s duration is more than the indicated value (in seconds), to avoid spoiling the browser’s cache and the RAM.

t (float, optional) – If not None, only the frame at time t will be displayed in the notebook, instead of a video of the clip.

fps (int, optional) – Enables to specify an fps, as required for clips whose fps is unknown.

rd_kwargs (dict, optional) – Keyword arguments for the rendering, like dict(fps=15, bitrate="50k"). Allow you to give some options to the render process. You can, for example, disable the logger bar passing dict(logger=None).

center (bool, optional) – If true (default), the content will be wrapped in a <div align=middle> HTML container, so the content will be displayed at the center.

kwargs – Allow you to give some options, like width=260, etc. When editing looping gifs, a good choice is loop=1, autoplay=1.

Examples

from moviepy import *
# later ...
clip.display_in_notebook(width=360)
clip.audio.display_in_notebook()

clip.write_gif("test.gif")
display_in_notebook('test.gif')

clip.save_frame("first_frame.jpeg")
display_in_notebook("first_frame.jpeg")
iter_chunks(chunksize=None, chunk_duration=None, fps=None, quantize=False, nbytes=2, logger=None)[source]
Iterator that returns the whole sound array of the clip by chunks

max_volume(stereo=False, chunksize=50000, logger=None)[source]
Returns the maximum volume level of the clip.

to_soundarray(tt=None, fps=None, quantize=False, nbytes=2, buffersize=50000)[source]
Transforms the sound into an array that can be played by pygame or written in a wav file. See AudioClip.preview.

Parameters
:
fps – Frame rate of the sound for the conversion. 44100 for top quality.

nbytes – Number of bytes to encode the sound: 1 for 8bit sound, 2 for 16bit, 4 for 32bit sound.

write_audiofile(filename, fps=None, nbytes=2, buffersize=2000, codec=None, bitrate=None, ffmpeg_params=None, write_logfile=False, logger='bar')[source]
Writes an audio file from the AudioClip.

Parameters
:
filename – Name of the output file, as a string or a path-like object.

fps – Frames per second. If not set, it will try default to self.fps if already set, otherwise it will default to 44100.

nbytes – Sample width (set to 2 for 16-bit sound, 4 for 32-bit sound)

buffersize – The sound is not generated all at once, but rather made by bunches of frames (chunks). buffersize is the size of such a chunk. Try varying it if you meet audio problems (but you shouldn’t have to). Default to 2000

codec – Which audio codec should be used. If None provided, the codec is determined based on the extension of the filename. Choose ‘pcm_s16le’ for 16-bit wav and ‘pcm_s32le’ for 32-bit wav.

bitrate – Audio bitrate, given as a string like ‘50k’, ‘500k’, ‘3000k’. Will determine the size and quality of the output file. Note that it mainly an indicative goal, the bitrate won’t necessarily be the this in the output file.

ffmpeg_params – Any additional parameters you would like to pass, as a list of terms, like [‘-option1’, ‘value1’, ‘-option2’, ‘value2’]

write_logfile – If true, produces a detailed logfile named filename + ‘.log’ when writing the file

logger – Either "bar" for progress bar or None or any Proglog logger.

-----------------------------------------------------


AudioClip
AudioClip is the base class for all audio clips. If all you want is to edit audio files, you will never need it.

All you need is to define a function frame_function(t) which returns a Nx1 or Nx2 numpy array representing the sound at time t.

from moviepy import AudioClip
import numpy as np


def audio_frame(t):
    """Producing a sinewave of 440 Hz -> note A"""
    return np.sin(440 * 2 * np.pi * t)


audio_clip = AudioClip(frame_function=audio_frame, duration=3)
For more, see AudioClip.

AudioFileClip
AudioFileClip is used to load an audio file. This is probably the only kind of audio clip you will use.

You simply pass it the file you want to load :

from moviepy import *

# Works for audio files, but also videos file where you only want the keep the audio track
clip = AudioFileClip("example.wav")
clip.write_audiofile("./result.wav")
For more, see AudioFileClip.



-------------------------------------------


Working imports:
from moviepy.editor import VideoFileClip
from moviepy.editor import (
    AudioFileClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
    concatenate_videoclips,
    ColorClip,
    VideoClip,
    vfx
)
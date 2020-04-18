import os
import pyaudio
import _thread
import wave
import time
import requests
import base64
import uuid
import key

ak = key.ak
sk = key.sk


class Recorder:
    def __init__(self, chunk=1024, rec_channels=1, rate=16000):
        self.CHUNK = chunk
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = rec_channels
        self.RATE = rate
        self._running = True
        self._frames = []

    @staticmethod
    def findInternalRecordingDevice(p):
        target = '立体声混音'
        for z in range(p.get_device_count()):
            devInfo = p.get_device_info_by_index(z)
            if devInfo['name'].find(target) >= 0 and devInfo['hostApi'] == 0:
                return z
        print('无法找到内录设备!')
        return -1

    def start(self):
        _thread.start_new_thread(self.__record, ())

    def __record(self):
        self._running = True
        self._frames = []

        p = pyaudio.PyAudio()
        dev_idx = self.findInternalRecordingDevice(p)
        if dev_idx < 0:
            return
        stream = p.open(input_device_index=dev_idx,
                        format=self.FORMAT,
                        channels=self.CHANNELS,
                        rate=self.RATE,
                        input=True,
                        frames_per_buffer=self.CHUNK)
        while self._running:
            data = stream.read(self.CHUNK)
            self._frames.append(data)

        stream.stop_stream()
        stream.close()
        p.terminate()
        return

    def stop(self):
        self._running = False

    def save(self, fileName):
        p = pyaudio.PyAudio()
        wf = wave.open(fileName, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(p.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(self._frames))
        wf.close()
        p.terminate()


def get_token(api_key=ak, secret_key=sk):
    api_key = api_key
    secret_key = secret_key
    return requests.get('https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id='
                        + api_key + '&client_secret=' + secret_key).json()['access_token']


framerate = 16000
num_samples = 2000
channels = 1
sampwidth = 2
FILEPATH = "record/rec.wav"


def speech2text(speech_data, token, dev_pid=1737):
    FORMAT = 'wav'
    RATE = '16000'
    CHANNEL = 1
    address = hex(uuid.getnode())[2:]
    CUID = '-'.join(address[m:m + 2] for m in range(0, len(address), 2))
    SPEECH = base64.b64encode(speech_data).decode('utf-8')
    data = {
        'format': FORMAT,
        'rate': RATE,
        'channel': CHANNEL,
        'cuid': CUID,
        'len': len(speech_data),
        'speech': SPEECH,
        'token': token,
        'dev_pid': dev_pid
    }
    url_post = 'https://vop.baidu.com/server_api'
    headers = {'Content-Type': 'application/json'}
    r = requests.post(url_post, json=data, headers=headers)
    Result = r.json()
    if 'result' in Result:
        return Result['result'][0]
    else:
        return Result


def get_audio(file):
    with open(file, 'rb') as f:
        data = f.read()
    return data


def temp():
    speech = get_audio(FILEPATH)
    if os.path.exists(FILEPATH):
        os.remove(FILEPATH)
    return speech2text(speech, get_token())


if __name__ == "__main__":
    if not os.path.exists('record'):
        os.makedirs('record')

    print("\npython 录音机 ....\n")
    print("提示：按 r 键并回车 开始录音\n")

    i = input('请输入操作码:')
    if i == 'r':
        rec = Recorder()
        begin = time.time()

        print("\n开始录音,按 s 键并回车 停止录音，自动保存到 record 子目录\n")
        rec.start()

        running = True
        while running:
            i = input("请输入操作码:")
            if i == 's':
                running = False
                print("录音已停止")
                rec.stop()
                t = time.time() - begin
                print('录音时间为%ds' % t)
                rec.save("record/rec.wav")
    r = temp()
    print(r)
    data = {
        'doctype': 'json',
        'type': 'AUTO',
        'i': r
    }
    url = "http://fanyi.youdao.com/translate"
    r1 = requests.get(url, params=data)
    result = r1.json()
    print(result['translateResult'][0][0]['tgt'])
    input('按任意键退出')

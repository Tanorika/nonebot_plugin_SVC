import io
import logging
import edge_tts
from pathlib import Path
import os
import numpy as np
import soundfile
from .inference import infer_tool
from .inference import slicer
from .inference.infer_tool import Svc
from .config import Config
from nonebot import get_driver
logging.getLogger('numba').setLevel(logging.WARNING)
current_path = os.path.dirname(__file__)
chunks_dict = infer_tool.read_temp(current_path+"/inference/chunks_temp.json")
plugin_config = Config.parse_obj(get_driver().config)
#import部分结束


async def texttosound(spk_list,model_path,config_path,cluster_model_path,voice,msg):
    rate = '-4%'            #语速
    volume = '+0%'          #音量    
    output = current_path+'/raw/origin.wav'
    tts = edge_tts.Communicate(msg, voice=voice, rate=rate, volume=volume)
    await tts.save(output)
    botmain(model_path,config_path,cluster_model_path,spk_list)
def botmain(model_path,config_path,cluster_model_path,spk_list):
    enhancer_adaptive_key = plugin_config.enhancer_adaptive_key  # 使增强器适应更高的音域(单位为半音数)|默认为0
    clean_names = plugin_config.clean_names  # wav文件名列表，放在raw文件夹下
    slice_db = plugin_config.slice_db  # 默认-40，嘈杂的音频可以-30，干声保留呼吸可以-50
    wav_format = plugin_config.wav_format  # 音频输出格式
    auto_predict_f0 = plugin_config.auto_predict_f0  # 语音转换自动预测音高，转换歌声时不要打开这个会严重跑调
    cluster_infer_ratio = plugin_config.cluster_infer_ratio  # 聚类方案占比，范围0-1，若没有训练聚类模型则默认0即可
    noice_scale = plugin_config.noice_scale  # 噪音级别，会影响咬字和音质，较为玄学
    pad_seconds = plugin_config.pad_seconds  # 推理音频pad秒数，由于未知原因开头结尾会有异响，pad一小段静音段后就不会出现
    clip = plugin_config.clip  # 音频强制切片，默认0为自动切片，单位为秒/s
    lg = plugin_config.lg  # 两段音频切片的交叉淡入长度，如果强制切片后出现人声不连贯可调整该数值，如果连贯建议采用默认值0，单位为秒
    lgr = plugin_config.lgr  # 自动音频切片后，需要舍弃每段切片的头尾。该参数设置交叉长度保留的比例，范围0-1,左开右闭
    F0_mean_pooling = plugin_config.F0_mean_pooling  # 是否对F0使用均值滤波器(池化)，对部分哑音有改善。注意，启动该选项会导致推理速度下降，默认关闭
    enhance = plugin_config.enhance  # 是否使用NSF_HIFIGAN增强器,该选项对部分训练集少的模型有一定的音质增强效果，但是对训练好的模型有反面效果，默认关闭
    trans = plugin_config.trans  # 音高，自动预测开启后无需配置
    device = plugin_config.device  # 推理设备，None则为自动选择cpu和gpu
     
    svc_model = Svc(model_path, config_path, device, cluster_model_path,enhance)
    
    
    infer_tool.mkdir(["raw", "results"])

    infer_tool.fill_a_to_b(trans, clean_names)
    for clean_name, tran in zip(clean_names, trans):
        raw_audio_path = f"{clean_name}"
        if "." not in raw_audio_path:
            raw_audio_path += ".wav"
        infer_tool.format_wav(raw_audio_path)
        wav_path = Path(raw_audio_path).with_suffix('.wav')
        chunks = slicer.cut(wav_path, db_thresh=slice_db)
        audio_data, audio_sr = slicer.chunks2audio(wav_path, chunks)
        per_size = int(clip*audio_sr)
        lg_size = int(lg*audio_sr)
        lg_size_r = int(lg_size*lgr)
        lg_size_c_l = (lg_size-lg_size_r)//2
        lg_size_c_r = lg_size-lg_size_r-lg_size_c_l
        lg = np.linspace(0,1,lg_size_r) if lg_size!=0 else 0

        for spk in spk_list:
            audio = []
            for (slice_tag, data) in audio_data:
                print(f'#=====segment start, {round(len(data) / audio_sr, 3)}s======')
                
                length = int(np.ceil(len(data) / audio_sr * svc_model.target_sample))
                if slice_tag:
                    print('jump empty segment')
                    _audio = np.zeros(length)
                    audio.extend(list(infer_tool.pad_array(_audio, length)))
                    continue
                if per_size != 0:
                    datas = infer_tool.split_list_by_n(data, per_size,lg_size)
                else:
                    datas = [data]
                for k,dat in enumerate(datas):
                    per_length = int(np.ceil(len(dat) / audio_sr * svc_model.target_sample)) if clip!=0 else length
                    if clip!=0: print(f'###=====segment clip start, {round(len(dat) / audio_sr, 3)}s======')
                    # padd
                    pad_len = int(audio_sr * pad_seconds)
                    dat = np.concatenate([np.zeros([pad_len]), dat, np.zeros([pad_len])])
                    raw_path = io.BytesIO()
                    soundfile.write(raw_path, dat, audio_sr, format="wav")
                    raw_path.seek(0)
                    out_audio, out_sr = svc_model.infer(spk, tran, raw_path,
                                                        cluster_infer_ratio=cluster_infer_ratio,
                                                        auto_predict_f0=auto_predict_f0,
                                                        noice_scale=noice_scale,
                                                        F0_mean_pooling = F0_mean_pooling,
                                                        enhancer_adaptive_key = enhancer_adaptive_key
                                                        )
                    _audio = out_audio.cpu().numpy()
                    pad_len = int(svc_model.target_sample * pad_seconds)
                    _audio = _audio[pad_len:-pad_len]
                    _audio = infer_tool.pad_array(_audio, per_length)
                    if lg_size!=0 and k!=0:
                        lg1 = audio[-(lg_size_r+lg_size_c_r):-lg_size_c_r] if lgr != 1 else audio[-lg_size:]
                        lg2 = _audio[lg_size_c_l:lg_size_c_l+lg_size_r]  if lgr != 1 else _audio[0:lg_size]
                        lg_pre = lg1*(1-lg)+lg2*lg
                        audio = audio[0:-(lg_size_r+lg_size_c_r)] if lgr != 1 else audio[0:-lg_size]
                        audio.extend(lg_pre)
                        _audio = _audio[lg_size_c_l+lg_size_r:] if lgr != 1 else _audio[lg_size:]
                    audio.extend(list(_audio))
            key = "auto" if auto_predict_f0 else f"{tran}key"
            cluster_name = "" if cluster_infer_ratio == 0 else f"_{cluster_infer_ratio}"
            res_path = f'{current_path}/results/qqbot.{wav_format}'
            soundfile.write(res_path, audio, svc_model.target_sample, format=wav_format)
            svc_model.clear_empty()

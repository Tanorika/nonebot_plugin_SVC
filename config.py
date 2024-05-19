from pydantic import BaseModel
import os
current_path = os.path.dirname(__file__)
class Config(BaseModel):
    enhancer_adaptive_key: int = 0  # 使增强器适应更高的音域(单位为半音数)|默认为0
    clean_names: list = [current_path + "/raw/origin.wav"]  # wav文件名列表，放在raw文件夹下
    slice_db: int = -40  # 默认-40，嘈杂的音频可以-30，干声保留呼吸可以-50
    wav_format: str = 'wav'  # 音频输出格式x
    auto_predict_f0: bool = True  # 语音转换自动预测音高，转换歌声时不要打开这个会严重跑调
    cluster_infer_ratio: float = 0  # 聚类方案占比，范围0-1，若没有训练聚类模型则默认0即可
    noice_scale: float = 0.4  # 噪音级别，会影响咬字和音质，较为玄学
    pad_seconds: float = 0.5  # 推理音频pad秒数，由于未知原因开头结尾会有异响，pad一小段静音段后就不会出现
    clip: int = 0  # 音频强制切片，默认0为自动切片，单位为秒/s
    lg: int = 0  # 两段音频切片的交叉淡入长度，如果强制切片后出现人声不连贯可调整该数值，如果连贯建议采用默认值0，单位为秒
    lgr: float = 0.75  # 自动音频切片后，需要舍弃每段切片的头尾。该参数设置交叉长度保留的比例，范围0-1,左开右闭
    F0_mean_pooling: bool = False  # 是否对F0使用均值滤波器(池化)，对部分哑音有改善。注意，启动该选项会导致推理速度下降，默认关闭
    enhance: bool = False  # 是否使用NSF_HIFIGAN增强器,该选项对部分训练集少的模型有一定的音质增强效果，但是对训练好的模型有反面效果，默认关闭
    trans: list = [0]  # 音高，自动预测开启后无需配置
    device: str = None  # 推理设备，None则为自动选择cpu和gpu

    
    
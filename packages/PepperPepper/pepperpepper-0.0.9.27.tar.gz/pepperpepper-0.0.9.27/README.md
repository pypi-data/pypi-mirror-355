# Pepper
## Version：0
##### Version:0.0.9.6
PepperV0.0.9.6

FFT_PriorFilter: We added a Fourier prior module to the layers/custom_layer.py for prior knowledge filter.

SCTransNet: We reproduce the SCTrans model for infrared small target detection.

##### Version:0.0.9.7
get_all_images: It can get all the images in a directory and pass set the load_images to control whether it load the image or return path.it locate the datasets/dataset_utils.py.

get_img_norm_cfg: It can get the norm parameters in a directory all the images to adjust.it locate the datasets/dataset_utils.py.

DataSetLoader: It is Dataset for IRSTD datasets.it locate the IRSTD/datasets.

##### Version:0.0.9.8
IRSTDTrainer: The training of the task is integrated for IRSTD. It locate the IRSTD/callbacks.

##### Version:0.0.9.8.post1
We repair the IRSTDTrainer's Test epoch num error.

##### Version:0.0.9.9
We reproduce Wavelet Transform as Convolutions.It is located the layers/WTConv.py.

##### Version:0.0.9.10
We reproduce MLPnet on IRSTD/models.

##### Version:0.0.9.11
We reproduce MoE and HeirarchicalMoE in models/mixture_of_experts.

##### Version:0.0.9.12
We design the combination of Gate and wavelet dubbed as GateWTConv in layers/GateWTConv.

##### Version:0.0.9.13
We redesign the optimizer and schedule of config and getting obejct in the  callbacks/config_setting.py.

##### Version:0.0.9.14
We redesign the tools and write the Get2FA function on the tools.

##### Version:0.0.9.15
We reproduce the SS2D and VSSBlock on the layers/mamba.py

##### Version:0.0.9.16
We design the ExtractEmbedding on the layers/ExtractEmbedding.py. 

We design the SobelHighFreqEnhance Module on the layers/HighFreqEnhance.py

We design the visualize_tensor on the tools/Visualize_tensor.py for visualize the out that is tensor type.

##### Version:0.0.9.17
CrossScaleFeature: It is the multi scale kernel to extract the feature in layers/MultiScaleFeature.py.

MultiScaleSPWDilate: It is the multi scale dilate conv and each one path synerging-competition in layers/MultiScaleFeature.py.

AttentionalCS：Channels are linked to spatial attention in layers/attention.py.

##### Version:0.0.9.18
VMUNet: It is UNet structure using vssmblock in IRSTD/models.

##### Version:0.0.9.19
Global_Context_Mamba_Bridge: It is the use of MAMBA to integrate contextual information.

Coopetition_Fuse: It is the synerging and competition between all feature.

collect_image_names: It output the file of txt from document for image.

##### Version:0.0.9.20
AlternateCat: It alternatly concatenate A and B by the offered dims.

CM2UNet:It redesign the combination of mamba and Unet construction for IRSTD.

UNet: It is UNet constructment for IRSTD.

analyze_connected_pixels: Statistics on connected area properties in datasets/Analyze_Connected_Pixels.py

ManualConv2D: Implementation of manual convolution layer in layers/ManualConv2D

IRGradOri: This is a conventional trainable gradient infrared small target detection module

##### Version:0.0.9.21
IRGradOriNet: This is using the UNet constructure for IRSTD

RL: It is the reinforce learning package.

##### Version:0.0.9.22
IRFourierStatFocus: Infrared Fourier truncation enhancement

Mario: This is reinforcement learning about mario's code in RL

##### Version:0.0.9.23
[Translate_COCO.py](PepperPepper/datasets/Translate_COCO.py):It is the tool that translate other version datasets to COCO type.

[Gated_Bottleneck_Convolution.py](PepperPepper/layers/Gated_Bottleneck_Convolution.py):门控瓶颈卷积（Gated Bottleneck Convolution, GBC）

##### Version:0.0.9.24
[IRWACV.py](PepperPepper/IRSTD/models/IRWACV.py):It is the new IRSTD model for pix2pix


##### Version:0.0.9.25
WUNet:It is the Wave-UNet constructure for try













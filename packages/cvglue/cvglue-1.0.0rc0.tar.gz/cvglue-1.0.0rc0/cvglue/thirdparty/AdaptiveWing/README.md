Source project: https://github.com/protossw512/AdaptiveWingLoss

dataset: WFLW

一般情况下非常准，瞳孔也准  
人脸框部分超出屏幕的话，超出部分会__非常不准__，BORDER 方式严重影响最终结果  
个别不清晰或大幅度偏转时效果会非常差  

用 crop_face_v4 来对齐是最好的
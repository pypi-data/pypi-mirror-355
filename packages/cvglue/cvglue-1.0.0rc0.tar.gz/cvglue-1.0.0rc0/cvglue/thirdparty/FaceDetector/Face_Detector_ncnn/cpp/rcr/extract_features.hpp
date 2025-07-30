//
// Created by admin on 2017/7/26.
//

#ifndef FACE_DETECT_CNN_EXTRACT_FEATURES_HPP
#define FACE_DETECT_CNN_EXTRACT_FEATURES_HPP

#include <vector>
#include "config.hpp"

extern void FeatureExtractor_Init(std::vector<std::vector<int>> &calcId, int num_landmarks, ModeSelect mode);
extern void FeatureExtractor_Extract(const unsigned char *gray_image, float **feature,
                              float *parameters, int img_rows, int img_cols,
                              int regressor_level, ModeSelect mode);

#endif //FACE_DETECT_CNN_EXTRACT_FEATURES_HPP

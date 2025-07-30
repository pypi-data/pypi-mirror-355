//
// Created by admin on 2017/7/26.
//

#include "basift.hpp"
#include "dsift.hpp"
#include "extract_features.hpp"

static BASiftTransform basift;
static DenseSiftTransform dsift;

void FeatureExtractor_Init(std::vector<std::vector<int>> &calcId, int num_landmarks, ModeSelect mode)
{
    switch(mode)
    {
        case P106_WITH_5_POINTS:
            dsift.init_dsift(calcId, num_landmarks);
            break;
        case P106_WITHOUT_5_POINTS:
            basift.init_basift(calcId, num_landmarks);
            break;
        case P68_WITH_5_POINTS:
            dsift.init_dsift(calcId, num_landmarks);
            break;
    }
}

void FeatureExtractor_Extract(const unsigned char *gray_image, float **feature,
                                        float *parameters, int img_rows, int img_cols,
                                        int regressor_level, ModeSelect mode)
{
    switch(mode)
    {
        case P106_WITH_5_POINTS:
        case P68_WITH_5_POINTS:
            dsift(gray_image, feature, parameters, img_rows, img_cols, regressor_level);
            break;
        case P106_WITHOUT_5_POINTS:
            basift(gray_image, feature, parameters, img_rows, img_cols, regressor_level);
            break;
    }
}


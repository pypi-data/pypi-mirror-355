//
// Created by admin on 2017/7/21.
//

#ifndef FACE_DETECT_CNN_RCR_DETECT_HPP
#define FACE_DETECT_CNN_RCR_DETECT_HPP

#include <rcr/config.hpp>

#define LOAD_MODEL_ENALBE    1
#define LOAD_MODEL_DISALBE   0

extern void face_alignment(const unsigned char *src_image, const int *face_rect, float *out_shape,
                           float *align_points, int image_rows, int image_cols, const int shape_total_points,
                           const ModeSelect mode);
extern int face_align_config(const char *model_name, ModeSelect mode);

#endif //FACE_DETECT_CNN_RCR_DETECT_HPP

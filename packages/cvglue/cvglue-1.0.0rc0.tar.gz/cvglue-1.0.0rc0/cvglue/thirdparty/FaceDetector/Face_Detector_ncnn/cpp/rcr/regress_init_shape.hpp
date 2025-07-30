//
// Created by admin on 2017/7/26.
//

#ifndef FACE_DETECT_CNN_REGRESS_INIT_SHAPE_HPP
#define FACE_DETECT_CNN_REGRESS_INIT_SHAPE_HPP

#include <vector>
#include "config.hpp"

extern float get_ied(float *shape, int num_landmark);
extern void getInitShape(float *mean_shape, const float *align_points, float *out_shape, int num_points, const int *face_box, ModeSelect mode);

#endif //FACE_DETECT_CNN_REGRESS_INIT_SHAPE_HPP

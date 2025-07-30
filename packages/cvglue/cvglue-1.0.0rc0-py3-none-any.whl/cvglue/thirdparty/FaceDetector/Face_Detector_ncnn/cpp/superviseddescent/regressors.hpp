/*
 * superviseddescent: A C++11 implementation of the supervised descent
 *                    optimisation method
 * File: superviseddescent/regressors.hpp
 *
 * Copyright 2014, 2015 Patrik Huber
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
#pragma once

#ifndef REGRESSORS_HPP_
#define REGRESSORS_HPP_

#include <iostream>
#include <stdio.h>
//#include <define.h>
#include <rcr-detect.hpp>
#include <rcr/config.hpp>
//#include <arm_neon.h>
#include <vector>
#include <malloc.h>

#define REGRESSOR_NUM_106		        2
#define GLOBAL_REGRESSOR_NUM_106	    1
#define REGRESSOR_NUM_106_FAST          4
#define GLOBAL_REGRESSOR_NUM_106_FAST	2
#define REGRESSOR_NUM_68		        4
#define GLOBAL_REGRESSOR_NUM_68	        2

#define FEATURE_DIMENSION   128

namespace superviseddescent {

/**
 * A simple LinearRegressor that learns coefficients x for the linear relationship
 * \f$ Ax = b \f$. This class handles learning, testing, and predicting single examples.
 *
 * A Regulariser can be specified to make the least squares problem more
 * well-behaved (or invertible, in case it is not).
 *
 * Works with multi-dimensional label data. In that case, the coefficients for
 * each label will be learned independently.
 */
class LinearRegressor
{
    public:
        /**
         * Creates a LinearRegressor with no regularisation.
         *
         * @param[in] regulariser A Regulariser to regularise the data matrix. Default means no regularisation.
         */
        LinearRegressor() : x(), x_reg(), r_bias()
        {
        };

        void gemm_neon(const float *lhs, const float *rhs, float *out_mat, int rhs_rows, int rhs_cols);


        /**
         * Predicts the regressed value for one given sample.
         *
         * @param[in] values One data point as a row vector.
         * @return The predicted value(s).
         */

        void predict(float **value, std::vector<float> &output, size_t regressor_level, int shape_total_point, ModeSelect mode);

        float *x;
        int x_rows, x_cols;
        std::vector<float *> x_reg;
        std::vector<int> x_reg_rows, x_reg_cols;
	    std::vector<int> r_bias;
};

} /* namespace superviseddescent */
#endif /* REGRESSORS_HPP_ */

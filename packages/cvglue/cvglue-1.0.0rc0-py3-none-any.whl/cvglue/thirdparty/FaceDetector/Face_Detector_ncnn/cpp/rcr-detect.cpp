/*
 * superviseddescent: A C++11 implementation of the supervised descent
 *                    optimisation method
 * File: apps/rcr/rcr-detect.cpp
 *
 * Copyright 2015 Patrik Huber
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
//#include "superviseddescent/superviseddescent.hpp"
//#include "superviseddescent/regressors.hpp"

#include "superviseddescent/regressors.hpp"
#include "rcr-detect.hpp"

#include "svdcmp.hpp"

#include <vector>
#include <iostream>
#include <fstream>
#include <random>
#include <errno.h>
//#include <define.h>
#include <rcr/extract_features.hpp>
#include <rcr/regress_init_shape.hpp>

using namespace std;
using namespace superviseddescent;

float mean_shape_data_106[] = { -0.500212,-0.497459,-0.498729,-0.497712,-0.493233,-0.484589,-0.471338,-0.45303,-0.42757,-0.394972,-0.355974,-0.311136,-0.261595,-0.207447,-0.147255,-0.0790475,-3.08565e-09,0.0790475,0.147255,0.207447,0.261594,0.311135,0.355974,0.394972,0.427571,0.453029,0.471337,0.48459,0.493234,0.497709,0.498729,0.497459,0.500212,-0.404347,-0.334398,-0.253534,-0.17113,-0.0984492,0.0984491,0.17113,0.253534,0.334398,0.404348,-3.15688e-09,-4.51024e-09,-4.85214e-09,-3.1056e-09,-0.102692,-0.0498893,-8.34807e-10,0.0498893,0.102692,-0.319057,-0.274088,-0.173617,-0.133267,-0.179643,-0.275416,0.133267,0.173617,0.274088,0.319058,0.275416,0.179643,-0.327848,-0.255389,-0.178598,-0.102167,0.102167,0.178598,0.255388,0.327848,-0.223182,-0.227916,-0.224174,0.223182,0.227916,0.224174,-0.0705873,0.0705873,-0.104942,0.104942,-0.140356,0.140356,-0.204509,-0.128489,-0.0475093,8.17712e-10,0.0475093,0.12849,0.204508,0.149918,0.084879,9.08885e-10,-0.084879,-0.149918,-0.168525,-0.0802309,-1.00861e-09,0.0802309,0.168525,0.0818455,-1.09978e-09,-0.0818455,-0.222253,0.222253,-0.196413,-0.125508,-0.0563693,0.0124181,0.0808483,0.149488,0.218793,0.286724,0.351914,0.413434,0.470941,0.523863,0.572793,0.618763,0.657746,0.684175,0.693226,0.684176,0.657746,0.618764,0.572794,0.523862,0.470941,0.413433,0.351914,0.286724,0.218793,0.149489,0.0808484,0.0124181,-0.0563693,-0.125508,-0.196413,-0.24992,-0.290746,-0.299809,-0.287065,-0.250249,-0.250249,-0.287065,-0.299809,-0.290746,-0.24992,-0.151156,-0.060637,0.029383,0.118725,0.180765,0.185161,0.204796,0.18516,0.180765,-0.142494,-0.170065,-0.165999,-0.128509,-0.118589,-0.122672,-0.128509,-0.165999,-0.170065,-0.142494,-0.122671,-0.118589,-0.242218,-0.246466,-0.238278,-0.229228,-0.229228,-0.238278,-0.246465,-0.242218,-0.179283,-0.114604,-0.151958,-0.179282,-0.114604,-0.151957,-0.125073,-0.125073,0.0627526,0.0627525,0.143596,0.143596,0.330031,0.304127,0.288335,0.300467,0.288335,0.304127,0.330031,0.394623,0.436001,0.451286,0.436001,0.394622,0.33693,0.332163,0.337542,0.332163,0.33693,0.37358,0.384757,0.37358,-0.151516,-0.151516 };
float mean_shape_data_68[] = { -0.513881, -0.510726, -0.496027, -0.467656, -0.414523, -0.333173, -0.233632, -0.123929, 5.01754e-010, 0.123929, 0.233632, 0.333173, 0.414523, 0.467656, 0.496027, 0.510726, 0.513881, -0.416678, -0.352805, -0.262017, -0.168067, -0.080468, 0.080468, 0.168067, 0.262017, 0.352805, 0.416678, 3.26614e-010, -3.55015e-010, -1.21652e-009, -4.49686e-010, -0.105404, -0.0546911, 8.85171e-010, 0.0546911, 0.105404, -0.312849, -0.257323, -0.190599, -0.131909, -0.19475, -0.261225, 0.131909, 0.190599, 0.257323, 0.312849, 0.261225, 0.19475, -0.199469, -0.125964, -0.0515452, 1.37746e-009, 0.0515452, 0.125964, 0.199469, 0.128228, 0.0560781, -4.26018e-011, -0.0560781, -0.128228, -0.168953, -0.0522786, 3.45548e-010, 0.0522786, 0.168953, 0.0532968, -2.36677e-010, -0.0532968, -0.125559, 0.0101943, 0.145426, 0.277808, 0.400515, 0.506841, 0.595653, 0.666693, 0.687626, 0.666693, 0.595653, 0.506841, 0.400515, 0.277808, 0.145426, 0.0101943, -0.125559, -0.227179, -0.285542, -0.302947, -0.289565, -0.252456, -0.252456, -0.289565, -0.302947, -0.285542, -0.227179, -0.146604, -0.0590897, 0.0277219, 0.117172, 0.177837, 0.196256, 0.21216, 0.196256, 0.177837, -0.135324, -0.167468, -0.166632, -0.122214, -0.110868, -0.111775, -0.122214, -0.166632, -0.167468, -0.135324, -0.111775, -0.110868, 0.341063, 0.31159, 0.296146, 0.309078, 0.296146, 0.31159, 0.341063, 0.41268, 0.443828, 0.449664, 0.443828, 0.41268, 0.344885, 0.339596, 0.345083, 0.339595, 0.344885, 0.377937, 0.384283, 0.377937 };

float *align_mean(float *mean, float *aligned_mean, int num_points, const int *facebox, float scaling_x=1.0f, float scaling_y=1.0f, float translation_x=0.0f, float translation_y=0.0f)
{
    // Initial estimate x_0: Center the mean face at the [-0.5, 0.5] x [-0.5, 0.5] square (assuming the face-box is that square)
    // More precise: Take the mean as it is (assume it is in a space [-0.5, 0.5] x [-0.5, 0.5]), and just place it in the face-box as
    // if the box is [-0.5, 0.5] x [-0.5, 0.5]. (i.e. the mean coordinates get upscaled)
    for(int i = 0; i < num_points; ++i)
    {
        aligned_mean[i] = (mean[i]*scaling_x + 0.5f + translation_x) * facebox[2] + facebox[0];
        aligned_mean[i+num_points] = (mean[i+num_points]*scaling_y + 0.5f + translation_y) * facebox[3] + facebox[1];
    }
    return aligned_mean;
}

// 106 without 5points align
//int feature_cfg_1[] = { 8,12,16,20,24,33,37,38,42,46,47,51,52,55,58,61,65,70,72,73,74,75,76,77,84,87,90,93,98,102 };
//int feature_cfg_2[] = { 8,12,16,20,24,33,35,37,38,40,42,46,47,51,52,53,54,55,56,57,58,59,60,61,62,63,65,70,74,77,84,86,87,88,90,92,93,94,98,102 };
//int feature_cfg_3[] = { 8,12,16,20,24,33,35,37,38,40,42,46,47,51,52,53,54,55,56,57,58,59,60,61,62,63,65,70,74,77,84,86,87,88,90,92,93,94,98,102 };
//int feature_cfg_4[] = { 8,10,12,14,16,18,20,22,24,33,35,37,38,40,42,46,47,51,52,53,54,55,56,57,58,59,60,61,62,63,65,70,74,77,84,86,87,88,90,92,93,94,98,102 };
//int feature_cfg_5[] = { 8,10,12,14,16,18,20,22,24,33,35,37,38,40,42,46,47,51,52,53,54,55,56,57,58,59,60,61,62,63,65,70,74,77,84,86,87,88,90,92,93,94,98,102 };
//int cfg_1_prefix[] = { 30, 5, 7, 9, 12, 14, 16, 17, 18, 21, 24, 24, 30 };
//int cfg_2_prefix[] = { 40, 5, 8, 11, 14, 20, 26, 27, 28, 29, 30, 30, 40 };
//int cfg_3_prefix[] = { 40, 5, 8, 11, 14, 20, 26, 27, 28, 29, 30, 30, 40 };
//int cfg_4_prefix[] = { 44, 9, 12, 15, 18, 24, 30, 31, 32, 33, 34, 34, 44 };
//int cfg_5_prefix[] = { 44, 9, 12, 15, 18, 24, 30, 31, 32, 33, 34, 34, 44 };

void regressorSetConfig(LinearRegressor &regressor, int config[], ModeSelect mode)
{
	regressor.r_bias.clear();
    switch(mode)
    {
        case P106_WITH_5_POINTS:
        case P106_WITHOUT_5_POINTS:
        {
            regressor.r_bias.resize(13);
            for (int idx = 0; idx < 13; ++idx) {
                regressor.r_bias[idx] = config[idx];
            }
            break;
        }
        case P68_WITH_5_POINTS:
        {
            regressor.r_bias.resize(8);
            for (int idx = 0; idx < 8; ++idx) {
                regressor.r_bias[idx] = config[idx];
            }
            break;
        }
    }
}

// Without model data checking and memory free.
int load_model(vector<LinearRegressor> &regressors, const char *model_name, ModeSelect mode)
{
    int regressor_num = 0;
    int global_regressor_num = 0;
    switch (mode)
    {
        case P106_WITH_5_POINTS:
            regressor_num = REGRESSOR_NUM_106;
            global_regressor_num = GLOBAL_REGRESSOR_NUM_106;
            break;
        case P106_WITHOUT_5_POINTS:
            regressor_num = REGRESSOR_NUM_106_FAST;
            global_regressor_num = GLOBAL_REGRESSOR_NUM_106_FAST;
            break;
        case P68_WITH_5_POINTS:
            regressor_num = REGRESSOR_NUM_68;
            global_regressor_num = GLOBAL_REGRESSOR_NUM_68;
            break;
    }
	regressors.clear();
	regressors.resize(regressor_num);

	FILE *model_file = fopen(model_name, "rb");
	if(model_file == NULL)
	{
		return errno;
	}

	for(int i = 0; i < global_regressor_num; ++i)
	{
		int x_rows, x_cols;
        fread(&x_cols, sizeof(int), 1, model_file);
		fread(&x_rows, sizeof(int), 1, model_file);
		float *x = (float *) malloc(sizeof(float) * x_rows * x_cols);
		fread(x, sizeof(float), x_rows * x_cols, model_file);
//        regressors[i].x_ = Mat(x_cols, x_rows, CV_32FC1, x).t();
        regressors[i].x_rows = x_rows;
        regressors[i].x_cols = x_cols;
        regressors[i].x = x;
//        regressors[i].x_rows = regressors[i].x_.rows;
//        regressors[i].x_cols = regressors[i].x_.cols;
//        regressors[i].x = (float *)regressors[i].x_.data;

//        regressors[i].x = (float*)malloc(temp.rows*temp.cols* sizeof(float));
//        for (int j = 0; j < temp.rows; ++j)
//        {
//            float *dptr = regressors[i].x+j*temp.cols;
//            float *sptr = (float*)temp.ptr(j);
//            memcpy(dptr, sptr, temp.cols* sizeof(float));
//        }
//        regressors[i].x_rows = temp.rows;
//        regressors[i].x_cols = temp.cols;
//		regressors[i].x = Mat(x_rows, x_cols, CV_32FC1, x);
	}

	for(int i = global_regressor_num; i < regressor_num; ++i)
	{
        regressors[i].x_reg_rows.resize(5);
        regressors[i].x_reg_cols.resize(5);
		regressors[i].x_reg.resize(5);
		for(int n = 0; n < 5; ++n)
		{
			int x_reg_rows, x_reg_cols;
            fread(&x_reg_cols, sizeof(int), 1, model_file);
			fread(&x_reg_rows, sizeof(int), 1, model_file);
			float *xreg = (float *)malloc(sizeof(float) * x_reg_rows * x_reg_cols);
			fread(xreg, sizeof(float), x_reg_rows * x_reg_cols, model_file);
//            regressors[i].x_reg_[n] = Mat(x_reg_cols, x_reg_rows, CV_32FC1, xreg).t();
            regressors[i].x_reg_rows[n] = x_reg_rows;
            regressors[i].x_reg_cols[n] = x_reg_cols;
			regressors[i].x_reg[n] = xreg;
//            regressors[i].x_reg_rows[n] = regressors[i].x_reg_[n].rows;
//            regressors[i].x_reg_cols[n] = regressors[i].x_reg_[n].cols;
//			regressors[i].x_reg[n] = (float *)regressors[i].x_reg_[n].data;
		}
	}

	return 0;
}

void unload_model(vector<LinearRegressor> &regressors)
{
    for(int i = 0; i < regressors.size(); ++i)
    {
        free(regressors[i].x);
        regressors[i].r_bias.clear();
        regressors[i].x_reg_rows.clear();
        regressors[i].x_reg_cols.clear();
        if(!regressors[i].x_reg.empty())
        {
            for(int n = 0; n < regressors[i].x_reg.size(); ++n)
            {
                free(regressors[i].x_reg[n]);
            }
            regressors[i].x_reg.clear();
        }
    }
    regressors.clear();
}

static vector<LinearRegressor> regressors;
static vector<int> right_eye_identifiers, left_eye_identifiers; // for ied calc. One or several.
static vector<vector<int>> extract_id;
int face_align_config(const char *model_name, ModeSelect mode_sel)
{
	//-------------- Load the learned model:
    if(!regressors.empty())
    {
        unload_model(regressors);
    }
	int checkf = load_model(regressors, model_name, mode_sel);
	if(checkf)
	{
		return checkf;
	}

    right_eye_identifiers.clear();
    left_eye_identifiers.clear();
    switch(mode_sel)
    {
        case P106_WITH_5_POINTS:
        case P106_WITHOUT_5_POINTS:
            right_eye_identifiers.push_back(74);
    //        right_eye_identifiers.push_back(104);
            left_eye_identifiers.push_back(77);
    //        left_eye_identifiers.push_back(105);
            break;
        case P68_WITH_5_POINTS:
            right_eye_identifiers.push_back(36);
            right_eye_identifiers.push_back(39);
            left_eye_identifiers.push_back(42);
            left_eye_identifiers.push_back(45);
            break;
    }

    extract_id.clear();
	extract_id.reserve(4);

    switch(mode_sel)
    {
        case P106_WITH_5_POINTS:
        {
            int feature_cfg_1[] = {9, 16, 23, 33, 35, 37, 38, 40, 42, 46, 47, 51, 52, 53, 54,
                                   55, 56, 57, 58, 59, 60, 61, 62, 63, 65, 70, 72, 73, 74, 75,
                                   76, 77, 84, 86, 87, 88, 90, 92, 93, 94, 97, 98, 99, 101, 102,
                                   103};
            int feature_cfg_2[] = {9, 16, 23, 33, 35, 37, 38, 40, 42, 46, 47, 51, 52, 53, 54,
                                   55, 56, 57, 58, 59, 60, 61, 62, 63, 65, 70, 72, 73, 74, 75,
                                   76, 77, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96,
                                   97, 98, 99, 100, 101, 102, 103};
            int cfg_1_prefix[] = {46, 3, 6, 9, 12, 18, 24, 25, 26, 29, 32, 32, 46};
            int cfg_2_prefix[] = {52, 3, 6, 9, 12, 18, 24, 25, 26, 29, 32, 32, 52};
            vector<int> vec_id1(feature_cfg_1,
                                feature_cfg_1 + sizeof(feature_cfg_1) / sizeof(int));
            vector<int> vec_id2(feature_cfg_2,
                                feature_cfg_2 + sizeof(feature_cfg_2) / sizeof(int));
            extract_id.push_back(vec_id1);
            extract_id.push_back(vec_id2);
            int *cfg_prefix[] = {cfg_1_prefix, cfg_2_prefix};
            for (int i = GLOBAL_REGRESSOR_NUM_106; i < REGRESSOR_NUM_106; ++i) {
                regressorSetConfig(regressors[i], cfg_prefix[i], mode_sel);
            }
            break;
        }
        case P106_WITHOUT_5_POINTS:
        {
            int feature_cfg_1[] = {9, 16, 23, 35, 40, 46, 47, 51, 52, 55, 58, 61, 72, 73, 75,
                                   76, 84, 87, 90, 93, 98, 102};
            int feature_cfg_2[] = {9, 16, 23, 33, 35, 37, 38, 40, 42, 46, 47, 51, 52, 53, 54,
                                   55, 56, 57, 58, 59, 60, 61, 62, 63, 65, 70, 74, 77, 84, 86,
                                   87, 88, 90, 92, 93, 94, 97, 98, 99, 101, 102, 103};
            int feature_cfg_3[] = {9, 16, 23, 33, 35, 37, 38, 40, 42, 46, 47, 51, 52, 53, 54,
                                   55, 56, 57, 58, 59, 60, 61, 62, 63, 65, 70, 74, 77, 84, 85,
                                   86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100,
                                   101, 102, 103};
            int feature_cfg_4[] = {9, 16, 23, 33, 35, 37, 38, 40, 42, 46, 47, 51, 52, 53, 54,
                                   55, 56, 57, 58, 59, 60, 61, 62, 63, 65, 70, 74, 77, 84, 85,
                                   86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100,
                                   101, 102, 103};
            int cfg_1_prefix[] = {28, 3, 5, 7, 10, 12, 14, 15, 16, 19, 22, 22, 28};
            int cfg_2_prefix[] = {42, 3, 6, 9, 12, 18, 24, 25, 26, 27, 28, 28, 42};
            int cfg_3_prefix[] = {48, 3, 6, 9, 12, 18, 24, 25, 26, 27, 28, 28, 48};
            int cfg_4_prefix[] = {48, 3, 6, 9, 12, 18, 24, 25, 26, 27, 28, 28, 48};
            vector<int> vec_id1(feature_cfg_1,
                                feature_cfg_1 + sizeof(feature_cfg_1) / sizeof(int));
            vector<int> vec_id2(feature_cfg_2,
                                feature_cfg_2 + sizeof(feature_cfg_2) / sizeof(int));
            vector<int> vec_id3(feature_cfg_3,
                                feature_cfg_3 + sizeof(feature_cfg_3) / sizeof(int));
            vector<int> vec_id4(feature_cfg_4,
                                feature_cfg_4 + sizeof(feature_cfg_4) / sizeof(int));
            extract_id.push_back(vec_id1);
            extract_id.push_back(vec_id2);
            extract_id.push_back(vec_id3);
            extract_id.push_back(vec_id4);
            int *cfg_prefix[] = {cfg_1_prefix, cfg_2_prefix, cfg_3_prefix, cfg_4_prefix};
            for (int i = GLOBAL_REGRESSOR_NUM_106_FAST; i < REGRESSOR_NUM_106_FAST; ++i) {
                regressorSetConfig(regressors[i], cfg_prefix[i], mode_sel);
            }
            break;
        }
        case P68_WITH_5_POINTS:
        {
            static int feature_cfg_1[] = { 3,8,12,17,19,21,22,24,26,30,31,35,36,37,38,39,40,41,42,43,44,45,46,47,48,50,51,52,54,56,57,58,62,66 };
            static int feature_cfg_2[] = { 3,8,12,17,19,21,22,24,26,30,31,35,36,37,38,39,40,41,42,43,44,45,46,47,48,50,51,52,54,56,57,58,62,66 };
            static int feature_cfg_3[] = { 3,8,12,17,19,21,22,24,26,30,31,35,36,37,38,39,40,41,42,43,44,45,46,47,48,50,51,52,54,56,57,58,62,66 };
            static int feature_cfg_4[] = { 3,8,12,17,19,21,22,24,26,30,31,35,36,37,38,39,40,41,42,43,44,45,46,47,48,50,51,52,54,56,57,58,62,66 };
            int cfg_1_prefix[] = { 34, 3, 6, 9, 12, 18, 24, 34 };
            int cfg_2_prefix[] = { 34, 3, 6, 9, 12, 18, 24, 34 };
            int cfg_3_prefix[] = { 34, 3, 6, 9, 12, 18, 24, 34 };
            int cfg_4_prefix[] = { 34, 3, 6, 9, 12, 18, 24, 34 };
            vector<int> vec_id1(feature_cfg_1, feature_cfg_1 + sizeof(feature_cfg_1) / sizeof(int));
            vector<int> vec_id2(feature_cfg_2, feature_cfg_2 + sizeof(feature_cfg_2) / sizeof(int));
            vector<int> vec_id3(feature_cfg_3, feature_cfg_3 + sizeof(feature_cfg_3) / sizeof(int));
            vector<int> vec_id4(feature_cfg_4, feature_cfg_4 + sizeof(feature_cfg_4) / sizeof(int));
            extract_id.push_back(vec_id1);
            extract_id.push_back(vec_id2);
            extract_id.push_back(vec_id3);
            extract_id.push_back(vec_id4);
            int *cfg_prefix[] = {cfg_1_prefix, cfg_2_prefix, cfg_3_prefix, cfg_4_prefix};
            for(int i = GLOBAL_REGRESSOR_NUM_68; i < REGRESSOR_NUM_68; ++i)
            {
                regressorSetConfig(regressors[i], cfg_prefix[i], mode_sel);
            }
            break;
        }
    }
	return 0;
}

void face_alignment(const unsigned char *gray_image, const int *face_rect, float *out_shape, float *align_points, int image_rows, int image_cols, const int shape_total_points, const ModeSelect mode)
{
//    Mat gray_image;
//    if (src_image.channels() == 3)
//    {
//        cv::cvtColor(src_image, gray_image, cv::COLOR_RGB2GRAY);
//    }
//    else if(src_image.channels() == 4)
//    {
//        cv::cvtColor(src_image, gray_image, cv::COLOR_RGBA2GRAY);
//    }
//    else {
//        gray_image = src_image;
//    }

	//-------------- Load mean shape:
//	Mat model_mean;
    float *model_mean;
    int regressor_num = 0;
    switch(mode)
    {
        case P106_WITH_5_POINTS:
//            model_mean = Mat(1, 2 * shape_total_points, CV_32FC1, mean_shape_data_106);
            model_mean = mean_shape_data_106;
            regressor_num = REGRESSOR_NUM_106;
            break;
        case P106_WITHOUT_5_POINTS:
//            model_mean = Mat(1, 2 * shape_total_points, CV_32FC1, mean_shape_data_106);
            model_mean = mean_shape_data_106;
            regressor_num = REGRESSOR_NUM_106_FAST;
            break;
        case P68_WITH_5_POINTS:
//            model_mean = Mat(1, 2 * shape_total_points, CV_32FC1, mean_shape_data_68);
            model_mean = mean_shape_data_68;
            regressor_num = REGRESSOR_NUM_68;
            break;
        default:
            return;
    }

	//-------------- Detect the landmarks:
//	Mat current_x = align_mean(model_mean, face_rect);
    float *current_x = (float *)malloc(2*shape_total_points*sizeof(float));
    switch(mode)
    {
        case P68_WITHOUT_5_POINTS:
        case P106_WITHOUT_5_POINTS:
            align_mean(model_mean, current_x, shape_total_points, face_rect);
            break;
        case P68_WITH_5_POINTS:
        case P106_WITH_5_POINTS:
            getInitShape(model_mean, align_points, current_x, shape_total_points, face_rect, mode);
            break;
    }

    //---------------------IMPROVE----------------------//
    /**
    Should be place in init function
    **/
    FeatureExtractor_Init(extract_id, shape_total_points, mode);


    // long sift_time = 0;
    // long pred_time = 0;

	for (size_t r = 0; r < regressor_num; ++r) {

        // long start_time = clock();

        float **observed_value = init_matrix(extract_id[r].size(), FEATURE_DIMENSION);
        FeatureExtractor_Extract(gray_image, observed_value, current_x, image_rows, image_cols, r, mode);

        // long end_time = clock();
        // sift_time += ((end_time - start_time)/1000);

        vector<float> update_step_;
		regressors[r].predict(observed_value, update_step_, r, shape_total_points, mode);

        // pred_time += ((clock()-end_time)/1000);

        auto ied = get_ied(current_x, shape_total_points);
        for(int cnt = 0; cnt < shape_total_points*2; ++cnt)
        {
            update_step_[cnt] *= ied;
            current_x[cnt] -= update_step_[cnt];
        }
        delete_matrix(observed_value);
	}
	for(int i = 0; i < 2*shape_total_points; ++i)
	{
		out_shape[i] = current_x[i];
	}

    free(current_x);
//    LOGE("sift time:%ld, pred time:%ld\n", sift_time, pred_time);
}

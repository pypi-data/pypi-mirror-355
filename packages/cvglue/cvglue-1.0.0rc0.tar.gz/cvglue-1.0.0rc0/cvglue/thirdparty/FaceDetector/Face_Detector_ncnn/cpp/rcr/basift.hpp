/*
* superviseddescent: A C++11 implementation of the supervised descent
*                    optimisation method
* File: rcr/adaptive_vlhog.hpp
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
#pragma once

#ifndef BASIFT_HPP_
#define BASIFT_HPP_

#include "sign_matrix.h"

#include <vector>
#include <string>
#include <cmath>
//#include <define.h>
//#include <arm_neon.h>

#define std_max(a,b) (((a) > (b)) ? (a) : (b))
#define std_min(a,b) (((a) < (b)) ? (a) : (b))

using namespace std;

	class BASiftTransform
	{
		#define BOUND_LIMIT(x,l,h)	( (x)<(l) ? (l) : ((x)>(h) ? (h) : (x)) )
	public:
		BASiftTransform()
        {
		};

        void init_basift(std::vector<std::vector<int>> &calcId, int num_land)
        {
            calc_id = calcId;
            num_landmarks = num_land;
        }

		float get_ied(float *shape, int num_landmark)
		{
			if(num_landmark == 106)
			{
				float right_eye_x = (shape[74] + shape[104])/2;
				float right_eye_y = (shape[74+num_landmark] + shape[104+num_landmark])/2;
				float left_eye_x = (shape[77] + shape[105])/2;
				float left_eye_y = (shape[77+num_landmark] + shape[105+num_landmark])/2;

				float ied = sqrt((left_eye_x - right_eye_x) * (left_eye_x - right_eye_x) + (left_eye_y - right_eye_y) * (left_eye_y - right_eye_y));
				return ied;
			}
			else
			{
				float right_eye_x = (shape[36] + shape[39])/2;
				float right_eye_y = (shape[36+num_landmark] + shape[39+num_landmark])/2;
				float left_eye_x = (shape[42] + shape[45])/2;
				float left_eye_y = (shape[42+num_landmark] + shape[45+num_landmark])/2;

				float ied = sqrt((left_eye_x - right_eye_x) * (left_eye_x - right_eye_x) + (left_eye_y - right_eye_y) * (left_eye_y - right_eye_y));
				return ied;
			}
		}

		void operator()(const unsigned char *gray_image, float **feature, float *parameters, int img_rows, int img_cols, int regressor_level)
		{
            //-------------------------------------------------//
            long sum_time = 0;
            long start_time;
            long end_time;
            //-------------------------------------------------//
			float scale_fator[5] = { 1.0f, 0.7f, 0.4f, 0.25f, 0.12f };
			int max_x = img_cols - 1;
			int max_y = img_rows - 1;

			int plen_half = std::round(scale_fator[regressor_level] * get_ied(parameters, num_landmarks)/2);
			int clen = 16;
			int bklen = 4;
			int blen = 8;

			if (plen_half < 2)
			{
				plen_half = 2;
			}

			unsigned char sift_dir_table[] = { 5, 4, 2, 3, 6, 7, 1, 0 };
			int p;
			for (p = 0; p < calc_id[regressor_level].size(); ++p)
			{
				int i, r, c, n;
                float x = parameters[calc_id[regressor_level][p]];
                float y = parameters[calc_id[regressor_level][p] + num_landmarks];
				int x_floor = floor(x);
				int y_floor = floor(y);
				float x_bias = x - x_floor;
				float y_bias = y - y_floor;
//				cv::Mat_<float> patch(plen_half * 2, plen_half * 2, 0.0f);
				float grad_x[16][16];
				float grad_y[16][16];
				unsigned char binaryDir[256];
                int8_t dir_hist_[8*256] = { 0 };
                int8_t *dir_hist[8];
                dir_hist[0] = dir_hist_;
                for(int bin = 1; bin < 8; ++bin)
                {
                    dir_hist[bin] = dir_hist[bin-1]+256;
                }

//				for (int p_r = 0; p_r < plen_half * 2; ++p_r)
//				{
//					int tpy0 = y_floor - plen_half + p_r;
//					int tpy1 = y_floor + 1 - plen_half + p_r;
//					int tempy0 = BOUND_LIMIT(tpy0, 0, max_y);
//					int tempy1 = BOUND_LIMIT(tpy1, 0, max_y);
//					unsigned char *img_ptr_y0 = gray_image.ptr(tempy0);
//					unsigned char *img_ptr_y1 = gray_image.ptr(tempy1);
//					for (int p_c = 0; p_c < plen_half * 2; ++p_c)
//					{
//						int tpx0 = x_floor - plen_half + p_c;
//						int tpx1 = x_floor + 1 - plen_half + p_c;
//						int tempx0 = BOUND_LIMIT(tpx0, 0, max_x);
//						int tempx1 = BOUND_LIMIT(tpx1, 0, max_x);
//
//						patch[p_r][p_c] = (float)img_ptr_y0[tempx0] * (1 - x_bias)   * (1 - y_bias) \
//										+ (float)img_ptr_y0[tempx1] * x_bias		 * (1 - y_bias) \
//										+ (float)img_ptr_y1[tempx0] * (1 - x_bias)   * y_bias \
//										+ (float)img_ptr_y1[tempx1] * x_bias		 * y_bias;
//					}
//				}
//
//				cv::Size fix_size(16, 16);
//				cv::resize(patch, patch, fix_size);

                vector<vector<float>> patch(clen, vector<float>(clen, 0));
                resize_fpatch(gray_image, patch, x_floor, y_floor, plen_half*2, plen_half*2, clen, clen, max_y+1, max_x+1);

				for (i = 0; i < 16; ++i)
				{
					grad_x[i][0] = patch[i][1] - patch[i][0];
					grad_x[i][15] = patch[i][15] - patch[i][14];
					grad_y[0][i] = patch[1][i] - patch[0][i];
					grad_y[15][i] = patch[15][i] - patch[14][i];
				}
				for (r = 0; r < 16; ++r)
				{
					for (c = 1; c < 15; ++c)
					{
						grad_x[r][c] = patch[r][c + 1] - patch[r][c - 1];
					}
				}
				for (r = 1; r < 15; ++r)
				{
					for (c = 0; c < 16; ++c)
					{
						grad_y[r][c] = patch[r + 1][c] - patch[r - 1][c];
					}
				}

				int tmp_cnt = 0;
				for (c = 0; c < 16; ++c)
				{
					for (r = 0; r < 16; ++r)
					{
						// if equal 0 can get a better performance? or judge 0.5
						binaryDir[tmp_cnt++] = sift_dir_table[((grad_x[r][c] > 0) ? 4 : 0) + ((grad_y[r][c] > 0) ? 2 : 0) + ((fabs(grad_x[r][c]) > fabs(grad_y[r][c])) ? 1 : 0)];
					}
				}

				for (i = 0; i < 256; ++i)
				{
					dir_hist[binaryDir[i]][i] = 1;
					if (binaryDir[i] == 7)
					{
						dir_hist[0][i] = 1;
					}
					else
					{
						dir_hist[binaryDir[i] + 1][i] = 1;
					}
				}

				float norm2_sum = 0;
				// int8_t *p_signM = sign_matrix;
				signed char *p_signM_ = sign_matrix;
				float *p_feat = feature[p];

                start_time = clock();
                for (n = 0; n < 128; ++n)
                {
                   int temp_ = 0;
                    //------------------------------------------------------------------------------------------------------------------//
                   for (i = 0; i < 2048; ++i)
                   {
                       if(dir_hist_[i] != 0)			// p_signM取值：-1或1    dir_hist取值：0或1
                       {
                           temp_ += *p_signM_;
                       }
                       ++p_signM_;
                   }
                    // int16_t temp = 0;
                    // int8x16_t ssum = vdupq_n_s8(0);
                    // for (i = 0; i < 2048; i+=16)
                    // {
                    //     int8x16_t dir_his = vld1q_s8(dir_hist_+i);
                    //     int8x16_t sign_mat = vld1q_s8(p_signM);
                    //     ssum = vmlaq_s8(ssum, dir_his, sign_mat);
                    //     p_signM += 16;
                    // }
                    // int8_t sum[16];
                    // vst1q_s8(sum, ssum);
                    // temp += sum[0] + sum[1] + sum[2] + sum[3] + sum[4] + sum[5] + sum[6] + sum[7]\
                    //       + sum[8] + sum[9] + sum[10] + sum[11] + sum[12] + sum[13] + sum[14] + sum[15];
                    //------------------------------------------------------------------------------------------------------------------//
                    *p_feat = temp_;
                    ++p_feat;
                    norm2_sum += temp_ * temp_;
                }
                end_time = clock();
                sum_time += end_time - start_time;


				norm2_sum = sqrt(norm2_sum);

				float eps = 0.0000001;
				p_feat = feature[p];
				for (n = 0; n < 128; ++n)
				{
					p_feat[0] = p_feat[0] / (norm2_sum + eps) - sift_bias[n];
					++p_feat;
				}
			}
//            LOGE("make feature time:%ldms\n", (sum_time)/1000);

//            cv::Mat features;
//            for(p = 0; p < calc_id[regressor_level].size(); ++p)
//            {
//                cv::Mat feat(1, 128, CV_32FC1, feature[p]);
//                features.push_back(feat);
//            }
//
//            features = features.reshape(0, features.cols * calc_id[regressor_level].size()).t();
//
//            cv::Mat bias = cv::Mat::ones(1, 1, CV_32FC1);
//            cv::hconcat(features, bias, features);
//            return features;
	    };

        void resize_fpatch(const unsigned char *in_img, vector<vector<float>> &out_img, int x_floor, int y_floor, int in_rows, int in_cols, int out_rows, int out_cols, int img_rows, int img_cols)
        {
            long r;
            int max_x = img_cols-1;
            int max_y = img_rows-1;
            int plen_half = in_rows/2;
            int tpx0 = x_floor - plen_half;
            int tpy0 = y_floor - plen_half;
            int tempx0 = BOUND_LIMIT(tpx0, 0, max_x);
            int tempy0 = BOUND_LIMIT(tpy0, 0, max_y);
            const double x_scale = (in_cols - 1) / (double)std_max((out_cols - 1), 1l);
            const double y_scale = (in_rows - 1) / (double)std_max((out_rows - 1), 1l);
            double y = -y_scale;

            for (r = 0; r < out_rows; ++r)
            {
                long c = 0;
                y += y_scale;
                long top = (long)(floor(y));
                long bottom = std_min(top + 1, in_rows - 1);
                double tb_frac = y - top;
                double x = -x_scale;

                top += tempy0;
                bottom += tempy0;

                top = BOUND_LIMIT(top, 0, max_y);
                bottom = BOUND_LIMIT(bottom, 0, max_y);

                for (; c < out_cols; ++c)
                {
                    x += x_scale;
                    long left = (long)(floor(x));
                    long right = std_min(left + 1, in_cols - 1);
                    double lr_frac = x - left;

                    left += tempx0;
                    right += tempx0;

                    left = BOUND_LIMIT(left, 0, max_x);
                    right = BOUND_LIMIT(right, 0, max_x);

                    float tl, tr, bl, br;
                    float inter_value;

                    tl = in_img[top*img_cols + left];
                    tr = in_img[top*img_cols + right];
                    bl = in_img[bottom*img_cols + left];
                    br = in_img[bottom*img_cols + right];

                    inter_value = 0;

                    inter_value = (float)((1 - tb_frac)*((1 - lr_frac)*(double)tl + lr_frac*(double)tr) \
                    + tb_frac*((1 - lr_frac)*(double)bl + lr_frac*(double)br));

                    out_img[r][c] = inter_value;
                }
            }
        }

	private:
		std::vector<std::vector<int>> calc_id;
        int num_landmarks;
	};


#endif


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

#ifndef DSIFT_HPP_
#define DSIFT_HPP_

#include <string.h>
#include <vector>
//#include <define.h>
#include <cmath>
#include <malloc.h>

#define std_max(a,b) (((a) > (b)) ? (a) : (b))
#define std_min(a,b) (((a) < (b)) ? (a) : (b))

#define CV_2PI 6.283185307179586476925286766559

using namespace std;

	class DenseSiftTransform
	{
		#define BOUND_LIMIT(x,l,h)	( (x)<(l) ? (l) : ((x)>(h) ? (h) : (x)) )
	public:
        DenseSiftTransform(){};
		void init_dsift(std::vector<std::vector<int>> &calcId, int num_land)
		{
            calc_id = calcId;
            num_landmarks = num_land;
			//----------------------------------------------back up--------------------------------------------------------------//
			static float kerl_1[19*19] = { 0.0001, 0.0002, 0.0003, 0.0004, 0.0005, 0.0006, 0.0007, 0.0008, 0.0009, 0.0010, 0.0009, 0.0008, 0.0007, 0.0006, 0.0005, 0.0004, 0.0003, 0.0002, 0.0001\
			, 0.0002, 0.0004, 0.0006, 0.0008, 0.0010, 0.0012, 0.0014, 0.0016, 0.0018, 0.0020, 0.0018, 0.0016, 0.0014, 0.0012, 0.0010, 0.0008, 0.0006, 0.0004, 0.0002\
			, 0.0003, 0.0006, 0.0009, 0.0012, 0.0015, 0.0018, 0.0021, 0.0024, 0.0027, 0.0030, 0.0027, 0.0024, 0.0021, 0.0018, 0.0015, 0.0012, 0.0009, 0.0006, 0.0003\
			, 0.0004, 0.0008, 0.0012, 0.0016, 0.0020, 0.0024, 0.0028, 0.0032, 0.0036, 0.0040, 0.0036, 0.0032, 0.0028, 0.0024, 0.0020, 0.0016, 0.0012, 0.0008, 0.0004\
			, 0.0005, 0.0010, 0.0015, 0.0020, 0.0025, 0.0030, 0.0035, 0.0040, 0.0045, 0.0050, 0.0045, 0.0040, 0.0035, 0.0030, 0.0025, 0.0020, 0.0015, 0.0010, 0.0005\
			, 0.0006, 0.0012, 0.0018, 0.0024, 0.0030, 0.0036, 0.0042, 0.0048, 0.0054, 0.0060, 0.0054, 0.0048, 0.0042, 0.0036, 0.0030, 0.0024, 0.0018, 0.0012, 0.0006\
			, 0.0007, 0.0014, 0.0021, 0.0028, 0.0035, 0.0042, 0.0049, 0.0056, 0.0063, 0.0070, 0.0063, 0.0056, 0.0049, 0.0042, 0.0035, 0.0028, 0.0021, 0.0014, 0.0007\
			, 0.0008, 0.0016, 0.0024, 0.0032, 0.0040, 0.0048, 0.0056, 0.0064, 0.0072, 0.0080, 0.0072, 0.0064, 0.0056, 0.0048, 0.0040, 0.0032, 0.0024, 0.0016, 0.0008\
			, 0.0009, 0.0018, 0.0027, 0.0036, 0.0045, 0.0054, 0.0063, 0.0072, 0.0081, 0.0090, 0.0081, 0.0072, 0.0063, 0.0054, 0.0045, 0.0036, 0.0027, 0.0018, 0.0009\
			, 0.0010, 0.0020, 0.0030, 0.0040, 0.0050, 0.0060, 0.0070, 0.0080, 0.0090, 0.0100, 0.0090, 0.0080, 0.0070, 0.0060, 0.0050, 0.0040, 0.0030, 0.0020, 0.0010\
			, 0.0009, 0.0018, 0.0027, 0.0036, 0.0045, 0.0054, 0.0063, 0.0072, 0.0081, 0.0090, 0.0081, 0.0072, 0.0063, 0.0054, 0.0045, 0.0036, 0.0027, 0.0018, 0.0009\
			, 0.0008, 0.0016, 0.0024, 0.0032, 0.0040, 0.0048, 0.0056, 0.0064, 0.0072, 0.0080, 0.0072, 0.0064, 0.0056, 0.0048, 0.0040, 0.0032, 0.0024, 0.0016, 0.0008\
			, 0.0007, 0.0014, 0.0021, 0.0028, 0.0035, 0.0042, 0.0049, 0.0056, 0.0063, 0.0070, 0.0063, 0.0056, 0.0049, 0.0042, 0.0035, 0.0028, 0.0021, 0.0014, 0.0007\
			, 0.0006, 0.0012, 0.0018, 0.0024, 0.0030, 0.0036, 0.0042, 0.0048, 0.0054, 0.0060, 0.0054, 0.0048, 0.0042, 0.0036, 0.0030, 0.0024, 0.0018, 0.0012, 0.0006\
			, 0.0005, 0.0010, 0.0015, 0.0020, 0.0025, 0.0030, 0.0035, 0.0040, 0.0045, 0.0050, 0.0045, 0.0040, 0.0035, 0.0030, 0.0025, 0.0020, 0.0015, 0.0010, 0.0005\
			, 0.0004, 0.0008, 0.0012, 0.0016, 0.0020, 0.0024, 0.0028, 0.0032, 0.0036, 0.0040, 0.0036, 0.0032, 0.0028, 0.0024, 0.0020, 0.0016, 0.0012, 0.0008, 0.0004\
			, 0.0003, 0.0006, 0.0009, 0.0012, 0.0015, 0.0018, 0.0021, 0.0024, 0.0027, 0.0030, 0.0027, 0.0024, 0.0021, 0.0018, 0.0015, 0.0012, 0.0009, 0.0006, 0.0003\
			, 0.0002, 0.0004, 0.0006, 0.0008, 0.0010, 0.0012, 0.0014, 0.0016, 0.0018, 0.0020, 0.0018, 0.0016, 0.0014, 0.0012, 0.0010, 0.0008, 0.0006, 0.0004, 0.0002\
			, 0.0001, 0.0002, 0.0003, 0.0004, 0.0005, 0.0006, 0.0007, 0.0008, 0.0009, 0.0010, 0.0009, 0.0008, 0.0007, 0.0006, 0.0005, 0.0004, 0.0003, 0.0002, 0.0001 };

            static float kerl_2[15*15] = { 0.0002, 0.0005, 0.0007, 0.0010, 0.0012, 0.0015, 0.0017, 0.0020, 0.0017, 0.0015, 0.0012, 0.0010, 0.0007, 0.0005, 0.0002\
			, 0.0005, 0.0010, 0.0015, 0.0020, 0.0024, 0.0029, 0.0034, 0.0039, 0.0034, 0.0029, 0.0024, 0.0020, 0.0015, 0.0010, 0.0005\
			, 0.0007, 0.0015, 0.0022, 0.0029, 0.0037, 0.0044, 0.0051, 0.0059, 0.0051, 0.0044, 0.0037, 0.0029, 0.0022, 0.0015, 0.0007\
			, 0.0010, 0.0020, 0.0029, 0.0039, 0.0049, 0.0059, 0.0068, 0.0078, 0.0068, 0.0059, 0.0049, 0.0039, 0.0029, 0.0020, 0.0010\
			, 0.0012, 0.0024, 0.0037, 0.0049, 0.0061, 0.0073, 0.0085, 0.0098, 0.0085, 0.0073, 0.0061, 0.0049, 0.0037, 0.0024, 0.0012\
			, 0.0015, 0.0029, 0.0044, 0.0059, 0.0073, 0.0088, 0.0103, 0.0117, 0.0103, 0.0088, 0.0073, 0.0059, 0.0044, 0.0029, 0.0015\
			, 0.0017, 0.0034, 0.0051, 0.0068, 0.0085, 0.0103, 0.0120, 0.0137, 0.0120, 0.0103, 0.0085, 0.0068, 0.0051, 0.0034, 0.0017\
			, 0.0020, 0.0039, 0.0059, 0.0078, 0.0098, 0.0117, 0.0137, 0.0156, 0.0137, 0.0117, 0.0098, 0.0078, 0.0059, 0.0039, 0.0020\
			, 0.0017, 0.0034, 0.0051, 0.0068, 0.0085, 0.0103, 0.0120, 0.0137, 0.0120, 0.0103, 0.0085, 0.0068, 0.0051, 0.0034, 0.0017\
			, 0.0015, 0.0029, 0.0044, 0.0059, 0.0073, 0.0088, 0.0103, 0.0117, 0.0103, 0.0088, 0.0073, 0.0059, 0.0044, 0.0029, 0.0015\
			, 0.0012, 0.0024, 0.0037, 0.0049, 0.0061, 0.0073, 0.0085, 0.0098, 0.0085, 0.0073, 0.0061, 0.0049, 0.0037, 0.0024, 0.0012\
			, 0.0010, 0.0020, 0.0029, 0.0039, 0.0049, 0.0059, 0.0068, 0.0078, 0.0068, 0.0059, 0.0049, 0.0039, 0.0029, 0.0020, 0.0010\
			, 0.0007, 0.0015, 0.0022, 0.0029, 0.0037, 0.0044, 0.0051, 0.0059, 0.0051, 0.0044, 0.0037, 0.0029, 0.0022, 0.0015, 0.0007\
			, 0.0005, 0.0010, 0.0015, 0.0020, 0.0024, 0.0029, 0.0034, 0.0039, 0.0034, 0.0029, 0.0024, 0.0020, 0.0015, 0.0010, 0.0005\
			, 0.0002, 0.0005, 0.0007, 0.0010, 0.0012, 0.0015, 0.0017, 0.0020, 0.0017, 0.0015, 0.0012, 0.0010, 0.0007, 0.0005, 0.0002 };

            static float kerl_3[11*11] = { 0.0008, 0.0015, 0.0023, 0.0031, 0.0039, 0.0046, 0.0039, 0.0031, 0.0023, 0.0015, 0.0008\
			, 0.0015, 0.0031, 0.0046, 0.0062, 0.0077, 0.0093, 0.0077, 0.0062, 0.0046, 0.0031, 0.0015\
			, 0.0023, 0.0046, 0.0069, 0.0093, 0.0116, 0.0139, 0.0116, 0.0093, 0.0069, 0.0046, 0.0023\
			, 0.0031, 0.0062, 0.0093, 0.0123, 0.0154, 0.0185, 0.0154, 0.0123, 0.0093, 0.0062, 0.0031\
			, 0.0039, 0.0077, 0.0116, 0.0154, 0.0193, 0.0231, 0.0193, 0.0154, 0.0116, 0.0077, 0.0039\
			, 0.0046, 0.0093, 0.0139, 0.0185, 0.0231, 0.0278, 0.0231, 0.0185, 0.0139, 0.0093, 0.0046\
			, 0.0039, 0.0077, 0.0116, 0.0154, 0.0193, 0.0231, 0.0193, 0.0154, 0.0116, 0.0077, 0.0039\
			, 0.0031, 0.0062, 0.0093, 0.0123, 0.0154, 0.0185, 0.0154, 0.0123, 0.0093, 0.0062, 0.0031\
			, 0.0023, 0.0046, 0.0069, 0.0093, 0.0116, 0.0139, 0.0116, 0.0093, 0.0069, 0.0046, 0.0023\
			, 0.0015, 0.0031, 0.0046, 0.0062, 0.0077, 0.0093, 0.0077, 0.0062, 0.0046, 0.0031, 0.0015\
			, 0.0008, 0.0015, 0.0023, 0.0031, 0.0039, 0.0046, 0.0039, 0.0031, 0.0023, 0.0015, 0.0008 };

            static float kerl_4[7*7] = { 0.0039, 0.0078, 0.0117, 0.0156, 0.0117, 0.0078, 0.0039\
			, 0.0078, 0.0156, 0.0234, 0.0313, 0.0234, 0.0156, 0.0078\
			, 0.0117, 0.0234, 0.0352, 0.0469, 0.0352, 0.0234, 0.0117\
			, 0.0156, 0.0313, 0.0469, 0.0625, 0.0469, 0.0313, 0.0156\
			, 0.0117, 0.0234, 0.0352, 0.0469, 0.0352, 0.0234, 0.0117\
			, 0.0078, 0.0156, 0.0234, 0.0313, 0.0234, 0.0156, 0.0078\
			, 0.0039, 0.0078, 0.0117, 0.0156, 0.0117, 0.0078, 0.0039 };

            static float kerl_5[3*3] = { 0.0625, 0.1250, 0.0625\
			, 0.1250, 0.2500, 0.1250\
			, 0.0625, 0.1250, 0.0625 };

            static float scale_fator_[5] = { 1.0f, 0.7f, 0.4f, 0.25f, 0.12f };
            static int cell_num_[5] = { 40, 32, 24, 16, 8 };

			static float weight[4*4] = { 8.8688, 11.2159, 11.2159, 8.8688\
			, 11.2159, 14.1842, 14.1842, 11.2159\
			, 11.2159, 14.1842, 14.1842, 11.2159\
			, 8.8688, 11.2159, 11.2159, 8.8688 };

//		float *kerl[5] = { kerl_1[0], kerl_2[0], kerl_3[0], kerl_4[0], kerl_5[0] };
        switch(num_landmarks)
        {
            case 68:
                kerl[0] = kerl_1;
                kerl[1] = kerl_2;
                kerl[2] = kerl_3;
                kerl[3] = kerl_4;
                kerl[4] = kerl_5;
                for(int i = 0; i < 5; ++i)
                {
                    scale_fator[i] = scale_fator_[i];
                    cell_num[i] = cell_num_[i];
                }
                break;
            case 106:
                kerl[0] = kerl_2;
                kerl[1] = kerl_4;
                scale_fator[0] = scale_fator_[1];
                scale_fator[1] = scale_fator_[2];
                cell_num[0] = cell_num_[1];
                cell_num[1] = cell_num_[3];
                break;
        }
		weights = weight;
		};

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

		void operator()(const unsigned char *gray_image, float **feature, float *parameters, int img_rows, int img_cols, size_t regressor_level)
		{
            //-------------------------------------------------//
            long sum_time = 0;
            long start_time;
            long end_time;
            //-------------------------------------------------//

			//try {
            int max_x = img_cols - 1;
            int max_y = img_rows - 1;

			// patch length. The formula can use Zhenhua
            int plen_half = (int)round(scale_fator[regressor_level] * get_ied(parameters, num_landmarks)/2);

            const int clen = cell_num[regressor_level];
			const int bklen = 4;
            const int cklen = clen / bklen;
            const int blen = 8;
            const int flen = bklen*bklen*blen;

			if (plen_half < 2)
			{
				plen_half = 2;
			}

			//Mat features(calc_id[regressor_level].size(), bklen*bklen*blen, CV_32FC1);
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
                vector<vector<float>> grad_x(clen, vector<float>(clen, 0));
                vector<vector<float>> grad_y(clen, vector<float>(clen, 0));
                vector<vector<float>> dir_hist(blen, vector<float>(clen*clen, 0));

                vector<vector<float>> patch(clen, vector<float>(clen, 0));
				resize_fpatch(gray_image, patch, x_floor, y_floor, plen_half*2, plen_half*2, clen, clen, max_y+1, max_x+1);

				for (i = 0; i < clen; ++i)
				{
					grad_x[i][0] = patch[i][1] - patch[i][0];
					grad_x[i][clen-1] = patch[i][clen-1] - patch[i][clen-2];
					grad_y[0][i] = patch[1][i] - patch[0][i];
					grad_y[clen-1][i] = patch[clen-1][i] - patch[clen-2][i];
				}
				for (r = 0; r < clen; ++r)
				{
					for (c = 1; c < clen-1; ++c)
					{
						grad_x[r][c] = patch[r][c + 1] - patch[r][c - 1];
					}
				}
				for (r = 1; r < clen-1; ++r)
				{
					for (c = 0; c < clen; ++c)
					{
						grad_y[r][c] = patch[r + 1][c] - patch[r - 1][c];
					}
				}

                int tmp_cnt = 0;
				for (c = 0; c < clen; ++c)
				{
					for (r = 0; r < clen; ++r)
					{
						float angle = atan2(grad_y[r][c], grad_x[r][c]);
						float amplitude = sqrt(grad_x[r][c] * grad_x[r][c] + grad_y[r][c] * grad_y[r][c]);
						if (angle < 0.0f)
						{
							angle += CV_2PI;
						}
						float bin = angle * blen / CV_2PI;
						float bin_res = bin - floor(bin);
						unsigned char rest_bin = (((unsigned char)floor(bin)) >= blen) ? 0 : ((unsigned char)floor(bin));
						unsigned char next_bin = (rest_bin >= blen-1) ? 0 : rest_bin + 1;
						dir_hist[next_bin][tmp_cnt] = amplitude*bin_res;
                        dir_hist[rest_bin][tmp_cnt] = amplitude - dir_hist[next_bin][tmp_cnt];
						++tmp_cnt;
					}
				}

				int cnt = 0;
				for (int b = 0; b < blen; ++b)
				{
                    int padded = cklen/2;
                    int bord_rows = clen + padded + padded+1;
                    int bord_cols = clen + padded + padded+1;
                    float *bordHist = (float *)malloc((size_t)(bord_rows*bord_cols*sizeof(float)));
					float *feature_pointer = feature[p] + b*bklen*bklen;
                    memset(bordHist, 0, bord_rows*bord_cols*sizeof(float));
                    makeBorder((float *)dir_hist[b].data(), bordHist, clen, clen, padded, padded+1, padded, padded+1, 0);
                    start_time = clock();
					for (int by = 0; by < bklen; ++by)
					{
						for (int bx = 0; bx < bklen; ++bx)
						{
                            float sum_ = 0;
                            int cnt_ = 0;
                            for(int r_ = by * cklen + 1; r_ < by * cklen + 2*cklen; ++r_)
                            {
                                for(int c_ = bx * cklen + 1; c_ < bx * cklen + 2*cklen; ++c_)
                                {
                                    sum_ += kerl[regressor_level][cnt_] * bordHist[r_*bord_cols + c_];
                                    ++cnt_;
                                }
                            }
                            feature_pointer[by*bklen+bx] = sum_ * weights[by*bklen+bx];
						}
					}
                    end_time = clock();
                    sum_time += end_time - start_time;
                    free(bordHist);
				}

                float norm2_sum = 0;
                for(n = 0; n < flen; ++n)
                {
                    norm2_sum += feature[p][n] * feature[p][n];
                }
                norm2_sum = sqrt(norm2_sum);

				float eps = 0.0000001;
				for (n = 0; n < flen; ++n)
				{
                    feature[p][n] /= (norm2_sum + eps);
				}
			}

//            LOGE("make feature time:%ldms\n", (sum_time)/1000);
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

        void makeBorder(const float *in_img, float *out_img, int img_rows, int img_cols, int left, int right, int top, int bottom, char method)
        {
            int out_cols = left + right + img_cols;
            for (int r = top; r < img_rows+top; ++r)
            {
                for(int c = left; c < img_cols+left; ++c)
                {
                    out_img[r*out_cols+c] = in_img[(r-top)*img_cols+c-left];
                }
            }
        }

	private:
        float *kerl[5];
		float *weights;
        float scale_fator[5];
        int cell_num[5];

		std::vector<std::vector<int>> calc_id;
        int num_landmarks;
	};

#endif


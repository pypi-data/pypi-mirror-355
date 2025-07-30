//
// Created by lee on 2017/7/19.
//

#include "regressors.hpp"
// #include <arm_neon.h>

//public:
/**
 * Creates a LinearRegressor with no regularisation.
 *
 * @param[in] regulariser A Regulariser to regularise the data matrix. Default means no regularisation.
 */
//LinearRegressor() : x(), x_reg(), r_bias()
//{
//};

namespace superviseddescent
{
    void LinearRegressor::gemm_neon(const float *lhs, const float *rhs, float *out_mat, int rhs_rows, int rhs_cols)
    {
        for (int j = 0; j < rhs_rows; ++j)
        {
            float *data1 = (float*)lhs;
            float *data2 = (float*)(rhs + j*rhs_cols);
            int i = 0;
            // float32x4_t production = vdupq_n_f32(0.f);
            // for (i = 0; i < rhs_cols-3; i+=4)
            // {
            //     float32x4_t lfactor = vld1q_f32(data1);
            //     float32x4_t rfactor = vld1q_f32(data2);
            //     data1 += 4; data2 += 4;
            //     production = vmlaq_f32(production, lfactor, rfactor);
            // }
            float sum = 0.0f;
            for (;  i< rhs_cols; ++i)
            {
                sum += (*data1)*(*data2);
                data1++; data2++;
            }
            // float temp[4];
            // vst1q_f32(temp, production);
            // sum += (temp[0]+temp[1]+temp[2]+temp[3]);

            out_mat[j] = sum;
        }
    }

    void LinearRegressor::predict(float **value, std::vector<float> &output, size_t regressor_level, int shape_total_point, ModeSelect mode)
    {
        int global_regressor_num = 0;
        switch(mode)
        {
            case P68_WITH_5_POINTS:
                global_regressor_num = GLOBAL_REGRESSOR_NUM_68;
                break;
            case P106_WITH_5_POINTS:
                global_regressor_num = GLOBAL_REGRESSOR_NUM_106;
                break;
            case P106_WITHOUT_5_POINTS:
                global_regressor_num = GLOBAL_REGRESSOR_NUM_106_FAST;
                break;
        }
        if (regressor_level >= 0 && regressor_level <= global_regressor_num-1)
        {
            output.clear();
            output.resize(size_t(this->x_rows));
            gemm_neon(value[0], this->x, output.data(), this->x_rows, this->x_cols);
        }
        else if (regressor_level >= global_regressor_num && regressor_level <= 4 && shape_total_point == 106)
        {
            const int data_dim = FEATURE_DIMENSION;
            // jaw
            float* rtn_1 = (float*)(calloc(size_t(this->x_reg_rows[0]), sizeof(float)));
            gemm_neon(value[0], this->x_reg[0], rtn_1, this->x_reg_rows[0], this->x_reg_cols[0]);

            // right eye
            std::vector<float> data_reg2((this->r_bias[2]-this->r_bias[1]+this->r_bias[5]-this->r_bias[4]+this->r_bias[7]-this->r_bias[6]+this->r_bias[9]-this->r_bias[8])*data_dim);
            data_reg2.insert(data_reg2.begin(), value[this->r_bias[1]], value[this->r_bias[2]]);
            data_reg2.insert(data_reg2.end(), value[this->r_bias[4]], value[this->r_bias[5]]);
            data_reg2.insert(data_reg2.end(), value[this->r_bias[6]], value[this->r_bias[7]]);
            data_reg2.insert(data_reg2.end(), value[this->r_bias[8]], value[this->r_bias[9]]);
            float* rtn_2 = (float*)(calloc(size_t(this->x_reg_rows[1]), sizeof(float)));
            gemm_neon(data_reg2.data(), this->x_reg[1], rtn_2, this->x_reg_rows[1], this->x_reg_cols[1]);
            data_reg2.clear();

            // left eye
            std::vector<float> data_reg3((this->r_bias[3]-this->r_bias[2]+this->r_bias[6]-this->r_bias[5]+this->r_bias[8]-this->r_bias[7]+this->r_bias[10]-this->r_bias[9])*data_dim);
            data_reg3.insert(data_reg3.begin(), value[this->r_bias[2]], value[this->r_bias[3]]);
            data_reg3.insert(data_reg3.end(), value[this->r_bias[5]], value[this->r_bias[6]]);
            data_reg3.insert(data_reg3.end(), value[this->r_bias[7]], value[this->r_bias[8]]);
            data_reg3.insert(data_reg3.end(), value[this->r_bias[9]], value[this->r_bias[10]]);
            float* rtn_3 = (float*)(calloc(size_t(this->x_reg_rows[2]), sizeof(float)));
            gemm_neon(data_reg3.data(), (float *)this->x_reg[2], rtn_3, this->x_reg_rows[2], this->x_reg_cols[2]);
            data_reg3.clear();

            // nose
            std::vector<float> data_reg4;
            if(this->r_bias[11] - this->r_bias[10] > 0)
            {
                data_reg4.reserve((this->r_bias[4]-this->r_bias[3]+this->r_bias[11]-this->r_bias[10])*data_dim);
                data_reg4.insert(data_reg4.begin(), value[this->r_bias[3]], value[this->r_bias[4]]);
                data_reg4.insert(data_reg4.end(), value[this->r_bias[10]], value[this->r_bias[11]]);
            }
            else
            {
                data_reg4.reserve((this->r_bias[4]-this->r_bias[3])*data_dim);
                data_reg4.insert(data_reg4.begin(), value[this->r_bias[3]], value[this->r_bias[4]]);
            }
            float* rtn_4 = (float*)(calloc(size_t(this->x_reg_rows[3]), sizeof(float)));
            gemm_neon(data_reg4.data(), this->x_reg[3], rtn_4, this->x_reg_rows[3], this->x_reg_cols[3]);
            data_reg4.clear();

            // mouth
            float* rtn_5 = (float*)(calloc(size_t(this->x_reg_rows[4]), sizeof(float)));
            gemm_neon(value[this->r_bias[11]], this->x_reg[4], rtn_5, this->x_reg_rows[4], this->x_reg_cols[4]);

            const int pm1 = 33;
            const int pm2 = 17;
            const int pm3 = 17;
            const int pm4 = 15;
            const int pm5 = 20;

            output.clear();
            output.reserve(shape_total_point*2);
            output.insert(output.begin(), rtn_1, rtn_1+33);
            output.insert(output.end(), rtn_2, rtn_2+5);
            output.insert(output.end(), rtn_3, rtn_3+5);
            output.insert(output.end(), rtn_4, rtn_4+9);
            output.insert(output.end(), rtn_2+5, rtn_2+11);
            output.insert(output.end(), rtn_3+5, rtn_3+11);
            output.insert(output.end(), rtn_2+11, rtn_2+14);
            output.insert(output.end(), rtn_2[4]);		// eyebow merge point
            output.insert(output.end(), rtn_3[0]);		// eyebow merge point
            output.insert(output.end(), rtn_3+11, rtn_3+14);
            output.insert(output.end(), rtn_2+14, rtn_2+17);
            output.insert(output.end(), rtn_3+14, rtn_3+17);
            output.insert(output.end(), rtn_4+9, rtn_4+15);
            output.insert(output.end(), rtn_5, rtn_5+20);
            output.insert(output.end(), rtn_2[16]);		// pupil merge point
            output.insert(output.end(), rtn_3[16]);		// pupil merge point

            output.insert(output.end(), rtn_1+pm1, rtn_1+pm1+33);
            output.insert(output.end(), rtn_2+pm2, rtn_2+pm2+5);
            output.insert(output.end(), rtn_3+pm3, rtn_3+pm3+5);
            output.insert(output.end(), rtn_4+pm4, rtn_4+pm4+9);
            output.insert(output.end(), rtn_2+pm2+5, rtn_2+pm2+11);
            output.insert(output.end(), rtn_3+pm3+5, rtn_3+pm3+11);
            output.insert(output.end(), rtn_2+pm2+11, rtn_2+pm2+14);
            output.insert(output.end(), rtn_2[4+pm2]);		// eyebow merge point
            output.insert(output.end(), rtn_3[0+pm3]);		// eyebow merge point
            output.insert(output.end(), rtn_3+pm3+11, rtn_3+pm3+14);
            output.insert(output.end(), rtn_2+pm2+14, rtn_2+pm2+17);
            output.insert(output.end(), rtn_3+pm3+14, rtn_3+pm3+17);
            output.insert(output.end(), rtn_4+pm4+9, rtn_4+pm4+15);
            output.insert(output.end(), rtn_5+pm5, rtn_5+pm5+20);
            output.insert(output.end(), rtn_2[16+pm2]);		// pupil merge point
            output.insert(output.end(), rtn_3[16+pm3]);		// pupil merge point

            free(rtn_1);
            free(rtn_2);
            free(rtn_3);
            free(rtn_4);
            free(rtn_5);
        }
        else if(regressor_level >= global_regressor_num && regressor_level <= 4 && shape_total_point == 68)
        {
            const int data_dim = FEATURE_DIMENSION;

            // jaw
            float* rtn_1 = (float*)(calloc(size_t(this->x_reg_rows[0]), sizeof(float)));
            gemm_neon(value[0], this->x_reg[0], rtn_1, this->x_reg_rows[0], this->x_reg_cols[0]);


            // right eye
            std::vector<float> data_reg2((this->r_bias[2]-this->r_bias[1]+this->r_bias[5]-this->r_bias[4])*data_dim);
            data_reg2.insert(data_reg2.begin(), value[this->r_bias[1]], value[this->r_bias[2]]);
            data_reg2.insert(data_reg2.end(), value[this->r_bias[4]], value[this->r_bias[5]]);
            float* rtn_2 = (float*)(calloc(size_t(this->x_reg_rows[1]), sizeof(float)));
            gemm_neon(data_reg2.data(), this->x_reg[1], rtn_2, this->x_reg_rows[1], this->x_reg_cols[1]);
            data_reg2.clear();


            // left eye
            std::vector<float> data_reg3((this->r_bias[3]-this->r_bias[2]+this->r_bias[6]-this->r_bias[5])*data_dim);
            data_reg3.insert(data_reg3.begin(), value[this->r_bias[2]], value[this->r_bias[3]]);
            data_reg3.insert(data_reg3.end(), value[this->r_bias[5]], value[this->r_bias[6]]);
            float* rtn_3 = (float*)(calloc(size_t(this->x_reg_rows[2]), sizeof(float)));
            gemm_neon(data_reg3.data(), this->x_reg[2], rtn_3, this->x_reg_rows[2], this->x_reg_cols[2]);
            data_reg3.clear();


            // nose
            std::vector<float> data_reg4((this->r_bias[4]-this->r_bias[3])*data_dim);
            data_reg4.insert(data_reg4.begin(), value[this->r_bias[3]], value[this->r_bias[4]]);
            float* rtn_4 = (float*)(calloc(size_t(this->x_reg_rows[3]), sizeof(float)));
            gemm_neon(data_reg4.data(), this->x_reg[3], rtn_4, this->x_reg_rows[3], this->x_reg_cols[3]);
            data_reg4.clear();


            // mouth
            float* rtn_5 = (float*)(calloc(size_t(this->x_reg_rows[4]), sizeof(float)));
            gemm_neon(value[this->r_bias[6]], this->x_reg[4], rtn_5, this->x_reg_rows[4], this->x_reg_cols[4]);


            const int pm1 = 17;
            const int pm2 = 11;
            const int pm3 = 11;
            const int pm4 = 9;
            const int pm5 = 20;

            output.clear();
            output.reserve(shape_total_point*2);
            output.insert(output.begin(), rtn_1, rtn_1+17);
            output.insert(output.end(), rtn_2, rtn_2+5);
            output.insert(output.end(), rtn_3, rtn_3+5);
            output.insert(output.end(), rtn_4, rtn_4+9);
            output.insert(output.end(), rtn_2+5, rtn_2+11);
            output.insert(output.end(), rtn_3+5, rtn_3+11);
            output.insert(output.end(), rtn_5, rtn_5+20);

            output.insert(output.end(), rtn_1+pm1, rtn_1+pm1+17);
            output.insert(output.end(), rtn_2+pm2, rtn_2+pm2+5);
            output.insert(output.end(), rtn_3+pm3, rtn_3+pm3+5);
            output.insert(output.end(), rtn_4+pm4, rtn_4+pm4+9);
            output.insert(output.end(), rtn_2+pm2+5, rtn_2+pm2+11);
            output.insert(output.end(), rtn_3+pm3+5, rtn_3+pm3+11);
            output.insert(output.end(), rtn_5+pm5, rtn_5+pm5+20);

            free(rtn_1);
            free(rtn_2);
            free(rtn_3);
            free(rtn_4);
            free(rtn_5);
        }
    }
}

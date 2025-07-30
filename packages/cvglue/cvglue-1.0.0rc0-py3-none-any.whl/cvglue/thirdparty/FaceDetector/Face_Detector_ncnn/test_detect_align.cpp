#include <opencv2/highgui/highgui.hpp>
#include <opencv2/opencv.hpp>
// #include <mtcnn.h>
#include "FaceDetector.h"
#include <rcr-detect.hpp>
#include <iostream>
#include <fstream>
#include <string>
#include <stdio.h>
#include <memory.h>

#define LANDMARKS_NUM   106
#define MAXFACENUM      5

static int model_flag = 0;
static ModeSelect mode_sel = P106_WITH_5_POINTS;

// setup
static float points[2*LANDMARKS_NUM*MAXFACENUM];
static float result[MAXFACENUM*15];

cv::Mat EstimateHeadPose(const float *curr_shape);

int main(int argc, char **argv)
{
        if(argc < 3)
        {
            return 0;
        }
        
        std::ifstream fin(argv[1]);
        
        int cnt = 0;
        std::string param = "../model/face.param";
        std::string bin = "../model/face.bin";
        const int max_side = 320;
        Detector detector(param, bin, false);
        
        while(1)
        {
            std::string line;
            fin >> line;
            cv::Mat img = cv::imread(line);
            if(img.empty())
            {
                printf("Empty image input\n");
                break;
            }
            printf("img size:%d, %d\n", img.rows, img.cols);
            std::cout<<cnt<<" "<<line<<std::endl;

            float long_side = std::max(img.cols, img.rows);
            float scale = max_side/long_side;
            cv::Mat img_scale;
            cv::resize(img, img_scale, cv::Size(img.cols*scale, img.rows*scale));
            
            cv::Mat src;
            cv::cvtColor(img, src, cv::COLOR_RGB2RGBA);
            if(src.channels() != 4)
            {
                return 0;
            }

            int width = src.cols;
            int height = src.rows;
            unsigned char *src_data = new unsigned char[4*width*height];
            for(int j = 0; j < height; j++)
            {
                unsigned char *p = src.ptr(j);
                memcpy(src_data+4*j*width, p, 4*width*sizeof(unsigned char));
            }

            int face_num = 0;
            std::vector<bbox> boxes;
            long start_time_ = clock();

            // slim or RFB
            detector.Detect(img_scale, boxes);

            // Occur after hundreds of times
            /*
            *** Error in `./detect_align_cnn': double free or corruption (fasttop): 0x0000000005a3db00 ***
            ======= Backtrace: =========
            /lib/x86_64-linux-gnu/libc.so.6(+0x777e5)[0x7f363aede7e5]
            /lib/x86_64-linux-gnu/libc.so.6(+0x8037a)[0x7f363aee737a]
            /lib/x86_64-linux-gnu/libc.so.6(cfree+0x4c)[0x7f363aeeb53c]
            ./detect_align_cnn(_Z10detectfacePhiiibPfPi+0xeb2)[0x443608]
            ./detect_align_cnn(main+0x35a)[0x439820]
            /lib/x86_64-linux-gnu/libc.so.6(__libc_start_main+0xf0)[0x7f363ae87830]
            ./detect_align_cnn(_start+0x29)[0x4393f9]
            */
            // detectface(src_data, width, height, MAXFACENUM, true, result, &face_num);
            long end_time_ = clock();
            printf("detect time:%ldms\n", (end_time_ - start_time_)/1000);
            
            face_num = boxes.size();
            if(face_num > 0)
            {
                // Occur when continuous high-resolution image input:
                /*
                terminate called after throwing an instance of 'std::bad_alloc'
                what():  std::bad_alloc
                */
                unsigned char *srcImg = new unsigned char[width*height];
                for (int r = 0; r < height; ++r)
                {
                    unsigned char *sptr = src_data + 4*r*width;
                    unsigned char *dptr = srcImg+r*width;
                    for (int c = 0; c < width; ++c)
                    {
                        dptr[0] = (307 * (int)sptr[0] + 604 * sptr[1] + 113 * sptr[2]) >> 10;
                        dptr++;
                        sptr += 4;
                    }
                }
                
                for (int i = 0; i < face_num; ++i)
                {
                    // 
                    result[15*i] = boxes[i].point[0]._x / scale;
                    result[15*i+2] = boxes[i].point[1]._x / scale;
                    result[15*i+6] = boxes[i].point[3]._x / scale;
                    result[15*i+8] = boxes[i].point[4]._x / scale;
                    result[15*i+4] = boxes[i].point[2]._x / scale;
                    result[15*i+1] = boxes[i].point[0]._y / scale;
                    result[15*i+3] = boxes[i].point[1]._y / scale;
                    result[15*i+7] = boxes[i].point[3]._y / scale;
                    result[15*i+9] = boxes[i].point[4]._y / scale;
                    result[15*i+5] = boxes[i].point[2]._y / scale;
                    result[15*i+10] = boxes[i].x1/scale;
                    result[15*i+11] = boxes[i].y1/scale;
                    result[15*i+12] = (boxes[i].x2-boxes[i].x1)/scale;
                    result[15*i+13] = (boxes[i].y2-boxes[i].y1)/scale;

                    // left x, top y, width, height
                    int true_face[4] = {(int)result[15*i+10], (int)result[15*i+11], (int)result[15*i+12], (int)result[15*i+13]};
                    float align_points[10];

                    if(LANDMARKS_NUM == 0)
                    {
                        return -4;
                    }
                    else
                    {
                        switch(mode_sel)
                        {
                            case P68_WITH_5_POINTS:
                                for(int p = 0; p < 5; ++p)
                                {
                                    align_points[p] = result[15*i+p*2];
                                    align_points[p+5] = result[15*i+p*2+1];
                                }
                                break;
                            case P106_WITH_5_POINTS:
                                align_points[0] = result[15*i];
                                align_points[1] = result[15*i+2];
                                align_points[2] = result[15*i+6];
                                align_points[3] = result[15*i+8];
                                align_points[4] = result[15*i+4];
                                align_points[5] = result[15*i+1];
                                align_points[6] = result[15*i+3];
                                align_points[7] = result[15*i+7];
                                align_points[8] = result[15*i+9];
                                align_points[9] = result[15*i+5];
                                break;
                            case P106_WITHOUT_5_POINTS:
                                align_points[0] = result[15*i];
                                align_points[1] = result[15*i+2];
                                align_points[2] = result[15*i+6];
                                align_points[3] = result[15*i+8];
                                align_points[4] = result[15*i+4];
                                align_points[5] = result[15*i+1];
                                align_points[6] = result[15*i+3];
                                align_points[7] = result[15*i+7];
                                align_points[8] = result[15*i+9];
                                align_points[9] = result[15*i+5];
                                break;
                            default:
                                return -5;
                        }
                    }

                    
                    if(model_flag == 0)
                    {
                        int error_flag = face_align_config(argv[2], mode_sel);
                        if(error_flag)
                        {
                            return error_flag;
                        }
                        
                        model_flag = 1;
                    }

                    long start_time = clock();
                    face_alignment(srcImg, true_face, points + 2*i*LANDMARKS_NUM, align_points, height, width, LANDMARKS_NUM, mode_sel);
                    long end_time = clock();

                    printf("one face align time:%ldms\n", (end_time - start_time)/1000);
                    
                    cv::rectangle(src, cv::Rect(result[i*15+10], result[i*15+11], result[i*15+12], result[i*15+13]), cv::Scalar(0, 0, 255), 2);
                    for(int pid = 0; pid < LANDMARKS_NUM; pid++)
                    {
                        cv::circle(src, cv::Point(points[2*LANDMARKS_NUM*i+pid], points[2*LANDMARKS_NUM*i+pid+LANDMARKS_NUM]), 2, cv::Scalar(0, 255, 0, 255), 2);
                    }
                    
                    float estimate_from[14];
                    int estimate_idx[] = {52, 55, 58, 61, 46, 84, 90}; // 4 eye contours, 1 nose, 2 mouth
                    for(int cnt = 0; cnt < 7; ++cnt)
                    {
                        estimate_from[cnt] = points[2*LANDMARKS_NUM*i + estimate_idx[cnt]];
                        estimate_from[cnt+7] = points[2*LANDMARKS_NUM*i + estimate_idx[cnt] + LANDMARKS_NUM];
                    }
                    cv::Mat head_pose = EstimateHeadPose(estimate_from);
                    std::cout << "Pitch: " << head_pose.at<float>(0) << std::endl;
                    std::cout << "Yaw: " << head_pose.at<float>(1) << std::endl;
                    std::cout << "Roll: " << head_pose.at<float>(2) << std::endl;
                }
                
                delete[] srcImg;
                memset(points, 0, 2*LANDMARKS_NUM*MAXFACENUM*sizeof(float));
                
            }
            
            cnt += 1;
            cv::imwrite("out.png", src);
            // cv::imshow("test", src);
            // cv::waitKey(0);
            
            delete[] src_data;
        }

        fin.close();
        
        
        return 0;
}


static float estimateHeadPoseMatrix[] = {
        0.139791,27.4028,7.02636,
        -2.48207,9.59384,6.03758,
        1.27402,10.4795,6.20801,
        1.17406,29.1886,1.67768,
        0.306761,-103.832,5.66238,
        4.78663,17.8726,-15.3623,
        -5.20016,9.29488,-11.2495,
        -25.1704,10.8649,-29.4877,
        -5.62572,9.0871,-12.0982,
        -5.19707,-8.25251,13.3965,
        -23.6643,-13.1348,29.4322,
        67.239,0.666896,1.84304,
        -2.83223,4.56333,-15.885,
        -4.74948,-3.79454,12.7986,
        -16.1,1.47175,4.03941 };


// For simple: 
// Pitch: [-up, +down]
// Yaw: [-left, +right]
// Roll: [-顺时针, +逆时针]
cv::Mat EstimateHeadPose(const float *curr_shape)
{
    int estimate_num = 7;
    float mean_x = 0;
    float mean_y = 0;
    float min_y = curr_shape[estimate_num];
    float max_y = curr_shape[estimate_num];
    for(int i = 0; i < estimate_num; ++i)
    {
        float x = curr_shape[i];
        float y = curr_shape[i+estimate_num];
        mean_x += x;
        mean_y += y;
        if(min_y > y)
        {
            min_y = y;
        }
        if(max_y < y)
        {
            max_y = y;
        }
    }
    mean_x /= estimate_num;
    mean_y /= estimate_num;
    float dist = max_y - min_y;

    cv::Mat tmp(1, 2*estimate_num+1, CV_32FC1);
    for(int i=0; i < estimate_num; i++)
    {
        float x = curr_shape[i];
        float y = curr_shape[i+estimate_num];
        tmp.at<float>(i) = (x - mean_x) / dist;
        tmp.at<float>(i+estimate_num) = (y - mean_y) / dist;
    }
    tmp.at<float>(2*estimate_num) = 1.0f;

    cv::Mat estimateHeadPoseMat(15, 3, CV_32FC1, estimateHeadPoseMatrix);
    cv::Mat predict = tmp * estimateHeadPoseMat;
    return predict;
}


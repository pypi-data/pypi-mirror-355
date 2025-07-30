//
// Created by admin on 2017/7/24.
//

#ifndef FACE_DETECT_CNN_SVDCMP_H
#define FACE_DETECT_CNN_SVDCMP_H

extern float **init_matrix(int rows, int cols);
extern void delete_matrix(float **m);
extern double **dmatrix(int nrl, int nrh, int ncl, int nch);
extern double *dvector(int nl, int nh);
extern void svdcmp(double **a, int m, int n, double *w, double **v);

#endif //FACE_DETECT_CNN_SVDCMP_H

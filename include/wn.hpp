#include <Eigen/Core>
#include <vector>
#include <cmath>
#include <omp.h>

void compute_face_winding_numbers(
    const Eigen::MatrixXd &V,
    const Eigen::MatrixXi &F,
    const Eigen::MatrixXd &poly_V,
    const Eigen::MatrixXi &poly_E,
    Eigen::VectorXd &wns_out)
{
    const int num_faces = F.rows();
    const int num_edges = poly_E.rows();
    wns_out.resize(num_faces);

// compute wns
#pragma omp parallel for schedule(static)
    for (int i = 0; i < num_faces; i++)
    {
        double qx = (V(F(i, 0), 0) + V(F(i, 1), 0) + V(F(i, 2), 0)) / 3.0;
        double qy = (V(F(i, 0), 1) + V(F(i, 1), 1) + V(F(i, 2), 1)) / 3.0;
        double total_angle = 0.0;

        for (int j = 0; j < num_edges; j++)
        {
            int v0 = poly_E(j, 0);
            int v1 = poly_E(j, 1);

            double Ax = poly_V(v0, 0);
            double Ay = poly_V(v0, 1);
            double Bx = poly_V(v1, 0);
            double By = poly_V(v1, 1);
            double vax = Ax - qx;
            double vay = Ay - qy;
            double vbx = Bx - qx;
            double vby = By - qy;

            double cross = (vax * vby) - (vay * vbx);
            double dot = (vax * vbx) + (vay * vby);
            total_angle += std::atan2(cross, dot);
        }
        wns_out(i) = (total_angle / (2.0 * M_PI));
    }
}
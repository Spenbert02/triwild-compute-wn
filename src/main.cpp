#include <iostream>
#include <string>
#include <vector>
#include <filesystem>
#include <set>
#include <mshio/mshio.h>
#include <Eigen/Core>
#include "mesh_help.hpp"
#include <omp.h>
#include "wn.hpp"
#include <chrono>

namespace fs = std::filesystem;

int main(int argc, char *argv[])
{
    // Basic argument check
    if (argc < 4)
    {
        std::cerr << "Usage: " << argv[0] << " <mesh_dir> <curve_dir> <output_dir>" << std::endl;
        return 1;
    }

    // Assign arguments to variables
    std::string mesh_dir = argv[1];
    fs::path mesh_dir_path(mesh_dir);
    std::string curve_dir = argv[2];
    fs::path curve_dir_path(curve_dir);
    std::string output_dir = argv[3];
    fs::path output_dir_path(output_dir);
    std::cout << "Processing meshes from: " << mesh_dir << std::endl;
    std::cout << "Using curves from: " << curve_dir << std::endl;
    std::cout << "Saving results to: " << output_dir << std::endl;

    // make sure directories exist
    if (!fs::is_directory(mesh_dir))
    {
        std::cerr << "Mesh directory [" << mesh_dir << "] does not exist." << std::endl;
    }
    if (!fs::is_directory(curve_dir))
    {
        std::cerr << "Curve directory [" << curve_dir << "] does not exist." << std::endl;
    }
    if (!fs::is_directory(output_dir))
    {
        std::cerr << "Output directory [" << output_dir << "] does not exist." << std::endl;
    }

    // kinda debugging
    std::cout << "Running with " << omp_get_max_threads() << " threads." << std::endl;

    // collect .msh file nums
    std::set<int> msh_nums;
    for (const auto &entry : fs::directory_iterator(mesh_dir))
    {
        if (entry.path().extension() == ".msh")
        {
            try
            {
                msh_nums.insert(std::stoi(entry.path().stem().string()));
            }
            catch (const std::invalid_argument &e)
            {
                // This catches things like .DS_Store or non-numeric folders
                // std::cerr << "Skipping non-numeric file: " << entry.path() << std::endl;
                continue;
            }
            catch (const std::out_of_range &e)
            {
                // std::cerr << "Filename number too large: " << entry.path() << std::endl;
                continue;
            }
        }
    }
    std::cout << "found " << msh_nums.size() << " valid .msh files" << std::endl;

    // collect .obj file nums
    std::set<int> obj_nums;
    for (const auto &entry : fs::directory_iterator(curve_dir))
    {
        if (entry.path().extension() == ".obj")
        {
            try
            {
                obj_nums.insert(std::stoi(entry.path().stem().string()));
            }
            catch (const std::invalid_argument &e)
            {
                // This catches things like .DS_Store or non-numeric folders
                // std::cerr << "Skipping non-numeric file: " << entry.path() << std::endl;
                continue;
            }
            catch (const std::out_of_range &e)
            {
                // std::cerr << "Filename number too large: " << entry.path() << std::endl;
                continue;
            }
        }
    }
    std::cout << "found " << obj_nums.size() << " valid .obj files" << std::endl;

    // intersect to get paired files
    std::set<int> paired_nums;
    std::set_intersection(msh_nums.begin(), msh_nums.end(),
                          obj_nums.begin(), obj_nums.end(),
                          std::inserter(paired_nums, paired_nums.begin()));

    // load .msh and .obj, compute wn, tag, write .msh
    int curr_data = 0;
    int total_data = paired_nums.size();
    auto overall_start = std::chrono::high_resolution_clock::now();
    for (const int &id : paired_nums)
    {
        // terminal comms
        std::cout << "processing model [" << id << "]... " << std::flush;
        auto start_time = std::chrono::high_resolution_clock::now();

        // load msh
        fs::path msh_path = mesh_dir_path / (std::to_string(id) + ".msh");
        std::string msh_path_str = msh_path.string();
        mshio::MshSpec spec = mshio::load_msh(msh_path_str);

        // extract verts/faces
        Eigen::MatrixXd V(get_num_face_vertices(spec), 2);
        extract_face_vertices(spec, V);
        Eigen::MatrixXi F(get_num_faces(spec), 3);
        extract_faces(spec, F);

        // load obj
        fs::path obj_path = curve_dir_path / (std::to_string(id) + ".obj");
        std::string obj_path_str = obj_path.string();
        Eigen::MatrixXd poly_V;
        Eigen::MatrixXi poly_E;
        read_obj_polyline(obj_path_str, poly_V, poly_E);

        // compute winding numbers
        Eigen::VectorXd wns;
        compute_face_winding_numbers(V, F, poly_V, poly_E, wns);
        Eigen::VectorXd tags;
        if (wns.maxCoeff() > -0.5)
        {
            tags = (wns.array() > 0.5).cast<double>();
        }
        else
        {
            tags = (wns.array() < -0.5).cast<double>();
        }

        // write output .msh file
        fs::path output_subdir_path = output_dir_path / ("data_" + std::to_string(id));
        fs::create_directories(output_subdir_path);
        fs::path output_msh_path = output_subdir_path / (std::to_string(id) + "_tagged.msh");
        mshio::MshSpec out_spec;
        add_face_vertices(out_spec, V.rows(), V);
        add_faces(out_spec, F.rows(), F);
        add_scalar_face_attribute(out_spec, "tag_0", tags);
        save_msh(out_spec, output_msh_path.string(), false);

        // terminal comms
        auto end_time = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::seconds>(end_time - start_time);
        auto overall_duration = std::chrono::duration_cast<std::chrono::minutes>(end_time - overall_start);
        std::cout << "finished (" << ++curr_data << "/" << total_data << ") in " << duration.count() << "s";
        std::cout << " (total elapsed: " << overall_duration.count() << "m)" << std::endl;
    }

    return 0;
}
#pragma once
#include <vector>
#include <mshio/mshio.h>
#include <Eigen/Core>
#include <fstream>
#include <sstream>
#include <string>

//// MSHIIO STUFF
const mshio::NodeBlock *get_face_vertex_block(const mshio::MshSpec &spec)
{
    for (const auto &block : spec.nodes.entity_blocks)
    {
        if (block.entity_dim == 2)
        {
            return &block;
        }
    }
    return nullptr;
}

void extract_face_vertices(const mshio::MshSpec &spec, Eigen::MatrixXd &V)
{
    const auto *block = get_face_vertex_block(spec);
    if (block == nullptr)
        return;

    const size_t num_vertices = block->num_nodes_in_block;
    if (num_vertices == 0)
        return;

    const size_t tag_offset = block->tags.front();
    for (size_t i = 0; i < num_vertices; i++)
    {
        size_t tag = block->tags[i] - tag_offset;
        V.row(tag) << block->data[i * 3], block->data[i * 3 + 1];
    }
}

size_t get_num_face_vertices(const mshio::MshSpec &spec)
{
    const auto *block = get_face_vertex_block(spec);
    if (block != nullptr)
    {
        return block->num_nodes_in_block;
    }
    else
    {
        return 0;
    }
}

const mshio::ElementBlock *get_face_block(const mshio::MshSpec &spec)
{
    for (const auto &block : spec.elements.entity_blocks)
    {
        if (block.entity_dim == 2)
        {
            return &block;
        }
    }
    return nullptr;
}

void extract_faces(const mshio::MshSpec &spec, Eigen::MatrixXi &F)
{
    const auto *vertex_block = get_face_vertex_block(spec);
    const auto *element_block = get_face_block(spec);
    if (element_block == nullptr)
        return;
    // assert(vertex_block != nullptr);

    const size_t num_elements = element_block->num_elements_in_block;
    if (num_elements == 0)
        return;
    // assert(vertex_block->num_nodes_in_block != 0);

    const size_t vert_tag_offset = vertex_block->tags.front();
    const size_t elem_tag_offset = element_block->data.front();
    for (size_t i = 0; i < num_elements; i++)
    {
        const size_t tag = element_block->data[i * (4)] - elem_tag_offset;
        // assert(tag < num_elements);
        const auto *element = element_block->data.data() + i * (4) + 1;
        F.row(tag) << element[0] - vert_tag_offset, element[1] - vert_tag_offset, element[2] - vert_tag_offset;
    }
}

size_t get_num_faces(const mshio::MshSpec &spec)
{
    const auto *block = get_face_block(spec);
    if (block != nullptr)
    {
        return block->num_elements_in_block;
    }
    else
    {
        return 0;
    }
}

void add_face_vertices(mshio::MshSpec &spec, size_t num_vertices, const Eigen::MatrixXd &V)
{
    if (num_vertices == 0)
    {
        int dummy = 0; // TODO: throw warning here, ie "adding empty vertex block"
    }
    mshio::NodeBlock block;
    block.num_nodes_in_block = num_vertices;
    block.tags.reserve(num_vertices);
    block.data.reserve(num_vertices * 3);
    block.entity_dim = 2;
    block.entity_tag = (int)spec.nodes.num_entity_blocks + 1;

    const size_t tag_offset = spec.nodes.max_node_tag;
    for (size_t i = 0; i < num_vertices; i++)
    {
        block.tags.push_back(tag_offset + i + 1);
        block.data.push_back(V(i, 0));
        block.data.push_back(V(i, 1));
        block.data.push_back(0.0);
    }

    spec.nodes.num_entity_blocks += 1;
    spec.nodes.num_nodes += num_vertices;
    spec.nodes.min_node_tag = 1;
    spec.nodes.max_node_tag += num_vertices;
    spec.nodes.entity_blocks.push_back(std::move(block));
}

void add_faces(mshio::MshSpec &spec, size_t num_elements, const Eigen::MatrixXi &F)
{
    if (num_elements == 0)
    {
        return; // TODO: throw warning here, ie "faces not added"
    }

    if (spec.nodes.num_nodes == 0)
    {
        return; // TODO: thow error like below
        // log_and_throw_error("Please add a vertex block before adding elements.");
    }
    const auto &vertex_block = spec.nodes.entity_blocks.back();
    // assert(!vertex_block.tags.empty());
    if (vertex_block.entity_dim != 2)
    {
        return; // TODO: throw error like below
        // log_and_throw_error("It seems the last added vertex block has different dimension "
        //                     "than the elements you want to add.");
    }

    mshio::ElementBlock block;
    block.entity_dim = 2;
    block.entity_tag = vertex_block.entity_tag;
    block.element_type = 2; // 3-node triangle.
    block.num_elements_in_block = num_elements;

    const size_t vertex_offset =
        vertex_block.num_nodes_in_block == 0 ? 0 : vertex_block.tags.front() - 1;
    if (vertex_offset == 0)
    {
        int dummy = 0; // TODO: throw warning like below
        // logger().trace(
        //     "Do not offset vertex IDs for this element block as vertex block was empty");
    }

    const size_t tag_offset = spec.elements.max_element_tag;
    block.data.reserve(num_elements * (4));
    for (size_t i = 0; i < num_elements; i++)
    {
        block.data.push_back(tag_offset + i + 1); // element tag.
        for (size_t j = 0; j <= 2; j++)
        {
            block.data.push_back(vertex_offset + F(i, j) + 1);
        }
    }

    spec.elements.num_entity_blocks++;
    spec.elements.num_elements += num_elements;
    spec.elements.min_element_tag = 1;
    spec.elements.max_element_tag += num_elements;
    spec.elements.entity_blocks.push_back(std::move(block));
}

void add_scalar_face_attribute(mshio::MshSpec &spec, const std::string &name, const Eigen::VectorXd &attrs)
{
    if (spec.elements.entity_blocks.empty())
    {
        return; // TODO: throw error here like below
        // throw std::runtime_error("Please add elements before adding element attributes!");
    }
    const auto &elem_block = spec.elements.entity_blocks.back();
    if (elem_block.entity_dim != 2)
    {
        return; // TODO: throw error here like below
        // throw std::runtime_error(
        //     "It seems the last added element block has different dimension "
        //     "than the element attribute you want to add.");
    }
    const size_t num_elements = elem_block.num_elements_in_block;

    mshio::Data data;
    data.header.string_tags = {name};
    data.header.real_tags = {0.0};
    data.header.int_tags = {0, 1, int(num_elements), 0, 2};

    data.entries.resize(num_elements);
    for (size_t i = 0; i < num_elements; i++)
    {
        auto &entry = data.entries[i];
        entry.tag = elem_block.data[i * (4)];
        entry.data.reserve(1);
        entry.data.push_back(attrs(i));
    }

    spec.element_data.push_back(std::move(data));
}

void save_msh(mshio::MshSpec &spec, const std::string &filename, bool binary = true)
{
    spec.mesh_format.file_type = binary;
    mshio::validate_spec(spec);
    mshio::save_msh(filename, spec);
}

//// OBJ STUFF
void read_obj_polyline(const std::string &filename, Eigen::MatrixXd &V, Eigen::MatrixXi &E)
{
    std::vector<Eigen::Vector2d> verts;
    std::vector<Eigen::Vector2i> edges;

    std::ifstream infile(filename);
    std::string line;
    while (std::getline(infile, line))
    {
        std::stringstream ss(line);
        std::string type;
        ss >> type;

        if (type == "v")
        {
            double x, y, z;
            ss >> x >> y >> z;
            verts.emplace_back(x, y); // Store only x, y for 2D winding
        }
        else if (type == "l")
        {
            int v1, v2;
            ss >> v1 >> v2;
            // OBJ is 1-indexed, convert to 0-indexed
            edges.emplace_back(v1 - 1, v2 - 1);
        }
    }

    V.resize(verts.size(), 2);
    E.resize(edges.size(), 2);
    for (int i = 0; i < verts.size(); i++)
    {
        V.row(i) = verts[i];
    }
    for (int i = 0; i < edges.size(); i++)
    {
        E.row(i) = edges[i];
    }
}
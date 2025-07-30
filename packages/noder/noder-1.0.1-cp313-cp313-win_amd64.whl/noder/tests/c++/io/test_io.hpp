#ifdef ENABLE_HDF5_IO
#ifndef TEST_IO_H
#define TEST_IO_H

#include <io/io.hpp>
#include <array/factory/vectors.hpp>

using namespace std::string_literals;
using namespace io;
using namespace arrayfactory;

namespace test_io {

void test_write_nodes( std::string filename = "test.cgns") {
     auto a = std::make_shared<Node>("a");
     Array arrA = uniformFromStep<int32_t>(0, 10);
     a->setData(arrA);

     auto b = std::make_shared<Node>("b");
     Array arrB = uniformFromCount<float>(-1, 1, 5);
     b->setData(arrB);
     b->attachTo(a);

     auto c = std::make_shared<Node>("c");
     Array arrC = "toto"s;
     c->setData(arrC);
     c->attachTo(a);

     auto d = std::make_shared<Node>("d");
     d->attachTo(b);

     write_node(filename, a);
}

std::shared_ptr<Node> test_read( std::string tmp_filename = "test_read.cgns") {
     test_write_nodes(tmp_filename);
     auto node = read(tmp_filename);
     return node;
}

}

#endif // TEST_IO_H
#endif // ENABLE_HDF5_IO

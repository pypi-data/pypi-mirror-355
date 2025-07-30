#ifndef TEST_NODE_CLASS_H
#define TEST_NODE_CLASS_H

# include <node/node.hpp>

# include <pybind11/numpy.h>
# include <pybind11/pybind11.h>

namespace py = pybind11;

void test_init();

Node test_init_cpp2py_by_copy();

std::shared_ptr<Node> test_init_cpp2py_by_ptr();

void test_name();

void test_setName();

void test_type();

void test_setType();

void test_binding_setNameAndTypeFromPython(Node& node);

void test_noData();

void test_children_empty();

void test_parent_empty();

void test_root_itself();

void test_level_0();

void test_positionAmongSiblings_null();

void test_getPath_itself();

void test_attachTo();

void test_attachTo_multiple_levels();

void test_addChild();

void test_addChildAsPointer();

void test_detach_0();

void test_detach_1();

void test_detach_2();

void test_detach_3();

void test_delete_multiple_descendants();

void test_getPath();

void test_root();

void test_level();

void test_printTree();

void test_children();

void test_children_checkPaths();    

void test_binding_addChildrenFromPython(std::shared_ptr<Node> node);

void test_positionAmongSiblings();

void test_getAllDescendants();

#endif // TEST_NODE_CLASS_H
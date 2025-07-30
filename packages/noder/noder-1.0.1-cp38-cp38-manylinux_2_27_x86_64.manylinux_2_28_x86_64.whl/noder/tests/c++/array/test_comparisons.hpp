# ifndef TEST_ARRAY_COMPARISONS_HPP
# define TEST_ARRAY_COMPARISONS_HPP

# include <array/array.hpp>
# include <array/factory/vectors.hpp>
# include <array/factory/matrices.hpp>

template <typename T> [[gnu::used]]
void test_twoIdenticalArraysAreEqual();

template <typename T> [[gnu::used]]
void test_twoIdenticalArraysButWithDifferentMemoryLayoutAreEqual();

void test_twoIdenticalArraysButWithDifferentDataTypesAreEqual();

template <typename T> [[gnu::used]]
void test_twoArraysWithDifferentItemsAreNotEqual();

template <typename T> [[gnu::used]]
void test_twoArraysWithDifferentSizesAreNotEqual();

template <typename T> [[gnu::used]]
void test_twoArraysWithDifferentShapesButSameSizeAreEqual();

template <typename T> [[gnu::used]]
void test_arrayOfZerosIsEqualToScalarZero();

template <typename T> [[gnu::used]]
void test_arrayOfZerosIsDifferentToScalarOne();

void assertEqualArraysAndNotDifferent(const Array& array1, const Array& array2);
void assertDifferentArraysAndNotEqual(const Array& array1, const Array& array2);

template <typename T> [[gnu::used]]
void assertArrayEqualAndNotDifferentToScalar(const Array& array1, const T& scalar);

template <typename T> [[gnu::used]]
void assertArrayDifferentAndNotEqualToScalar(const Array& array1, const T& scalar);

void test_rangeIsNeverEqualToScalar();

void test_twoIdenticalArraysContainingStringsAreEqual();
void test_twoIdenticalArraysContainingUnicodeStringsAreEqual();
void test_arrayEqualToString();
void test_arrayEqualToUnicodeString();
void test_arrayDifferentToString();
void test_numericalArrayDifferentToString();




# endif
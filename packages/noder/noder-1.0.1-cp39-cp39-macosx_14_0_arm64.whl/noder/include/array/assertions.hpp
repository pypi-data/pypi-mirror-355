#ifndef ARRAY_ASSERTIONS_HPP
#define ARRAY_ASSERTIONS_HPP

#include "array/array.hpp"


class Array::Assertions {

private:
    const Array& array;

public:
    explicit Assertions(const Array& array);

    template <typename T> [[gnu::used]]
    void haveSameSizeAs(const T& other) const {
        size_t arraySize = array.size();
        size_t otherSize = static_cast<size_t>(other.size());
        if (arraySize != otherSize) {
            throw py::value_error(
                "Array size ("+std::to_string(arraySize)+
                ") was not equal to "+std::to_string(otherSize));
        }
    }

    template <typename T, ssize_t N>
    void haveDataOfTypeAndDimensions() const {
        this->haveDataOfType<T>();
        this->haveDataOfDimensions<N>();
    }

    template <typename T> [[gnu::used]]
    void haveDataOfType() const {
        if (!array.hasDataOfType<T>()) {
            throw py::type_error(
                "Wrong requested type " + utils::getTypeName<T>());
        }
    }

    template <size_t N>
    void haveDataOfDimensions() const {
        if (N != array.dimensions()) {
            throw py::type_error(
                "Expected dimensions: " + std::to_string(N) +
                ", but got: " + std::to_string(array.dimensions())
            );
        }
    }

    template <typename T> [[gnu::used]]
    void haveValidDataTypeForSettingScalar() const;
    
};

#endif 
